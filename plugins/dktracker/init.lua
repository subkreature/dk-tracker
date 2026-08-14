local exports = {
    name = "dktracker",
    version = "0.1.12",
    description = "Donkey Kong Tracker",
    license = "MIT",
    author = { name = "Nick" }
}

local dktracker = exports

----------------------------------------------------------
-- Configuration
----------------------------------------------------------

local DEBUG_GAME_STATE = false
local DEBUG_LIVES = true

----------------------------------------------------------
-- Memory addresses
----------------------------------------------------------

local ADDRESS_SCORE_LOW = 0x60B3
local ADDRESS_SCORE_HIGH = 0x60B4

local ADDRESS_BOARD_STATE = 0x608A
local ADDRESS_BOARD_ACTIVE = 0x6208
local ADDRESS_AUX_STATE = 0x694E

local ADDRESS_SCREEN_TYPE = 0x6227
local ADDRESS_LIVES_REMAINING = 0x6228
local ADDRESS_LEVEL_NUMBER = 0x6229

----------------------------------------------------------
-- Helpers
----------------------------------------------------------

local function bcd_to_decimal(value)
    local high = (value >> 4) & 0x0F
    local low = value & 0x0F

    return high * 10 + low
end

local function read_score(space)
    local low_byte =
        space:read_u8(ADDRESS_SCORE_LOW)

    local high_byte =
        space:read_u8(ADDRESS_SCORE_HIGH)

    return
        bcd_to_decimal(high_byte) * 10000
        + bcd_to_decimal(low_byte) * 100
end

local function read_path_file(filename)
    local pathfile = io.open(filename, "r")

    if not pathfile then
        print("ERROR: Could not open " .. filename)
        return nil
    end

    local path = pathfile:read("*line")
    pathfile:close()

    if not path or path == "" then
        print("ERROR: " .. filename .. " was empty")
        return nil
    end

    return path
end

local function resolve_output_path(
    environment_name,
    fallback_filename
)
    local environment_path =
        os.getenv(environment_name)

    if
        environment_path
        and environment_path ~= ""
    then
        return environment_path
    end

    return read_path_file(
        fallback_filename
    )
end

local function screen_name(screen_type)
    local names = {
        [1] = "barrels",
        [2] = "pie_factory",
        [3] = "elevators",
        [4] = "rivets"
    }

    return names[screen_type] or "unknown"
end

local function is_valid_screen(screen_type)
    return screen_type >= 1 and screen_type <= 4
end

----------------------------------------------------------
-- Plugin
----------------------------------------------------------

function dktracker.startplugin()

    print("=================================")
    print("Jungle Gym plugin loaded!")
    print("Version: " .. exports.version)
    print("Telemetry sampling: every emulated frame")
    print("=================================")

    ------------------------------------------------------
    -- Resolve output paths
    ------------------------------------------------------

    local score_path =
        resolve_output_path(
            "JUNGLE_GYM_SCORE_PATH",
            "score_path.txt"
        )

    if not score_path then
        return
    end

    local events_path =
        resolve_output_path(
            "JUNGLE_GYM_EVENTS_PATH",
            "events_path.txt"
        )

    if not events_path then
        return
    end

    ------------------------------------------------------
    -- Open telemetry files
    ------------------------------------------------------

    local score_log = io.open(score_path, "w")

    if not score_log then
        print("ERROR: Could not create score log")
        return
    end

    local events_log = io.open(events_path, "w")

    if not events_log then
        print("ERROR: Could not create events log")
        score_log:close()
        return
    end

    score_log:write(
        "elapsed_seconds,score\n"
    )
    score_log:flush()

    events_log:write(
        "elapsed_seconds,event,score,level,"
        .. "board_position,screen_type,screen_name,"
        .. "lives,details\n"
    )
    events_log:flush()

    ------------------------------------------------------
    -- Runtime state
    ------------------------------------------------------

    local game_start_time = nil

    local last_score = -1
    local last_valid_score = 0

    local game_started = false

    -- After Game Over, require the old board to go fully
    -- inactive before accepting another board activation as
    -- a new game. This prevents attract/Game Over state changes
    -- from being mistaken for continued play.
    local waiting_for_new_game = false
    local new_game_board_went_inactive = false

    local last_board_state = nil
    local last_board_active = nil
    local last_aux_state = nil
    local last_lives_byte = nil

    local active_level = 0
    local active_board_position = 0
    local active_screen_type = 0

    -- Prevents startup animation/state changes from being
    -- interpreted as a real board clear.
    local first_board_activated = false

    -- Set only after a successful board clear.
    local board_advance_pending = false

    local current_lives = 0
    local lives_monitor_initialized = false

    local life_loss_pending = false
    local life_loss_previous_lives = nil
    local life_loss_new_lives = nil

    local bonus_life_pending = false
    local bonus_previous_lives = nil
    local bonus_new_lives = nil
    local bonus_detected_elapsed = nil

    local event_detection_armed = false

    local final_death_recorded = false
    local game_over_recorded = false

    local life_lost_count = 0
    local board_clear_count = 0
    local bonus_life_count = 0

    local frame_subscription = nil
    local stop_subscription = nil

    ------------------------------------------------------
    -- MAME API compatibility
    ------------------------------------------------------

    local function current_machine()
        if type(manager.machine) == "function" then
            return manager:machine()
        end

        return manager.machine
    end

    ------------------------------------------------------
    -- Timing
    ------------------------------------------------------

    local function current_emulated_time()
        if type(emu.time) == "function" then
            return emu.time()
        end

        return current_machine().time:as_double()
    end

    local function elapsed_seconds()
        if not game_start_time then
            return 0
        end

        return
            current_emulated_time()
            - game_start_time
    end

    ------------------------------------------------------
    -- CSV output
    ------------------------------------------------------

    local function write_score(score)
        score_log:write(
            string.format(
                "%.3f,%d\n",
                elapsed_seconds(),
                score
            )
        )

        score_log:flush()
    end

    local function write_event(
        event_name,
        score,
        level,
        board_position,
        screen_type,
        details
    )
        events_log:write(
            string.format(
                "%.3f,%s,%d,%d,%d,%d,%s,%d,%s\n",
                elapsed_seconds(),
                event_name,
                score,
                level,
                board_position,
                screen_type,
                screen_name(screen_type),
                current_lives,
                details or ""
            )
        )

        events_log:flush()
    end

    ------------------------------------------------------
    -- Semantic events
    ------------------------------------------------------

    local function record_board_start()
        print("---------------------------------")
        print(
            string.format(
                "BOARD ACTIVE: %d-%d (%s)",
                active_level,
                active_board_position,
                screen_name(active_screen_type)
            )
        )
        print(
            string.format(
                "Screen type: %d",
                active_screen_type
            )
        )
        print(
            string.format(
                "Lives remaining: %d",
                current_lives
            )
        )
        print("---------------------------------")

        write_event(
            "board_start",
            last_valid_score,
            active_level,
            active_board_position,
            active_screen_type,
            ""
        )
    end

    local function record_life_lost()
        life_lost_count =
            life_lost_count + 1

        print("=================================")
        print(
            string.format(
                "LIFE LOST #%d",
                life_lost_count
            )
        )
        print(
            string.format(
                "Board: %d-%d (%s)",
                active_level,
                active_board_position,
                screen_name(active_screen_type)
            )
        )
        print(
            string.format(
                "Score at death: %d",
                last_valid_score
            )
        )
        print(
            string.format(
                "Lives remaining: %d",
                current_lives
            )
        )
        print("=================================")

        write_event(
            "life_lost",
            last_valid_score,
            active_level,
            active_board_position,
            active_screen_type,
            string.format(
                "life_lost_number=%d;"
                .. "previous_lives=%d;"
                .. "current_lives=%d",
                life_lost_count,
                life_loss_previous_lives
                    or current_lives + 1,
                life_loss_new_lives
                    or current_lives
            )
        )
    end

    local function record_game_over()
        if game_over_recorded then
            return
        end

        game_over_recorded = true

        print("=================================")
        print("GAME OVER")
        print(
            string.format(
                "Final board: %d-%d (%s)",
                active_level,
                active_board_position,
                screen_name(active_screen_type)
            )
        )
        print(
            string.format(
                "Final score: %d",
                last_valid_score
            )
        )
        print("=================================")

        write_event(
            "game_over",
            last_valid_score,
            active_level,
            active_board_position,
            active_screen_type,
            string.format(
                "lives_lost=%d;"
                .. "boards_cleared=%d;"
                .. "bonus_lives=%d",
                life_lost_count,
                board_clear_count,
                bonus_life_count
            )
        )
    end

    local function record_board_clear()
        board_clear_count =
            board_clear_count + 1

        print("=================================")
        print(
            string.format(
                "BOARD CLEARED #%d",
                board_clear_count
            )
        )
        print(
            string.format(
                "Completed: %d-%d (%s)",
                active_level,
                active_board_position,
                screen_name(active_screen_type)
            )
        )
        print(
            string.format(
                "Score after board clear: %d",
                last_valid_score
            )
        )
        print("=================================")

        write_event(
            "level_transition",
            last_valid_score,
            active_level,
            active_board_position,
            active_screen_type,
            string.format(
                "board_clear_number=%d",
                board_clear_count
            )
        )
    end

    local function finalize_bonus_life(score)
        if not bonus_life_pending then
            return
        end

        bonus_life_count =
            bonus_life_count + 1

        print("=================================")
        print(
            string.format(
                "BONUS LIFE EARNED #%d",
                bonus_life_count
            )
        )
        print(
            string.format(
                "Board: %d-%d (%s)",
                active_level,
                active_board_position,
                screen_name(active_screen_type)
            )
        )
        print(
            string.format(
                "Lives remaining: %d -> %d",
                bonus_previous_lives,
                bonus_new_lives
            )
        )
        print(
            string.format(
                "Score: %d",
                score
            )
        )
        print("=================================")

        write_event(
            "bonus_life",
            score,
            active_level,
            active_board_position,
            active_screen_type,
            string.format(
                "bonus_life_number=%d;"
                .. "previous_lives=%d;"
                .. "current_lives=%d;"
                .. "detected_elapsed=%.3f",
                bonus_life_count,
                bonus_previous_lives,
                bonus_new_lives,
                bonus_detected_elapsed
                    or elapsed_seconds()
            )
        )

        bonus_life_pending = false
        bonus_previous_lives = nil
        bonus_new_lives = nil
        bonus_detected_elapsed = nil
    end

    local function record_lives_change(
        previous_lives,
        new_lives
    )
        if DEBUG_LIVES then
            print(
                string.format(
                    "LIVES REMAINING: %d -> %d",
                    previous_lives,
                    new_lives
                )
            )
        end

        write_event(
            "lives_changed",
            last_valid_score,
            active_level,
            active_board_position,
            active_screen_type,
            string.format(
                "previous=%d;current=%d",
                previous_lives,
                new_lives
            )
        )
    end

    ------------------------------------------------------
    -- Board-position handling
    ------------------------------------------------------

    local function activate_board(
        raw_level,
        raw_screen_type
    )
        if not first_board_activated then
            -- First legitimate board activation.
            active_level = raw_level
            active_board_position = 1
            first_board_activated = true

        elseif board_advance_pending then
            -- A successful clear preceded this activation.
            if raw_level ~= active_level then
                active_level = raw_level
                active_board_position = 1
            else
                active_board_position =
                    active_board_position + 1
            end

            board_advance_pending = false

        else
            -- Death respawn. Keep the existing position.
            active_level = raw_level
        end

        active_screen_type = raw_screen_type

        record_board_start()
    end

    ------------------------------------------------------
    -- Per-frame game-state reader
    ------------------------------------------------------

    local function read_game_state()

        local machine = current_machine()
        local cpu =
            machine.devices[":maincpu"]

        if not cpu then
            return
        end

        local space =
            cpu.spaces["program"]

        if not space then
            return
        end

        local score =
            read_score(space)

        local board_state =
            space:read_u8(
                ADDRESS_BOARD_STATE
            )

        local board_active =
            space:read_u8(
                ADDRESS_BOARD_ACTIVE
            )

        local aux_state =
            space:read_u8(
                ADDRESS_AUX_STATE
            )

        local raw_screen_type =
            space:read_u8(
                ADDRESS_SCREEN_TYPE
            )

        local raw_level =
            space:read_u8(
                ADDRESS_LEVEL_NUMBER
            )

        local lives_remaining =
            space:read_u8(
                ADDRESS_LIVES_REMAINING
            )

        --------------------------------------------------
        -- Detect real game start
        --------------------------------------------------

        if not game_started then

            if
                waiting_for_new_game
                and board_active == 0x00
            then
                new_game_board_went_inactive = true
            end

            local first_board_is_active =
                last_board_active ~= 0x02
                and board_active == 0x02
                and raw_level > 0
                and is_valid_screen(raw_screen_type)
                and lives_remaining >= 2

            if waiting_for_new_game then
                first_board_is_active =
                    new_game_board_went_inactive
                    and first_board_is_active
            end

            if not first_board_is_active then
                last_board_state = board_state
                last_board_active = board_active
                last_aux_state = aux_state

                if lives_monitor_initialized then
                    last_lives_byte = lives_remaining
                end

                return
            end

            game_started = true
            waiting_for_new_game = false
            new_game_board_went_inactive = false

            -- Keep one continuous session clock across every
            -- game played during this MAME launch.
            if not game_start_time then
                game_start_time =
                    current_emulated_time()
            end

            last_score = 0
            last_valid_score = 0

            active_level = raw_level
            active_board_position = 1
            active_screen_type = raw_screen_type

            first_board_activated = true
            board_advance_pending = false

            current_lives = lives_remaining
            lives_monitor_initialized = true
            last_lives_byte = lives_remaining

            life_loss_pending = false
            life_loss_previous_lives = nil
            life_loss_new_lives = nil

            bonus_life_pending = false
            bonus_previous_lives = nil
            bonus_new_lives = nil
            bonus_detected_elapsed = nil

            event_detection_armed = true

            final_death_recorded = false
            game_over_recorded = false

            life_lost_count = 0
            board_clear_count = 0
            bonus_life_count = 0

            print("Game started!")
            print(
                string.format(
                    "Initial level byte: %d",
                    raw_level
                )
            )
            print(
                string.format(
                    "Initial screen type: %d (%s)",
                    raw_screen_type,
                    screen_name(raw_screen_type)
                )
            )
            print(
                string.format(
                    "Initial lives byte: %d",
                    lives_remaining
                )
            )

            write_score(0)

            write_event(
                "game_start",
                0,
                raw_level,
                1,
                raw_screen_type,
                ""
            )

            record_board_start()

            last_board_state = board_state
            last_board_active = board_active
            last_aux_state = aux_state
            return
        end

        current_lives = lives_remaining

        --------------------------------------------------
        -- Preserve newest meaningful score
        --------------------------------------------------

        if score > 0 then
            last_valid_score = score
        end

        --------------------------------------------------
        -- Detect a board becoming active
        --------------------------------------------------

        if
            last_board_active ~= 0x02
            and board_active == 0x02
            and raw_level > 0
            and is_valid_screen(raw_screen_type)
        then
            if not lives_monitor_initialized then
                last_lives_byte =
                    lives_remaining

                lives_monitor_initialized =
                    true
            end

            activate_board(
                raw_level,
                raw_screen_type
            )
        end

        --------------------------------------------------
        -- Track lives changes
        --------------------------------------------------

        if
            lives_monitor_initialized
            and last_lives_byte ~= nil
            and lives_remaining ~= last_lives_byte
        then
            record_lives_change(
                last_lives_byte,
                lives_remaining
            )

            if lives_remaining < last_lives_byte then
                life_loss_previous_lives =
                    last_lives_byte

                life_loss_new_lives =
                    lives_remaining

                if lives_remaining == 0 then
                    record_life_lost()
                    record_game_over()

                    -- Enter an explicit post-Game-Over waiting
                    -- state. The old board must first become fully
                    -- inactive before a later activation can start
                    -- the next game.
                    game_started = false
                    waiting_for_new_game = true
                    new_game_board_went_inactive =
                        board_active == 0x00

                    final_death_recorded = true
                    life_loss_pending = false

                    life_loss_previous_lives = nil
                    life_loss_new_lives = nil

                    -- Do not let the remainder of this frame process
                    -- the lives reset or board teardown as part of
                    -- the finished game.
                    last_board_state = board_state
                    last_board_active = board_active
                    last_aux_state = aux_state
                    last_lives_byte = lives_remaining
                    return
                else
                    life_loss_pending = true
                end

            elseif lives_remaining > last_lives_byte then
                bonus_life_pending = true

                bonus_previous_lives =
                    last_lives_byte

                bonus_new_lives =
                    lives_remaining

                bonus_detected_elapsed =
                    elapsed_seconds()
            end
        end

        --------------------------------------------------
        -- Record score changes
        --------------------------------------------------

        if score > 0 and score ~= last_score then

            print(
                string.format(
                    "Score: %d",
                    score
                )
            )

            write_score(score)

            last_score = score

            finalize_bonus_life(score)
        end

        --------------------------------------------------
        -- Arm teardown detection only after the first
        -- legitimate board activation.
        --------------------------------------------------

        if
            first_board_activated
            and board_active == 0x02
        then
            event_detection_armed = true
        end

        --------------------------------------------------
        -- Classify board teardown
        --------------------------------------------------

        if
            first_board_activated
            and event_detection_armed
            and last_board_active == 0x02
            and board_active == 0x00
        then
            event_detection_armed = false

            if final_death_recorded then
                -- Already recorded on lives reaching zero.
                final_death_recorded = false

            elseif life_loss_pending then
                record_life_lost()

            else
                record_board_clear()
                board_advance_pending = true
            end

            life_loss_pending = false
            life_loss_previous_lives = nil
            life_loss_new_lives = nil
        end

        --------------------------------------------------
        -- Focused debug output
        --------------------------------------------------

        if DEBUG_GAME_STATE then

            if board_state ~= last_board_state then
                print(
                    string.format(
                        "608A: %02X -> %02X",
                        last_board_state,
                        board_state
                    )
                )
            end

            if aux_state ~= last_aux_state then
                print(
                    string.format(
                        "694E: %02X -> %02X",
                        last_aux_state,
                        aux_state
                    )
                )
            end

            if board_active ~= last_board_active then
                print(
                    string.format(
                        "6208: %02X -> %02X",
                        last_board_active,
                        board_active
                    )
                )
            end
        end

        --------------------------------------------------
        -- Save state for the next frame
        --------------------------------------------------

        last_board_state = board_state
        last_board_active = board_active
        last_aux_state = aux_state

        if lives_monitor_initialized then
            last_lives_byte = lives_remaining
        end
    end

    ------------------------------------------------------
    -- Register callbacks
    ------------------------------------------------------

    if type(emu.add_machine_frame_notifier) == "function" then
        frame_subscription =
            emu.add_machine_frame_notifier(
                read_game_state
            )
    else
        emu.register_frame(
            read_game_state
        )
    end

    local stop_notifier =
        emu.add_machine_stop_notifier
        or emu.register_stop

    stop_subscription =
        stop_notifier(
            function()

                if bonus_life_pending then
                    finalize_bonus_life(
                        last_valid_score
                    )
                end

                if frame_subscription then
                    frame_subscription:unsubscribe()
                    frame_subscription = nil
                end

                if score_log then
                    score_log:close()
                    score_log = nil
                end

                if events_log then
                    events_log:close()
                    events_log = nil
                end

                print("Telemetry logs saved.")
                print(
                    string.format(
                        "Lives lost detected: %d",
                        life_lost_count
                    )
                )
                print(
                    string.format(
                        "Boards cleared detected: %d",
                        board_clear_count
                    )
                )
                print(
                    string.format(
                        "Bonus lives detected: %d",
                        bonus_life_count
                    )
                )
                print(
                    string.format(
                        "Game over detected: %s",
                        game_over_recorded
                            and "yes"
                            or "no"
                    )
                )

                stop_subscription = nil
            end
        )

end

return exports