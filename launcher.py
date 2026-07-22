import subprocess
from datetime import datetime
import csv
from pathlib import Path

print("===================================")
print("        DK Tracker")
print("===================================")
print()

start_time = datetime.now()

print(f"Session started: {start_time}")

subprocess.run(
    [
        "./mame",
        "dkong",
        "-plugin",
        "dktracker"
    ],
    cwd="/Users/nick/Downloads/mame0286-x86"
)

end_time = datetime.now()

duration = end_time - start_time

print()
print("Game finished!")
print(f"Ended: {end_time}")
print(f"Duration: {duration}")

data_folder = Path("data")
data_folder.mkdir(exist_ok=True)

csv_file = data_folder / "sessions.csv"

file_exists = csv_file.exists()

with open(csv_file, "a", newline="") as file:
    writer = csv.writer(file)

    if not file_exists:
        writer.writerow([
            "start_time",
            "end_time",
            "duration_seconds"
        ])

    writer.writerow([
        start_time.isoformat(),
        end_time.isoformat(),
        int(duration.total_seconds())
    ])

print()
print("Session saved.")