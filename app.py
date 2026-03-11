import streamlit as st
import time
import random
import json
import pandas as pd
from core import logger
from core import llm_engine
from core import remediation
from core.monitor import calculate_fhs
import os
os.environ["GEMINI_API_KEY"] = "key"

if 'diagnosis_history' not in st.session_state:
    st.session_state.diagnosis_history = []
# -----------------------------------------------------

if 'fhs_history' not in st.session_state:
    st.session_state.fhs_history = []
if 'time_step' not in st.session_state:
    st.session_state.time_step = 0

# --- ADD THIS NEW BLOCK ---
if 'metrics_history' not in st.session_state:
    st.session_state.metrics_history = {
        "temp": [], "latency": [], "errors": [], "replicas": [], "checksum": []
    }
# --------------------------

# Create the CSV file when the app starts
logger.setup_logger()
# --- 1. Core FHS Calculation ---
# def calculate_fhs(metrics):
#     chk_score = 1.0 if metrics['checksum_mismatch_flag'] == 0 else 0.0
#     rep_score = metrics['replica_availability_ratio']
#     temp_score = max(0.0, 1.0 - ((metrics['node_temperature_c'] - 30) / 50))
#     lat_score = max(0.0, 1.0 - (metrics['disk_read_latency_ms'] / 200))
#     err_score = max(0.0, 1.0 - (metrics['smart_uncorrectable_errors'] / 10))
    
#     fhs = (0.35 * chk_score) + (0.25 * rep_score) + (0.15 * temp_score) + (0.15 * lat_score) + (0.10 * err_score)
#     return round(fhs * 100, 2)

# --- 2. Initialize Session State (The "Memory") ---
if 'running' not in st.session_state:
    st.session_state.running = False
if 'fault_type' not in st.session_state:
    st.session_state.fault_type = "baseline"
if 'fhs_history' not in st.session_state:
    st.session_state.fhs_history = []
if 'time_step' not in st.session_state:
    st.session_state.time_step = 0

# Initial Healthy Metrics
if 'metrics' not in st.session_state:
    st.session_state.metrics = {
        "node_id": "node-alpha-04",
        "node_temperature_c": 35.0,
        "disk_read_latency_ms": 12,
        "smart_uncorrectable_errors": 0,
        "replica_availability_ratio": 1.0,
        "checksum_mismatch_flag": 0
    }

# --- 3. UI Layout & Sidebar Controls --
st.set_page_config(page_title="Storage AIOps Monitor", layout="wide")
st.title("Self-Healing Storage Monitor") # Back to a clean, simple title!# --- Header with History Button on the Right ---
# h_col1, h_col2 = st.columns([4, 1]) # Makes the title wide, button narrow
# with h_col1:
#     st.title("Self-Healing Storage Monitor")
# with h_col2:
#     st.write("") # Tiny padding to push the button down to align with the title
#     with st.popover("📜 View Diagnosis History", use_container_width=True):
#         st.subheader("Past AI Diagnoses")
#         if len(st.session_state.diagnosis_history) == 0:
#             st.info("No faults diagnosed yet. The system is healthy.")
#         else:
#             # Show the newest alerts at the top
#             for record in reversed(st.session_state.diagnosis_history): 
#                 st.markdown(f"**Tick {record['time_step']} | Fault Triggered**")
#                 st.error(f"**Cause:** {record['root_cause']}")
#                 st.success(f"**Action:** {record['action']}")
#                 st.divider()
st.sidebar.header("System Controls")

# Start/Stop Buttons
col1, col2 = st.sidebar.columns(2)
if col1.button("▶️ Start System", use_container_width=True):
    st.session_state.running = True
    st.rerun()
if col2.button("⏹️ Stop System", use_container_width=True):
    st.session_state.running = False
    st.rerun()

st.sidebar.divider()
st.sidebar.header("Inject Fault Scenarios")

# Fault Injection Buttons
if st.sidebar.button("🔥 Gradual Degradation", use_container_width=True):
    st.session_state.fault_type = "degradation"
if st.sidebar.button("🔌 Network Partition", use_container_width=True):
    st.session_state.fault_type = "partition"
if st.sidebar.button("👾 Silent Data Corruption", use_container_width=True):
    st.session_state.fault_type = "corruption"
if st.sidebar.button("✅ Reset to Healthy (Baseline)", use_container_width=True):
    st.session_state.fault_type = "baseline"

# --- NEW: SIDEBAR AUDIT LOG ---
st.sidebar.divider()
st.sidebar.header("Audit & Logs")

with st.sidebar.popover("📜 View Diagnosis History", use_container_width=True):
    st.subheader("Past AI Diagnoses")
    if len(st.session_state.diagnosis_history) == 0:
        st.info("No faults diagnosed yet. The system is healthy.")
    else:
        # Show the newest alerts at the top
        for record in reversed(st.session_state.diagnosis_history): 
            st.markdown(f"**Tick {record['time_step']} | Fault Triggered**")
            st.error(f"**Cause:** {record['root_cause']}")
            st.info(f"**Reasoning:** {record['reasoning']}") # <-- NEW: Shows the logic!
            st.success(f"**Action:** {record['action']}")
            st.divider()

# # --- 4. Main Dashboard Placeholders ---
# # We use placeholders so we can update them in the loop without creating new elements
# metric_cols = st.columns(4)
# fhs_metric = metric_cols[0].empty()
# temp_metric = metric_cols[1].empty()
# lat_metric = metric_cols[2].empty()
# err_metric = metric_cols[3].empty()

# st.subheader("Real-Time File Health Score (FHS)")
# chart_placeholder = st.empty()

# st.subheader("Live Telemetry Stream")
# log_placeholder = st.empty()

# # --- The Master Reset Callback ---
# def apply_automated_fix():
#     # 1. Force perfect "God Mode" factory metrics
#     st.session_state.metrics["node_temperature_c"] = 35.0
#     st.session_state.metrics["disk_read_latency_ms"] = 12
#     st.session_state.metrics["smart_uncorrectable_errors"] = 0
#     st.session_state.metrics["replica_availability_ratio"] = 1.0
#     st.session_state.metrics["checksum_mismatch_flag"] = 0
    
#     # 2. Reset system flags back to healthy
#     st.session_state.fault_type = "baseline"
#     st.session_state.fhs_history = []
#     st.session_state.running = True
    
#     # 3. Wipe the AI's memory for the next disaster
#     if 'current_diagnosis' in st.session_state:
#         del st.session_state['current_diagnosis']

# # --- 5. The Real-Time Streaming Loop ---
# if st.session_state.running:
#     # 1. Apply Baseline Fluctuations
#     st.session_state.metrics["node_temperature_c"] += random.uniform(-0.5, 0.5)
#     st.session_state.metrics["disk_read_latency_ms"] = max(5, st.session_state.metrics["disk_read_latency_ms"] + random.randint(-2, 2))

#     # 2. Apply Fault Injections based on UI clicks
#     if st.session_state.fault_type == "degradation":
#         st.session_state.metrics["node_temperature_c"] += 2.5
#         st.session_state.metrics["disk_read_latency_ms"] += 15
#         if st.session_state.time_step % 2 == 0:
#             st.session_state.metrics["smart_uncorrectable_errors"] += 1
            
#     elif st.session_state.fault_type == "partition":
#         st.session_state.metrics["replica_availability_ratio"] = 0.66
        
#     elif st.session_state.fault_type == "corruption":
#         st.session_state.metrics["checksum_mismatch_flag"] = 1
        
#     elif st.session_state.fault_type == "baseline":
#         # Slowly recover if set back to baseline manually
#         st.session_state.metrics["replica_availability_ratio"] = 1.0
#         st.session_state.metrics["checksum_mismatch_flag"] = 0

#     # 3. Calculate FHS
#     current_fhs = calculate_fhs(st.session_state.metrics)
#     logger.log_telemetry(
#     st.session_state.time_step, 
#     st.session_state.fault_type, 
#     current_fhs, 
#     st.session_state.metrics
#     )
#     st.session_state.fhs_history.append(current_fhs)
#     # Keep chart history to last 50 ticks
#     if len(st.session_state.fhs_history) > 50:
#         st.session_state.fhs_history.pop(0)

#     # 4. Update UI Elements
#     fhs_metric.metric("FHS (0-100)", f"{current_fhs}", delta=f"{current_fhs - 100:.2f}" if current_fhs < 100 else "Perfect")
#     temp_metric.metric("Temperature", f"{st.session_state.metrics['node_temperature_c']:.1f} °C")
#     lat_metric.metric("Latency", f"{st.session_state.metrics['disk_read_latency_ms']} ms")
#     err_metric.metric("Uncorrectable Errors", f"{st.session_state.metrics['smart_uncorrectable_errors']}")

#     chart_placeholder.line_chart(st.session_state.fhs_history)

#     payload = {
#         "time_step": st.session_state.time_step,
#         "fault_scenario_active": st.session_state.fault_type,
#         "fhs_score": current_fhs,
#         "telemetry": st.session_state.metrics
#     }
#     log_placeholder.json(payload)

#     # 5. Check Threshold and Trigger LLM Alert
#     # 5. Check Threshold and Trigger LLM Alert
#     # 5. Check Threshold and Trigger LLM Alert
#     if current_fhs < 75.0:
#         st.error(f"🚨 CRITICAL ALERT: FHS dropped to {current_fhs}! Threshold breached.")
#         st.warning("⏸️ Stream paused. Packaging telemetry and invoking LLM SRE Diagnostic Engine...")
        
#         # --- THE FIX: ONLY CALL THE API ONCE PER FAULT ---
#         if 'current_diagnosis' not in st.session_state:
#             with st.spinner("🤖 AIOps Agents analyzing telemetry and determining root cause..."):
#                 try:
#                     # Call the API and SAVE it to memory
#                     st.session_state.current_diagnosis = llm_engine.run_aiops_diagnosis(st.session_state.metrics, current_fhs)
#                 except Exception as e:
#                     st.error(f"❌ LLM Engine Failed. Error: {e}")
#                     st.stop()
                    
#         # Retrieve the saved diagnosis from memory
#         diagnosis = st.session_state.current_diagnosis
#         # --------------------------------------------------
            
#         # Display the AI's structured response
#         st.markdown("### 🧠 AI Diagnostic Report")
#         st.error(f"**Diagnosed Root Cause:** {diagnosis.get('root_cause', 'Error')}")
#         st.info(f"**Agent Reasoning:** {diagnosis.get('reasoning', 'Error')}")
#         st.success(f"**Automated Remedy Action:** {diagnosis.get('remedy_action', 'Error')}")
        
#         st.divider()
#         st.subheader("⚙️ Execute Self-Healing Protocol")
        
#         # --- The Execution Button ---
#         st.button("Authorize & Execute Fix", type="primary", on_click=apply_automated_fix)
            
#         st.stop() # Stops the script from continuing so you can click the button
#     st.session_state.time_step += 1
#     time.sleep(1)
#     st.rerun()

# --- The Master Reset Callback ---
# --- The Master Reset Callback ---
def apply_automated_fix():
    # 1. Force perfect "God Mode" factory metrics
    st.session_state.metrics["node_temperature_c"] = 35.0
    st.session_state.metrics["disk_read_latency_ms"] = 12
    st.session_state.metrics["smart_uncorrectable_errors"] = 0
    st.session_state.metrics["replica_availability_ratio"] = 1.0
    st.session_state.metrics["checksum_mismatch_flag"] = 0
    
    # 2. Reset system flags back to healthy
    st.session_state.fault_type = "baseline"
    st.session_state.fhs_history = []
    st.session_state.running = True
    
    # --- NEW: WIPE THE RAW METRIC HISTORY ---
    st.session_state.metrics_history = {
        "temp": [], "latency": [], "errors": [], "replicas": [], "checksum": []
    }
    
    # 3. Wipe the AI's memory for the next disaster
    if 'current_diagnosis' in st.session_state:
        del st.session_state['current_diagnosis']

# --- 4 & 5. The Real-Time Dashboard (Fragment) ---
# The run_every=1 tells Streamlit to auto-loop this specific function in the background
@st.fragment(run_every=1)
def live_dashboard():
    
    # 1. Only increment data if the system is running
    if st.session_state.running:
        st.session_state.time_step += 1
        
        # Apply Baseline Fluctuations
        st.session_state.metrics["node_temperature_c"] += random.uniform(-0.5, 0.5)
        st.session_state.metrics["disk_read_latency_ms"] = max(5, st.session_state.metrics["disk_read_latency_ms"] + random.randint(-2, 2))

        # Apply Fault Injections based on UI clicks
        if st.session_state.fault_type == "degradation":
            st.session_state.metrics["node_temperature_c"] += 2.5
            st.session_state.metrics["disk_read_latency_ms"] += 15
            if st.session_state.time_step % 2 == 0:
                st.session_state.metrics["smart_uncorrectable_errors"] += 1
                
        elif st.session_state.fault_type == "partition":
            st.session_state.metrics["replica_availability_ratio"] = 0.66
            
        elif st.session_state.fault_type == "corruption":
            st.session_state.metrics["checksum_mismatch_flag"] = 1
            
        elif st.session_state.fault_type == "baseline":
            # Slowly recover if set back to baseline manually
            st.session_state.metrics["replica_availability_ratio"] = 1.0
            st.session_state.metrics["checksum_mismatch_flag"] = 0

        # Calculate FHS & Log
        current_fhs = calculate_fhs(st.session_state.metrics)
        logger.log_telemetry(st.session_state.time_step, st.session_state.fault_type, current_fhs, st.session_state.metrics)
        
        st.session_state.fhs_history.append(current_fhs)
        if len(st.session_state.fhs_history) > 50:
            st.session_state.fhs_history.pop(0)

        st.session_state.metrics_history["temp"].append(st.session_state.metrics["node_temperature_c"])
        st.session_state.metrics_history["latency"].append(st.session_state.metrics["disk_read_latency_ms"])
        st.session_state.metrics_history["errors"].append(st.session_state.metrics["smart_uncorrectable_errors"])
        st.session_state.metrics_history["replicas"].append(st.session_state.metrics["replica_availability_ratio"])
        st.session_state.metrics_history["checksum"].append(st.session_state.metrics["checksum_mismatch_flag"])
        
        # Keep histories to last 50 ticks to match FHS
        for key in st.session_state.metrics_history:
            if len(st.session_state.metrics_history[key]) > 50:
                st.session_state.metrics_history[key].pop(0)
            
        # Pause the stream if threshold is breached
        if current_fhs < 75.0:
            st.session_state.running = False
            
    else:
        # If paused, just calculate the score of the current broken metrics
        current_fhs = calculate_fhs(st.session_state.metrics)

    # 2. Render the UI (This draws seamlessly without flickering the whole page!)
    metric_cols = st.columns(4)
    metric_cols[0].metric("FHS (0-100)", f"{current_fhs}", delta=f"{current_fhs - 100:.2f}" if current_fhs < 100 else "Perfect")
    metric_cols[1].metric("Temperature", f"{st.session_state.metrics['node_temperature_c']:.1f} °C")
    metric_cols[2].metric("Latency", f"{st.session_state.metrics['disk_read_latency_ms']} ms")
    metric_cols[3].metric("Uncorrectable Errors", f"{st.session_state.metrics['smart_uncorrectable_errors']}")

    st.subheader("Real-Time File Health Score (FHS)")
    st.line_chart(st.session_state.fhs_history)

    # --- NEW: The Mini-Chart Grid ---
    st.subheader("Raw Telemetry Trends")
    
    # Row 1: 3 Columns
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    with r1_c1:
        st.caption("Temperature (°C)")
        st.line_chart(st.session_state.metrics_history["temp"], height=150)
    with r1_c2:
        st.caption("Latency (ms)")
        st.line_chart(st.session_state.metrics_history["latency"], height=150)
    with r1_c3:
        st.caption("SMART Errors")
        st.line_chart(st.session_state.metrics_history["errors"], height=150)
        
    # Row 2: 2 Columns
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    with r2_c1:
        st.caption("Replica Ratio")
        st.line_chart(st.session_state.metrics_history["replicas"], height=150)
    with r2_c2:
        st.caption("Checksum Mismatch")
        st.line_chart(st.session_state.metrics_history["checksum"], height=150)
    # --------------------------------
    
    st.subheader("Live JSON Telemetry")

    st.subheader("Live Telemetry Stream")
    payload = {
        "time_step": st.session_state.time_step,
        "fault_scenario_active": st.session_state.fault_type,
        "fhs_score": current_fhs,
        "telemetry": st.session_state.metrics
    }
    st.json(payload)

    # 3. Check Threshold and Trigger LLM Alert
    if current_fhs < 75.0:
        st.error(f"🚨 CRITICAL ALERT: FHS dropped to {current_fhs}! Threshold breached.")
        st.warning("⏸️ Stream paused. Packaging telemetry and invoking LLM SRE Diagnostic Engine...")
        
        if 'current_diagnosis' not in st.session_state:
            with st.spinner("🤖 AIOps Agents analyzing telemetry and determining root cause..."):
                try:
                    st.session_state.current_diagnosis = llm_engine.run_aiops_diagnosis(st.session_state.metrics, current_fhs)
                    
                    st.session_state.diagnosis_history.append({
                        "time_step": st.session_state.time_step,
                        "root_cause": st.session_state.current_diagnosis.get('root_cause', 'Unknown'),
                        "reasoning": st.session_state.current_diagnosis.get('reasoning', 'No reasoning provided.'),
                        "action": st.session_state.current_diagnosis.get('remedy_action', 'Unknown')
                    })
                    # -----------------------------------------
                except Exception as e:
                    st.error(f"❌ LLM Engine Failed. Error: {e}")
                    st.stop()
                    
        diagnosis = st.session_state.current_diagnosis
            
        st.markdown("### 🧠 AI Diagnostic Report")
        st.error(f"**Diagnosed Root Cause:** {diagnosis.get('root_cause', 'Error')}")
        st.info(f"**Agent Reasoning:** {diagnosis.get('reasoning', 'Error')}")
        st.success(f"**Automated Remedy Action:** {diagnosis.get('remedy_action', 'Error')}")
        
        st.divider()
        st.subheader("⚙️ Execute Self-Healing Protocol")
        
        # The Bulletproof Button pointing to your Master Reset Callback
        st.button("Authorize & Execute Fix", type="primary", on_click=apply_automated_fix)

# --- 6. Kick off the App ---
# We just call the fragment function once, and Streamlit handles the looping!
live_dashboard()