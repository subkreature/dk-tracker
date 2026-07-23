local exports = {
    name = "dktracker",
    version = "0.0.9",
    description = "Donkey Kong Tracker",
    license = "MIT",
    author = { name = "Nick" }
}

local dktracker = exports

----------------------------------------------------------
-- Configuration
----------------------------------------------------------

local DEBUG_GAME_STATE = true

----------------------------------------------------------
-- Memory addresses
----------------------------------------------------------

local ADDRESS_SCORE_LOW = 0x60B3
local ADDRESS_SCORE_HIGH = 0x60B4

local ADDRESS_BOARD_STATE = 0x608A
local ADDRESS_BOARD_ACTIVE = 0x6208
local ADDRESS_AUX_STATE = 0x694E

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

----------------------------------------------------------
-- Plugin
----------------------------------------------------------

function dktracker.startplugin()

    print("=================================")
    print("DK Tracker loaded from DK-Tracker project!")
    print("Version: " .. exports.version)
    print("=================================")

    ------------------------------------------------------
    -- Open score log
    ------------------------------------------------------

    local pathfile = io.open("score_path.txt", "r")

    if not pathfile then
        print("ERROR: Could not find score_path.txt")
        return
    end

    local score_path = pathfile:read("*line")
    pathfile:close()

    local logfile = io.open(score_path, "w")

    if not logfile then
        print("ERROR: Could not create score log")
        return
    end

    logfile:write("score\n")
    logfile:flush()

    ------------------------------------------------------
    -- Runtime state
    ------------------------------------------------------

    local last_score = -1
    local last_valid_score = 0

    local saw_nonzero_score = false
    local game_started = false

    local last_board_state = nil
    local last_board_active = nil
    local last_aux_state = nil

    local board_completion_pending = false
    local event_detection_armed = false

    local life_lost_count = 0
    local level_transition_count = 0

    ------------------------------------------------------
    -- Event output
    ------------------------------------------------------

    local function print_life_lost()
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
                "Score at death: %d",
                last_valid_score
            )
        )
        print("=================================")
    end

    local function print_level_transition()
        level_transition_count = level_transition_count + 1

        print("=================================")
        print(
            string.format(
                "LEVEL TRANSITION #%d",
                level_transition_count
            )
        )
        print(
            string.format(
                "Score after board clear: %d",
                last_valid_score
            )
        )
        print("=================================")
    end

    ------------------------------------------------------
    -- Periodic game-state reader
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

        --------------------------------------------------
        -- Detect real game start
        --------------------------------------------------

        if not game_started then

            if score > 0 then
                saw_nonzero_score = true
            end

            if saw_nonzero_score and score == 0 then

                game_started = true
                last_score = 0
                last_valid_score = 0

                last_board_state = board_state
                last_board_active = board_active
                last_aux_state = aux_state

                print("Game started!")

                logfile:write("0\n")
                logfile:flush()
            end

            return
        end

        --------------------------------------------------
        -- Preserve the most recent real score
        --------------------------------------------------

        if score > 0 then
            last_valid_score = score
        end

        --------------------------------------------------
        -- Track score changes
        --------------------------------------------------

        if score ~= last_score then

            print(string.format("Score: %d", score))

            logfile:write(string.format("%d\n", score))
            logfile:flush()

            last_score = score
        end

        --------------------------------------------------
        -- Arm event detection while a board is active
        --------------------------------------------------

        if board_active == 0x02 then
            event_detection_armed = true
        end

        --------------------------------------------------
        -- Detect successful board completion
        --
        -- Observed at the end of Level 1-1:
        --
        --   608A: 06 -> 07
        --------------------------------------------------

        if
            last_board_state ~= nil
            and last_board_state ~= 0x07
            and board_state == 0x07
        then
            board_completion_pending = true

            if DEBUG_GAME_STATE then
                print("Board completion state detected: 608A = 07")
            end
        end

        --------------------------------------------------
        -- Classify board teardown
        --
        -- Observed teardown:
        --
        --   6208: 02 -> 00
        --
        -- If 608A previously reached 07, classify this as
        -- a successful level transition. Otherwise, treat
        -- it as a life lost.
        --------------------------------------------------

        if
            event_detection_armed
            and last_board_active == 0x02
            and board_active == 0x00
        then

            event_detection_armed = false

            if board_completion_pending then
                print_level_transition()
            else
                print_life_lost()
            end

            board_completion_pending = false
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
        -- Save current state for next check
        --------------------------------------------------

        last_board_state = board_state
        last_board_active = board_active
        last_aux_state = aux_state
    end

    ------------------------------------------------------
    -- Register callbacks
    ------------------------------------------------------

    emu.register_periodic(read_game_state, 1)

    emu.add_machine_stop_notifier(
        function()

            if logfile then
                logfile:close()
                logfile = nil
            end

            print("Score log saved.")
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
        end
    )

end

return exports