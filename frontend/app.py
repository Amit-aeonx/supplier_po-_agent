import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agent import POAgent
from backend.tools import POTools

# Page config
st.set_page_config(
    page_title="SupplierX PO Bot",
    page_icon="🤖",
    layout="centered"
)

# Initialize tools
tools = POTools()

# Title
st.title("🤖 SupplierX PO Creation Bot")
st.caption("Create Purchase Orders through conversation")

# Initialize agent in session state
if "agent" not in st.session_state:
    st.session_state.agent = POAgent()
    st.session_state.messages = []
    st.session_state.pending_options = None  # Store options to show as buttons
    
    # Add welcome message
    welcome_msg = "👋 Hi! I'll help you create a Purchase Order.\n\nTell me what you need, for example:\n- 'Create a PO for 120 MS Pipe for Jindal supplier to Noida plant on 2025-12-15'\n- 'Order 50 Steel Rods from ABC Supplier'"
    st.session_state.messages.append({
        "role": "assistant",
        "content": welcome_msg
    })

# Sidebar with minimal info
with st.sidebar:
    st.header("ℹ️ About")
    st.write("This chatbot helps you create Purchase Orders in SupplierX.")
    
    st.header("🔄 Actions")
    if st.button("🔄 Restart Conversation", use_container_width=True):
        st.session_state.agent = POAgent()
        st.session_state.messages = []
        st.session_state.pending_options = None
        welcome_msg = "👋 Hi! I'll help you create a Purchase Order.\n\nTell me what you need, for example:\n- 'Create a PO for 120 MS Pipe for Jindal supplier to Noida plant on 2025-12-15'\n- 'Order 50 Steel Rods from ABC Supplier'"
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg
        })
        st.rerun()
    
    st.divider()
    st.header("📊 Current State")
    state = st.session_state.agent.state
    st.json({
        "Step": state.get("step"),
        "Validated": {
            "Supplier": state.get("supplier_valid", False),
            "Plant": state.get("plant_valid", False),
            "Material": state.get("material_valid", False),
            "Date": state.get("date_valid", False)
        }
    })

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show clickable buttons after agent messages
        if message["role"] == "assistant" and message.get("options"):
            st.write("**Click to select:**")
            cols = st.columns(2)
            for idx, option in enumerate(message["options"]):
                col = cols[idx % 2]
                with col:
                    if st.button(
                        option["name"], 
                        key=f"opt_{i}_{idx}",
                        use_container_width=True
                    ):
                        # User clicked an option
                        user_msg = option["name"]
                        st.session_state.messages.append({
                            "role": "user",
                            "content": user_msg
                        })
                        
                        # Process the selection
                        response = st.session_state.agent.process_message(user_msg)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response
                        })
                        
                        st.rerun()

# Chat input at bottom
if prompt := st.chat_input("Type your message..."):
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Get bot response
    response = st.session_state.agent.process_message(prompt)
    
    # Check if agent is asking for supplier/plant/material
    options = None
    if "I need a supplier name" in response or "supplier?" in response.lower():
        # Fetch suppliers and add as options
        suppliers = tools.get_suppliers(10)
        options = [{"name": s["name"], "id": s["id"]} for s in suppliers]
        response += "\n\n**Or choose from these suppliers:**"
    elif "Which plant" in response or "plant?" in response.lower():
        plants = tools.search_plants("")
        options = [{"name": p["name"], "id": p["id"]} for p in plants[:10]]
        response += "\n\n**Or choose from these plants:**"
    elif "What material" in response or "material?" in response.lower():
        materials = tools.search_materials("")
        options = [{"name": m["name"], "id": m["id"]} for m in materials[:10]]
        response += "\n\n**Or choose from these materials:**"
    
    # Add bot response to history
    msg = {
        "role": "assistant",
        "content": response
    }
    if options:
        msg["options"] = options
    
    st.session_state.messages.append(msg)
    
    # Rerun to update chat
    st.rerun()

