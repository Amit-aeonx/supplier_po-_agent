import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agent import POAgent
from backend.tools import POTools

# Page config
st.set_page_config(page_title="PO Creation Agent", page_icon="📦", layout="wide")

# Initialize tools
tools = POTools()

# JavaScript to auto-scroll to bottom
# JS removed as per user request

st.title("🤖 SupplierX PO Creation Bot")
st.caption("Create Purchase Orders through conversation")

# Initialize agent in session state
if "agent" not in st.session_state:
    st.session_state.agent = POAgent()
    st.session_state.messages = []
    st.session_state.pending_options = None  # Store options to show as buttons
    
    # Add welcome message
    welcome_msg = "👋 Hi! I'll help you create an **Independent Purchase Order**.\n\nWe'll go through:\n1. Header (Supplier, Type, Currency)\n2. Org Data (Plant, Purch Org, Group)\n3. Line Items\n\nType 'start' or just say 'Create PO' to begin!"
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
        welcome_msg = "👋 Hi! I'll help you create an **Independent Purchase Order**.\n\nWe'll go through:\n1. Header (Supplier, Type, Currency)\n2. Org Data (Plant, Purch Org, Group)\n3. Line Items\n\nType 'start' or just say 'Create PO' to begin!"
        st.session_state.messages.append({
            "role": "assistant",
            "content": welcome_msg
        })
        st.rerun()
    
    st.divider()
    st.header("📊 Current State")
    state = st.session_state.agent.state
    
    # Flatten for display
    display_state = {
        "Step": state.get("step"),
        "Header": state.get("header"),
        "Org Data": state.get("org_data"),
        "Items": len(state.get("line_items", []))
    }
    st.json(display_state)

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
    
    # Check state to show relevant buttons
    options = None
    last_user_input = st.session_state.messages[-2]["content"] if len(st.session_state.messages) > 1 else ""
    step = st.session_state.agent.state["step"]
    
    # 1. Supplier
    if step == "header_supplier":
        if "multiple matches" in response.lower():
             suppliers = tools.search_suppliers(last_user_input)
             options = [{"name": s["name"], "id": s["id"]} for s in suppliers]
             response += "\n\n**Select One:**"
        else:
             suppliers = tools.search_suppliers("")
             options = [{"name": s["name"], "id": s["id"]} for s in suppliers[:5]]
             response += "\n\n**Select Supplier:**"

    # 2. PO Type
    elif step == "header_type":
        options = [
            {"name": "Asset", "id": "asset"},
            {"name": "Service", "id": "service"},
            {"name": "Regular Purchase", "id": "regular"},
            {"name": "Internal Order Material", "id": "internal_material"},
            {"name": "Internal Order Service", "id": "internal_service"},
            {"name": "Network", "id": "network"},
            {"name": "Network Service", "id": "network_service"},
            {"name": "Cost Center Material", "id": "cost_center"}
        ]
        response += "\n\n**Select Type:**"
        
    # 3. Currency
    elif step == "header_currency":
        currencies = tools.get_currencies()
        options = [{"name": c["code"], "id": c["id"]} for c in currencies]
        if not options:
             options = [{"name": "INR", "id": "inr"}, {"name": "USD", "id": "usd"}, {"name": "EUR", "id": "eur"}]
        response += "\n\n**Select Currency:**"
        
    # 4. Plant
    elif step == "org_plant":
        if "multiple matches" in response.lower():
            plants = tools.search_plants(last_user_input)
            options = [{"name": p["name"], "id": p["id"]} for p in plants]
            response += "\n\n**Select One:**"
        else:
            plants = tools.search_plants("")
            options = [{"name": p["name"], "id": p["id"]} for p in plants[:5]]
            response += "\n\n**Select Plant:**"
        
    # 5. Purchase Org
    elif step == "org_purch_org":
        if "multiple matches" in response.lower():
            orgs = tools.search_purchase_orgs(last_user_input)
            options = [{"name": o["name"], "id": o["id"]} for o in orgs]
            response += "\n\n**Select One:**"
        else:
            orgs = tools.search_purchase_orgs("")
            options = [{"name": o["name"], "id": o["id"]} for o in orgs]
            response += "\n\n**Select Purchase Org:**"
        
    # 6. Purchase Group
    elif step == "org_purch_group":
        if "multiple matches" in response.lower():
            groups = tools.search_purchase_groups(last_user_input)
            options = [{"name": g["name"], "id": g["id"]} for g in groups]
            response += "\n\n**Select One:**"
        else:
            groups = tools.search_purchase_groups("")
            options = [{"name": g["name"], "id": g["id"]} for g in groups]
            response += "\n\n**Select Purchase Group:**"
        
    # 7. Material
    elif step == "item_material":
        if "multiple matches" in response.lower():
            materials = tools.search_materials(last_user_input)
            options = [{"name": m["name"], "id": m["id"]} for m in materials]
            response += "\n\n**Select One:**"
        else:
            materials = tools.search_materials("")
            options = [{"name": m["name"], "id": m["id"]} for m in materials[:5]]
            response += "\n\n**Select Material:**"
        
    # 8. Add More / Confirm
    elif step == "add_more_check":
        options = [{"name": "Yes", "id": "y"}, {"name": "No", "id": "n"}]
        response += "\n\n**Select:**"
    elif step == "confirm":
        options = [{"name": "Yes, Create PO", "id": "yes"}, {"name": "Cancel", "id": "cancel"}]
        response += "\n\n**Confirm:**"
    
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

