"""
Streamlit App for LangChain PO Agent
Run with: streamlit run langchain_app.py
"""
import streamlit as st
from langchain_agent.agent import LangChainPOAgent

# Page config
st.set_page_config(
    page_title="PO Agent (LangChain)",
    page_icon="🔗",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🔗 PO Agent (LangChain Version)</h1>
    <p>Powered by LangChain + AWS Bedrock + Claude</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🛠️ Settings")
    
    if st.button("🔄 Reset Conversation", use_container_width=True):
        st.session_state.messages = []
        if "agent" in st.session_state:
            st.session_state.agent.reset()
        st.rerun()
    
    st.divider()
    st.markdown("""
    ### 💡 Try These:
    - "Create a PO for MS Pipe"
    - "Show me all suppliers"
    - "What materials are available?"
    - "Create PO for 100 units of Steel"
    """)
    
    st.divider()
    st.markdown("""
    ### 📊 LangChain Stack:
    - **LLM**: ChatBedrock (Claude)
    - **Tools**: 7 custom tools
    - **Memory**: Conversation history
    - **SQL**: SQLDatabaseChain
    """)

# Initialize agent
if "agent" not in st.session_state:
    try:
        st.session_state.agent = LangChainPOAgent()
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Welcome message
if not st.session_state.messages:
    welcome = """👋 **Welcome to the LangChain PO Agent!**

I can help you:
- 📋 Create Independent Purchase Orders
- 🔍 Search for suppliers, plants, and materials
- 📊 Answer questions about your data

**Try:** "Create a PO for 50 units of MS Pipe from Noida Plant"
"""
    with st.chat_message("assistant"):
        st.markdown(welcome)

# Chat input
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.process_message(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
