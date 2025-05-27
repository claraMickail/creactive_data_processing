import os
import pandas as pd
import numpy as np 


DATA_DIR = "data"  # Directory where .pss files are stored
CALIBRATION_SLOPE = 0.01  # µM per µA - replace 
CALIBRATION_INTERCEPT = 0.05  # µM offset - replace

# Google says:
# A linear equation to convert peak current to concentration is often represented as y = mx + b, 
# where y is the peak current, x is the concentration, m is the slope (response factor), 
# and b is the y-intercept. This equation is derived from a calibration curve, 
# which is a plot of peak current values against known concentrations. 
# i.e concentration =  (current_peak - CALIBRATION_INTERCEPT) / CALIBRATION_SLOPE

# ---- Parse .pss file ----
def parse_file(filepath):
    """
    Parses a .pss file and returns a DataFrame with Voltage and Current.
    Assumes columns are space-separated and the first two are voltage/current.
    """
    with open(filepath, 'r') as file:
        lines = file.readlines()

    # Keep only lines that look like data (start with a digit or minus sign)
    data_lines = [line.strip() for line in lines if line.strip() and (line[0].isdigit() or line[0] == '-')]
    
    # Split and extract just the first two columns (assumed: voltage and current; will need to figure out what the other two variables are)
    data = [list(map(float, line.split()[:2])) for line in data_lines]  
    df = pd.DataFrame(data, columns=["Voltage (V)", "Current (µA)"])  # pack result in neat table
    return df

# def calibrate(concentrations, peak_currents):
#     """
#     Performs linear regression to find the calibration slope (m) and intercept (b)
#     from known concentrations and their corresponding peak currents.
#     """
#     # Ensure inputs are numpy arrays
#     concentrations = np.array(concentrations)
#     peak_currents = np.array(peak_currents)
    
#     # Fit a line: y = mx + b
#     m, b = np.polyfit(concentrations, peak_currents, 1)

#     print("Calibration Results:")
#     print(f"  Slope (m): {m:.5f} µA/µM")
#     print(f"  Intercept (b): {b:.5f} µA")
    
#     return m, b

# ---- Use calibration to get concentration ----
def estimate_concentration(current_peak):
    """
    Converts a peak current to concentration using a linear calibration model.
    """
    return (current_peak - CALIBRATION_INTERCEPT) / CALIBRATION_SLOPE #adjust relationship

# ---- Handle a single file ----
def process_file(filepath):
    print(f"\nProcessing file: {filepath}")
    df = parse_file(filepath)
    
    # Find the largest absolute current peak
    peak_current = df["Current (µA)"].abs().max()
    
    # Estimate concentration using calibration
    concentration = estimate_concentration(peak_current)
    
    # Show results in terminal
    print(f"Peak Current: {peak_current:.2f} µA")
    print(f"Estimated Concentration: {concentration:.2f} µM")
    
    # Save to a log file
    result = pd.DataFrame([[os.path.basename(filepath), peak_current, concentration]],
                          columns=["File", "Peak Current (µA)", "Estimated Concentration (µM)"])
    log_path = os.path.join("concentration_log.csv")
    
    # Append or create new log
    if os.path.exists(log_path):
        result.to_csv(log_path, mode='a', header=False, index=False)
    else:
        result.to_csv(log_path, index=False)

    print("Logged to concentration_log.csv")

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Loop through all .pss files in the data folder
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".pss"):
            process_file(os.path.join(DATA_DIR, fname))



# -- NEXT STEPS --
# When new file added, automatically track and update with watchdog
# Nice visuals and graphs