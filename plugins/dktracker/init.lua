local exports = {
	name = "dktracker",
	version = "0.0.3",
	description = "Donkey Kong Tracker",
	license = "MIT",
	author = { name = "Nick" }
}

local dktracker = exports


local function bcd_to_decimal(value)
	local high = (value >> 4) & 0x0F
	local low = value & 0x0F
	return high * 10 + low
end


function dktracker.startplugin()

	print("=================================")
	print("DK Tracker loaded!")
	print("=================================")

local last_score = -1
local saw_nonzero = false
local game_started = false


	local function read_score()

		local machine = manager.machine
		local cpu = machine.devices[":maincpu"]

		if cpu then
	local space = cpu.spaces["program"]

if not space then
    return
end

	local byte1 = space:read_u8(0x60B3)
local byte2 = space:read_u8(0x60B4)

local score =
    bcd_to_decimal(byte2) * 10000 +
    bcd_to_decimal(byte1) * 100

		if not game_started then

    if score > 0 then
        saw_nonzero = true
    end

    if saw_nonzero and score == 0 then
        game_started = true
        last_score = 0
        print("Game started!")
    end

else

    if score ~= last_score then
        print(
            string.format(
                "Score changed: %d  (bytes: %02X %02X)",
                score,
                byte1,
                byte2
            )
        )
    end

end

last_score = score
		end

	end


	emu.register_periodic(read_score, 1)

end

return exports