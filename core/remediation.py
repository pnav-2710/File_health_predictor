def execute_remediation(metrics, remedy_action):
    """
    Takes the selected remedy action from the LLM and applies the appropriate 
    state changes to the system metrics to simulate a successful recovery.
    """
    
    print(f"🔧 Executing Automated Remediation: {remedy_action}")
    
    # Create a copy of the metrics so we don't accidentally mutate the original 
    # before we are ready
    healed_metrics = metrics.copy()
    message = ""

    if remedy_action == "MIGRATE_PRIMARY_NODE" or remedy_action == "MIGRATE_NODE":
        # Simulate moving the file to a brand new, healthy physical server
        healed_metrics["node_temperature_c"] = 35.0
        healed_metrics["disk_read_latency_ms"] = 12
        healed_metrics["smart_uncorrectable_errors"] = 0
        message = "File successfully migrated to a healthy node. Hardware metrics normalized."
        
    elif remedy_action == "REBUILD_REPLICA":
        # Simulate spinning up a new container/node to replace the dead one
        healed_metrics["replica_availability_ratio"] = 1.0
        message = "Missing replica successfully rebuilt. Redundancy restored to 100%."
        
    elif remedy_action == "RESTORE_FROM_SNAPSHOT" or remedy_action == "RECALCULATE_CHECKSUM":
        # Simulate rolling back the corrupted file to a clean backup
        healed_metrics["checksum_mismatch_flag"] = 0
        message = "Corrupted data overwritten with clean snapshot. Checksum integrity restored."
        
    elif remedy_action == "IGNORE":
        message = "Action ignored as per SRE directive. No changes made."
        
    else:
        message = f"Unknown action '{remedy_action}'. Reverting to baseline safety protocols."
        # Fallback: Just reset to baseline if the LLM hallucinated an action
        healed_metrics["replica_availability_ratio"] = 1.0
        healed_metrics["checksum_mismatch_flag"] = 0
        healed_metrics["node_temperature_c"] = 35.0
        healed_metrics["disk_read_latency_ms"] = 12
        healed_metrics["smart_uncorrectable_errors"] = 0

    return healed_metrics, message