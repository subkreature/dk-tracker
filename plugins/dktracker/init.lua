local exports = {
    name = "dktracker",
    version = "0.0.4",
    description = "Donkey Kong Tracker",
    license = "MIT",
    author = { name = "Nick" }
}

local dktracker = exports

----------------------------------------------------------
-- Helpers
----------------------------------------------------------

local function bcd_to_decimal(value)
    local high = (value >> 4) & 0x0F
    local low = value & 0x0F
    return high * 10 + low
end

----------------------------------------------------------
-- Plugin
----------------------------------------------------------

function dktracker.startplugin()

    print("=================================")
    print("DK Tracker loaded from DK-Tracker project!")
    print("=================================")

local pathfile = io.open("score_path.txt", "r")

if not pathfile then
    print("ERROR: Could not find score_path.txt")
    return
end

local score_path = pathfile:read("*line")
pathfile:close()

local logfile = io.open(score_path, "w")
    if not logfile then
        print("ERROR: Couldn't create score_log.csv")
        return
    end

    logfile:write("score\n")
    logfile:flush()

    local last_score = -1
    local saw_nonzero = false
    local game_started = false

    local function read_score()

        local machine = manager.machine
        local cpu = machine.devices[":maincpu"]

        if not cpu then
            return
        end

        local space = cpu.spaces["program"]

        if not space then
            return
        end

        local byte1 = space:read_u8(0x60B3)
        local byte2 = space:read_u8(0x60B4)

        local score =
            bcd_to_decimal(byte2) * 10000 +
            bcd_to_decimal(byte1) * 100

        --------------------------------------------------
        -- Wait until an actual game has started
        --------------------------------------------------

        if not game_started then

            if score > 0 then
                saw_nonzero = true
            end

            if saw_nonzero and score == 0 then
                game_started = true
                last_score = 0

                print("Game started!")

                logfile:write("0\n")
                logfile:flush()
            end

            return
        end

        --------------------------------------------------
        -- Record score changes
        --------------------------------------------------

        if score ~= last_score then

            print(string.format("Score: %d", score))

            logfile:write(string.format("%d\n", score))
            logfile:flush()

            last_score = score
        end
    end

    emu.register_periodic(read_score, 1)

    emu.register_stop(function()
        logfile:close()
        print("Score log saved.")
    end)

end

return exports