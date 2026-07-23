local exports = {
    name = "dktracker",
    version = "0.1.4",
    description = "Donkey Kong Tracker",
    license = "MIT",
    author = { name = "Nick" }
}

local dktracker = exports

----------------------------------------------------------
-- Configuration
----------------------------------------------------------

local DEBUG_GAME_STATE = true
local DEBUG_LIVES = true

----------------------------------------------------------
-- Memory addresses
----------------------------------------------------------

local ADDRESS_SCORE_LOW = 0x60B3
local ADDRESS_SCORE_HIGH = 0x60B4

local ADDRESS_BOARD_STATE = 0x608A
local ADDRESS_BOARD_ACTIVE = 0x6208
local ADDRESS_AUX_STATE = 0x694E

local ADDRESS_SCREEN_NUMBER = 0x6227
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
    local low_byte = space:read_u8(ADDRESS_SCORE_LOW)
    local high_byte = space:read_u8(ADDRESS_SCORE_HIGH)

    return
        bcd_to_decimal(high_byte) * 10000 +
        bcd_to_decimal(low_byte) * 100
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

local function screen_name(screen_number)
    local names = {
        [1] = "barrels",
        [2] = "pie_factory",
        [3] = "elevators",
        [4] = "rivets"
    }

    return names[screen_number] or "unknown"
end

local function is_valid_screen(screen_number)
    return screen_number >= 1 and screen_number <= 4
end

----------------------------------------------------------
-- Plugin
----------------------------------------------------------

function dktracker.startplugin()

    print("=================================")
    print("DK Tracker loaded from DK-Tracker project!")
    print("Version: " .. exports.version)
    print("Telemetry sampling: every emulated frame")
    print("=================================")

    ------------------------------------------------------
    -- Resolve output paths
    ------------------------------------------------------

    local score_path = read_path_file("score_path.txt")

    if not score_path then
        return
    end

    local events_path = read_path_file("events_path.txt")

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

    score_log:write("elapsed_seconds,score\n")
    score_log:flush()

    events_log:write(
        "elapsed_seconds,event,score,level,screen,"
        .. "screen_name,lives,details\n"
    )
    events_log:flush()

    ------------------------------------------------------
    -- Runtime state
    ------------------------------------------------------

    local game_start_time = nil

    local last_score = -1
    local last_valid_score = 0

    local saw_nonzero_score = false
    local game_started = false

    local last_board_state = nil
    local last_board_active = nil
    local last_aux_state = nil
    local last_lives_byte = nil

    -- Identity of the board currently being played.
    local active_level = 0
    local active_screen = 0

    local last_reported_level = nil
    local last_reported_screen = nil

    local current_lives = 0
    local lives_monitor_initialized = false

    -- A lives decrease occurs before the board teardown
    -- associated with a death.
    local life_loss_pending = false
    local life_loss_previous_lives = nil
    local life_loss_new_lives = nil

    local event_detection_armed = false

    local life_lost_count = 0
    local level_transition_count = 0
    local bonus_life_count = 0

    local frame_subscription = nil
    local stop_subscription = nil

    ------------------------------------------------------
    -- Timing
    ------------------------------------------------------

    local function current_emulated_time()
        return manager.machine.time:as_double()
    end

    local function elapsed_seconds()
        if not game_start_time then
            return 0
        end

        return current_emulated_time() - game_start_time
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
        screen,
        details
    )
        events_log:write(
            string.format(
                "%.3f,%s,%d,%d,%d,%s,%d,%s\n",
                elapsed_seconds(),
                event_name,
                score,
                level,
                screen,
                screen_name(screen),
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
                "BOARD ACTIVE: Level %d, Screen %d (%s)",
                active_level,
                active_screen,
                screen_name(active_screen)
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
            active_screen,
            ""
        )
    end

    local function record_life_lost()
        life_lost_count = life_lost_count + 1

        print("=================================")
        print(
            string.format(
                "LIFE LOST #%d",
                life_lost_count
            )
        )
        print(
            string.format(
                "Board: Level %d, Screen %d (%s)",
                active_level,
                active_screen,
                screen_name(active_screen)
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
            active_screen,
            string.format(
                "life_lost_number=%d;previous_lives=%d;"
                .. "current_lives=%d",
                life_lost_count,
                life_loss_previous_lives or current_lives + 1,
                life_loss_new_lives or current_lives
            )
        )
    end

    local function record_level_transition()
        level_transition_count =
            level_transition_count + 1

        print("=================================")
        print(
            string.format(
                "LEVEL TRANSITION #%d",
                level_transition_count
            )
        )
        print(
            string.format(
                "Completed: Level %d, Screen %d (%s)",
                active_level,
                active_screen,
                screen_name(active_screen)
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
            active_screen,
            string.format(
                "level_transition_number=%d",
                level_transition_count
            )
        )
    end

    local function record_bonus_life(
        previous_lives,
        new_lives
    )
        bonus_life_count = bonus_life_count + 1

        print("=================================")
        print(
            string.format(
                "BONUS LIFE EARNED #%d",
                bonus_life_count
            )
        )
        print(
            string.format(
                "Lives remaining: %d -> %d",
                previous_lives,
                new_lives
            )
        )
        print(
            string.format(
                "Score: %d",
                last_valid_score
            )
        )
        print("=================================")

        write_event(
            "bonus_life",
            last_valid_score,
            active_level,
            active_screen,
            string.format(
                "bonus_life_number=%d;previous_lives=%d;"
                .. "current_lives=%d",
                bonus_life_count,
                previous_lives,
                new_lives
            )
        )
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
            active_screen,
            string.format(
                "previous=%d;current=%d",
                previous_lives,
                new_lives
            )
        )
    end

    ------------------------------------------------------
    -- Per-frame game-state reader
    ------------------------------------------------------

    local function read_game_state()

        local machine = manager.machine
        local cpu = machine.devices[":maincpu"]

        if not cpu then
            return
        end

        local space = cpu.spaces["program"]

        if not space then
            return
        end

        local score = read_score(space)

        local board_state =
            space:read_u8(ADDRESS_BOARD_STATE)

        local board_active =
            space:read_u8(ADDRESS_BOARD_ACTIVE)

        local aux_state =
            space:read_u8(ADDRESS_AUX_STATE)

        local raw_screen =
            space:read_u8(ADDRESS_SCREEN_NUMBER)

        local raw_level =
            space:read_u8(ADDRESS_LEVEL_NUMBER)

        local lives_remaining =
            space:read_u8(ADDRESS_LIVES_REMAINING)

        --------------------------------------------------
        -- Detect real game start
        --------------------------------------------------

        if not game_started then

            if score > 0 then
                saw_nonzero_score = true
            end

            if saw_nonzero_score and score == 0 then

                game_started = true
                game_start_time = current_emulated_time()

                last_score = 0
                last_valid_score = 0

                last_board_state = board_state
                last_board_active = board_active
                last_aux_state = aux_state

                current_lives = lives_remaining

                print("Game started!")
                print(
                    string.format(
                        "Initial level byte: %d",
                        raw_level
                    )
                )
                print(
                    string.format(
                        "Initial screen byte: %d (%s)",
                        raw_screen,
                        screen_name(raw_screen)
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
                    raw_screen,
                    ""
                )
            end

            return
        end

        current_lives = lives_remaining

        --------------------------------------------------
        -- Detect a board becoming active
        --------------------------------------------------

        if
            last_board_active ~= 0x02
            and board_active == 0x02
            and raw_level > 0
            and is_valid_screen(raw_screen)
        then
            active_level = raw_level
            active_screen = raw_screen

            if not lives_monitor_initialized then
                last_lives_byte = lives_remaining
                lives_monitor_initialized = true
            end

            if
                last_reported_level ~= active_level
                or last_reported_screen ~= active_screen
            then
                last_reported_level = active_level
                last_reported_screen = active_screen

                record_board_start()
            end
        end

        --------------------------------------------------
        -- Track actual lives changes
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
                life_loss_pending = true
                life_loss_previous_lives = last_lives_byte
                life_loss_new_lives = lives_remaining
            elseif lives_remaining > last_lives_byte then
                record_bonus_life(
                    last_lives_byte,
                    lives_remaining
                )
            end
        end

        --------------------------------------------------
        -- Preserve most recent meaningful score
        --------------------------------------------------

        if score > 0 then
            last_valid_score = score
        end

        --------------------------------------------------
        -- Track every observed score change
        --------------------------------------------------

        if score > 0 and score ~= last_score then

            print(string.format("Score: %d", score))

            write_score(score)

            last_score = score
        end

        --------------------------------------------------
        -- Arm teardown detection during active play
        --------------------------------------------------

        if board_active == 0x02 then
            event_detection_armed = true
        end

        --------------------------------------------------
        -- Classify board teardown
        --
        -- A life decrease reliably precedes death teardown.
        -- Teardown without a life decrease is a successful
        -- board completion.
        --------------------------------------------------

        if
            event_detection_armed
            and last_board_active == 0x02
            and board_active == 0x00
        then
            event_detection_armed = false

            if life_loss_pending then
                record_life_lost()
            else
                record_level_transition()
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

    frame_subscription =
        emu.add_machine_frame_notifier(read_game_state)

    stop_subscription =
        emu.add_machine_stop_notifier(
            function()

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
                        "Level transitions detected: %d",
                        level_transition_count
                    )
                )
                print(
                    string.format(
                        "Bonus lives detected: %d",
                        bonus_life_count
                    )
                )

                stop_subscription = nil
            end
        )

end

return exports