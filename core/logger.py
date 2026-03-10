import csv
import os
from datetime import datetime

LOG_FILE = "simulated_telemetry_log.csv"

def setup_logger():
    """
    Creates the CSV file and writes the column headers if it doesn't already exist.
    """
    headers = [
        "timestamp", 
        "time_step", 
        "fault_scenario", 
        "fhs_score",
        "node_temperature_c", 
        "disk_read_latency_ms",
        "smart_uncorrectable_errors", 
        "replica_availability_ratio",
        "checksum_mismatch_flag"
    ]
    
    # Only write headers if the file is new
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

def log_telemetry(time_step, scenario, fhs_score, metrics):
    """
    Appends a single row of telemetry data to the CSV file.
    """
    row = [
        datetime.now().isoformat(),  # Real-world timestamp
        time_step,                   # Simulation tick
        scenario,                    # e.g., "baseline" or "degradation"
        fhs_score,                   # The calculated health score
        round(metrics["node_temperature_c"], 2),
        metrics["disk_read_latency_ms"],
        metrics["smart_uncorrectable_errors"],
        round(metrics["replica_availability_ratio"], 2),
        metrics["checksum_mismatch_flag"]
    ]
    
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)