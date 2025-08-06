import json
import os
import matplotlib.pyplot as plt
import csv 
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


DATA_FOLDER = r"C:\Users\caraf\OneDrive\Biodesign\concentration_reporter\data"
SUMMARY_FILE = os.path.join(DATA_FOLDER, "summary.csv") 

# Temporary calibration: 1V -> 10000 µM
def voltage_to_concentration(voltage):
    return voltage * 10000

def extract_voltage_and_time_from_pssession(filepath):
    with open(filepath, 'rb') as file:
        raw = file.read()
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = raw.decode('utf-16')
            except UnicodeDecodeError:
                text = raw.decode('latin1')

    # Try to isolate the first full JSON object
    first_brace = text.find('{')
    last_brace = text.rfind('}') + 1
    cleaned_text = text[first_brace:last_brace]

    try:
        data = json.loads(cleaned_text)
    except json.JSONDecodeError:
        print("Failed to parse JSON. Check if the file is corrupted.")
        return [], []

    values = data["Measurements"][0]["DataSet"]["Values"]
    time_values = next(ds["DataValues"] for ds in values if ds["Description"] == "time")
    voltage_values = next(ds["DataValues"] for ds in values if ds["Description"] == "potential")

    time = [v["V"] for v in time_values]
    voltage = [v["V"] for v in voltage_values if v["S"] == 0]

    min_len = min(len(time), len(voltage))
    return time[:min_len], voltage[:min_len]

def process_file(filepath):
    print(f"\nProcessing file: {filepath}")
    time, voltage = extract_voltage_and_time_from_pssession(filepath)
    concentration = [voltage_to_concentration(v) for v in voltage]

    # Plot
    plt.figure(figsize=(10, 4))
    plt.plot(time, concentration, label='Creatinine (µM)', color='blue')
    plt.xlabel('Time (s)')
    plt.ylabel('Concentration (µM)')
    plt.title(f'Creatinine vs Time - {os.path.basename(filepath)}')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # Stats
    if concentration:
        avg = sum(concentration) / len(concentration)
        std = (sum((x - avg) ** 2 for x in concentration) / len(concentration)) ** 0.5

        # Write to summary.csv
        file_exists = os.path.isfile(SUMMARY_FILE)
        with open(SUMMARY_FILE, mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["Filename", "Average Concentration (uM)", "Standard Deviation (uM)"])
            writer.writerow([os.path.basename(filepath), f"{avg:.2f}", f"{std:.2f}"])
    else:
        print("No valid voltage readings with S=0")

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".pssession"):
            process_file(event.src_path)

def start_monitoring():
    observer = Observer()
    observer.schedule(NewFileHandler(), DATA_FOLDER, recursive=False)
    observer.start()
    print(f"Monitoring folder: {DATA_FOLDER}")
    try:
        while True:
            pass  # Keep script alive
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def plot_summary():
    if not os.path.exists(SUMMARY_FILE):
        print("No summary file found.")
        return

    filenames = []
    avg_concs = []
    std_devs = []

    with open(SUMMARY_FILE, mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            filenames.append(row["Filename"])
            avg_concs.append(float(row["Average Concentration (uM)"]))
            std_devs.append(float(row["Standard Deviation (uM)"]))

    if not filenames:
        print("Summary file is empty.")
        return

    # Plot average concentrations
    plt.figure(figsize=(10, 4))
    plt.bar(filenames, avg_concs, color='skyblue')
    plt.ylabel('Average Concentration (µM)')
    plt.title('Average Creatinine Concentration per File')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

    # Plot standard deviations
    plt.figure(figsize=(10, 4))
    plt.bar(filenames, std_devs, color='orange')
    plt.ylabel('Standard Deviation (µM)')
    plt.title('Standard Deviation of Creatinine Concentration per File')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    mode = input("Type 'monitor' to watch for new files or 'summary' to plot summary data:\n").strip().lower()

    if mode == "monitor":
        start_monitoring()
    elif mode == "summary":
        plot_summary()
    else:
        print("Unknown option. Exiting.")