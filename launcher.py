import subprocess

print("===================================")
print("        DK Tracker")
print("===================================")
print()
print("Launching Donkey Kong...")

subprocess.run(
    ["./mame", "dkong"],
    cwd="/Users/nick/Downloads/mame0286-x86"
)