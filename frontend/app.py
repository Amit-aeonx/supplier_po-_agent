import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agent import POAgent
from backend.tools import POTools

# Initialize tools
tools = POTools()

# Page config
st.set_page_config(
    page_title="SupplierX PO Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium UI and Scroll Control
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* Global Styles */
    .stApp {
        background-color: #f0f2f6; /* Light gray background */
        font-family: 'Inter', sans-serif;
        color: #212529; /* Dark text for contrast */
    }

    /* Chat Container Styling */
    .stChatMessage {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* User Message Styling */
    .stChatMessage[data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, #0062cc 0%, #0096ff 100%); /* Blue gradient */
        color: white;
        border: none;
    }
    
    /* Fix text color inside user message */
    .stChatMessage[data-testid="stChatMessageUser"] p {
        color: white !important;
    }

    /* Assistant Message Styling */
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
    }

    /* Header Styling */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(90deg, #0052d4 0%, #4364f7 50%, #6fb1fc 100%);
        color: white;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 2.5rem;
        color: white !important;
    }
    
    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
        color: white !important;
    }

    /* Button Styling */
    .stButton button {
        background-color: #0062cc;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        background-color: #0056b3;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #dee2e6;
    }

    /* Scroll Fix: Disable smooth scrolling to prevent visible jumps */
    html, body {
        scroll-behavior: auto !important;
    }

    /* Target the main scrollable container */
    div[data-testid="stAppViewContainer"] {
        overflow-anchor: none;
        scroll-behavior: auto !important;
    }
    
    /* Fixed Chat Container */
    .chat-container {
        height: calc(100vh - 200px);
        overflow-y: auto;
        padding: 1rem;
        scroll-behavior: smooth;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <h1>🤖 SupplierX PO Agent v2.1</h1>
    <p>Intelligent Independent Purchase Order Creation</p>
</div>
""", unsafe_allow_html=True)

def get_next_step_options(step, response, last_user_input):
    """Helper to determine options and append prompt text based on current step"""
    options = None
    
    # 1. Supplier
    if step == "header_supplier":
        if "multiple matches" in response.lower():
             suppliers = tools.search_suppliers(last_user_input)
             options = [{"name": s["name"], "id": s["id"]} for s in suppliers]
             response += "\n\n**Select One:**"
        else:
             suppliers = tools.search_suppliers("")
             options = [{"name": s["name"], "id": s["id"]} for s in suppliers]
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
            options = [{"name": p["name"], "id": p["id"]} for p in plants]
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
            options = [{"name": m["name"], "id": m["id"]} for m in materials]
            response += "\n\n**Select Material:**"
        
    # 8. Add More / Confirm
    elif step == "add_more_check":
        options = [{"name": "Yes", "id": "y"}, {"name": "No", "id": "n"}]
        response += "\n\n**Select:**"
    elif step == "confirm":
        options = [{"name": "Yes, Create PO", "id": "yes"}, {"name": "Cancel", "id": "cancel"}]
        response += "\n\n**Confirm:**"
        
    return options, response

# Initialize agent in session state
if "agent" not in st.session_state:
    st.session_state.agent = POAgent()
    st.session_state.messages = []
    st.session_state.pending_options = None
    
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

# Display chat history in a fixed container
with st.container(height=600, border=False):
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Show clickable buttons or selectbox after agent messages
            if message["role"] == "assistant" and message.get("options"):
                options = message["options"]
                
                # If many options, use selectbox
                if len(options) > 10:
                    st.write("**Select from list:**")
                    selected_name = st.selectbox(
                        "Choose option:",
                        options=[opt["name"] for opt in options],
                        key=f"select_{i}",
                        label_visibility="collapsed"
                    )
                    
                    if st.button("Confirm Selection", key=f"confirm_{i}"):
                        st.session_state.messages.append({
                            "role": "user",
                            "content": selected_name
                        })
                        response = st.session_state.agent.process_message(selected_name)
                        
                        # Get options for next step
                        next_step = st.session_state.agent.state["step"]
                        next_options, response = get_next_step_options(next_step, response, selected_name)
                        
                        msg = {
                            "role": "assistant",
                            "content": response
                        }
                        if next_options:
                            msg["options"] = next_options
                            
                        st.session_state.messages.append(msg)
                        st.rerun()
                
                else:
                    # Few options, use buttons
                    st.write("**Click to select:**")
                    cols = st.columns(2)
                    for idx, option in enumerate(options):
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
                                
                                # Get options for next step
                                next_step = st.session_state.agent.state["step"]
                                next_options, response = get_next_step_options(next_step, response, user_msg)
                                
                                msg = {
                                    "role": "assistant",
                                    "content": response
                                }
                                if next_options:
                                    msg["options"] = next_options
                                
                                st.session_state.messages.append(msg)
                                
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
    
    # Use helper to get options
    options, response = get_next_step_options(step, response, last_user_input)
    
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

