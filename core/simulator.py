import random

def get_initial_metrics():
    """
    Returns the baseline healthy state of a storage node and its hosted file.
    """
    return {
        "node_id": "node-alpha-04",
        "node_temperature_c": 35.0,
        "disk_read_latency_ms": 12,
        "smart_uncorrectable_errors": 0,
        "replica_availability_ratio": 1.0,
        "checksum_mismatch_flag": 0
    }

def update_metrics(metrics, fault_type, time_step):
    """
    Takes the current metrics, applies natural fluctuations, and injects 
    specific fault scenarios if requested. Modifies the metrics dictionary in place.
    """
    
    # 1. Natural Baseline Fluctuations (Always active)
    # Temperature naturally fluctuates by +/- 0.5 degrees
    metrics["node_temperature_c"] += random.uniform(-0.5, 0.5)
    
    # Latency naturally fluctuates by +/- 2ms, but never goes below 5ms
    metrics["disk_read_latency_ms"] = max(5, metrics["disk_read_latency_ms"] + random.randint(-2, 2))

    # 2. Inject Specific Fault Scenarios
    if fault_type == "degradation":
        # Simulate physical drive burning out
        metrics["node_temperature_c"] += 2.5
        metrics["disk_read_latency_ms"] += 15
        
        # Throw a SMART hardware error every 2 time steps
        if time_step % 2 == 0:
            metrics["smart_uncorrectable_errors"] += 1
            
    elif fault_type == "partition":
        # Simulate a network switch dying (1 out of 3 replicas drops)
        metrics["replica_availability_ratio"] = 0.66
        
    elif fault_type == "corruption":
        # Simulate a silent bit flip (hash no longer matches)
        metrics["checksum_mismatch_flag"] = 1
        
    elif fault_type == "baseline":
        # If explicitly set back to baseline, instantly heal logical errors
        # (Physical metrics like temp will naturally cool down over time if we programmed 
        # a cooling curve, but for the prototype, we just fix the logical flags)
        metrics["replica_availability_ratio"] = 1.0
        metrics["checksum_mismatch_flag"] = 0
        
        # Gradually cool down the physical hardware if it was running hot
        if metrics["node_temperature_c"] > 35.0:
            metrics["node_temperature_c"] -= 1.5
        if metrics["disk_read_latency_ms"] > 12:
            metrics["disk_read_latency_ms"] -= 5

    return metrics