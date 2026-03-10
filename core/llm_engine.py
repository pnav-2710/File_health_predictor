import os
from typing import TypedDict
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

# --- 1. Define the State ---
# This dictionary acts as the "memory" passed between our agents.
class SystemState(TypedDict):
    telemetry: dict
    fhs_score: float
    reasoning: str
    root_cause: str
    remedy_action: str

# --- 2. Define Structured Outputs (Pydantic) ---
# This forces Gemini to respond in perfect JSON that matches our exact needs.
class DiagnosisOutput(BaseModel):
    reasoning: str = Field(description="Step-by-step SRE reasoning analyzing the metrics.")
    root_cause: str = Field(description="The underlying issue. E.g., 'Hardware Degradation', 'Network Partition', or 'Silent Data Corruption'.")

class RemediationOutput(BaseModel):
    remedy_action: str = Field(description="The exact fix. MUST be one of: MIGRATE_NODE, REBUILD_REPLICA, RESTORE_FROM_SNAPSHOT, IGNORE.")

# --- 3. Define the Agents (Nodes) ---

def diagnostician_agent(state: SystemState):
    """Agent 1: Analyzes raw metrics to determine the root cause."""
    print("🤖 [Agent 1] Diagnostician is analyzing telemetry...")
    
    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
    structured_llm = llm.with_structured_output(DiagnosisOutput)
    
    prompt = f"""
    You are an expert Storage Site Reliability Engineer. 
    A critical alert was triggered. The File Health Score (FHS) dropped to {state['fhs_score']}.
    
    Analyze the following real-time telemetry:
    {state['telemetry']}
    
    Determine the root cause. Look for heat/latency spikes, missing replicas, or checksum mismatches.
    """
    
    response = structured_llm.invoke(prompt)
    
    # Update the state with the findings
    return {"reasoning": response.reasoning, "root_cause": response.root_cause}

def remediator_agent(state: SystemState):
    """Agent 2: Takes the diagnosis and selects the automated fix."""
    print(f"🤖 [Agent 2] Remediator is selecting fix for: {state['root_cause']}...")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0) # Dropped temp to 0.0 for maximum strictness
    structured_llm = llm.with_structured_output(RemediationOutput)
    
    # --- UPDATED STRICT PROMPT ---
    prompt = f"""
    You are an automated Remediation Executor for a cloud storage system.
    The Diagnostician has identified the following root cause: "{state['root_cause']}"
    The reasoning is: "{state['reasoning']}"
    
    Select the single best automated action to fix this storage system. 
    
    CRITICAL SRE RULEBOOK - You MUST map the root cause to the correct action:
    - If the root cause involves "Hardware Degradation", "Temperature", or "SMART Errors" -> action MUST be "MIGRATE_NODE"
    - If the root cause involves "Network Partition", "Dropped Node", or "Missing Replica" -> action MUST be "REBUILD_REPLICA"
    - If the root cause involves "Silent Data Corruption" or "Checksum Mismatch" -> action MUST be "RESTORE_FROM_SNAPSHOT"
    """
    
    response = structured_llm.invoke(prompt)
    
    # Update the state with the final action
    return {"remedy_action": response.remedy_action}
# --- 4. Build and Compile the LangGraph ---

# Initialize the graph
workflow = StateGraph(SystemState)

# Add our agents as nodes
workflow.add_node("diagnostician", diagnostician_agent)
workflow.add_node("remediator", remediator_agent)

# Define the flow (Edges)
workflow.add_edge(START, "diagnostician")
workflow.add_edge("diagnostician", "remediator")
workflow.add_edge("remediator", END)

# Compile the graph into an executable application
aiops_graph = workflow.compile()

# --- 5. Main Execution Function ---

def run_aiops_diagnosis(telemetry_data: dict, current_fhs: float):
    """
    The main function called by app.py when a threshold is breached.
    """
    # Requires GEMINI_API_KEY environment variable to be set
    if "GEMINI_API_KEY" not in os.environ:
        return {"error": "GEMINI_API_KEY not found in environment variables."}

    initial_state = {
        "telemetry": telemetry_data,
        "fhs_score": current_fhs,
        "reasoning": "",
        "root_cause": "",
        "remedy_action": ""
    }
    
    # Run the graph
    print("\n🚀 Initiating AIOps Agentic Workflow...")
    final_state = aiops_graph.invoke(initial_state)
    
    # Return the final diagnostic payload
    return {
        "fhs_score": final_state["fhs_score"],
        "root_cause": final_state["root_cause"],
        "reasoning": final_state["reasoning"],
        "remedy_action": final_state["remedy_action"]
    }