def calculate_fhs(metrics):
    # 1. Checksum (35% Weight)
    chk_score = 1.0 if metrics['checksum_mismatch_flag'] == 0 else 0.0
    
    # 2. Replicas (25% Weight)
    # STRICT PENALTY: If we lose a replica (ratio drops below 1.0), this score goes to 0.0
    rep_score = 1.0 if metrics['replica_availability_ratio'] >= 1.0 else 0.0
    
    # 3. Node Temperature (15% Weight)
    temp_score = max(0.0, 1.0 - ((metrics['node_temperature_c'] - 30) / 50))
    
    # 4. Read Latency (15% Weight)
    lat_score = max(0.0, 1.0 - (metrics['disk_read_latency_ms'] / 200))
    
    # 5. SMART Errors (10% Weight)
    err_score = max(0.0, 1.0 - (metrics['smart_uncorrectable_errors'] / 10))
    
    fhs = (0.35 * chk_score) + (0.25 * rep_score) + (0.15 * temp_score) + (0.15 * lat_score) + (0.10 * err_score)
    return round(fhs * 100, 2)

def is_critical_threshold_breached(fhs_score, threshold=75.0):
    """
    Evaluates if the current health score has dropped below the safe threshold.
    Returns True if the LLM diagnostic engine needs to be triggered.
    """
    return fhs_score < threshold