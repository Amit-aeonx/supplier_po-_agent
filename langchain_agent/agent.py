"""
LangChain Agent for PO Creation
Uses LangChain's Agent framework with custom tools
"""
import json
from typing import Dict, List, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

from langchain_agent.llm import get_llm_with_credentials
from langchain_agent.tools import ALL_TOOLS
from langchain_agent.sql_chain import get_sql_chain


class LangChainPOAgent:
    """LangChain-based PO Agent with conversation memory"""
    
    def __init__(self):
        self.llm = get_llm_with_credentials()
        self.tools = ALL_TOOLS
        self.chat_history: List = []
        self.sql_chain = get_sql_chain()
        
        # Create the agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful Purchase Order assistant for SupplierX.

Your job is to:
1. **Create new Purchase Orders** by collecting required information
2. **Retrieve existing PO details** when asked (use get_po_details tool)
3. **Answer data questions** about suppliers, materials, plants, etc.

**Available PO Types:**
- Asset, Service, Regular Purchase, Internal Order Material, Internal Order Service, Network, Network Service, Cost Center Material

**Required Information for Creating PO:**
- Supplier, PO Type, Currency, Plant, Purchase Organization, Purchase Group, Material/Service, Quantity, Unit Price

**To retrieve PO details:** Use the get_po_details tool with the PO number (e.g., IND-PO-97591)

Always be helpful and guide the user step by step."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        
        # Create the executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def _is_question(self, text: str) -> bool:
        """Check if the input is a data question"""
        question_words = ["how many", "what", "show", "list", "count", "tell me", "where", "which", "give me"]
        text_lower = text.lower()
        return any(text_lower.startswith(w) or text_lower.startswith(w) for w in question_words) or "?" in text
    
    def process_message(self, user_input: str) -> str:
        """Process a user message and return the response"""
        
        # Check if it's a data question
        if self._is_question(user_input):
            try:
                answer = self.sql_chain.run(user_input)
                self.chat_history.append(HumanMessage(content=user_input))
                self.chat_history.append(AIMessage(content=answer))
                return answer
            except Exception as e:
                print(f"[SQL Chain Error] {e}")
                # Fall through to agent
        
        try:
            # Run the agent
            result = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": self.chat_history
            })
            
            # Extract clean response
            raw_output = result.get("output", "I couldn't process that request.")
            
            # Clean up the response if it's a list/dict
            if isinstance(raw_output, list):
                # Extract text from list of dicts
                response = "\n".join([item.get("text", str(item)) for item in raw_output if isinstance(item, dict)])
            elif isinstance(raw_output, dict):
                response = raw_output.get("text", str(raw_output))
            else:
                response = str(raw_output)
            
            # Update chat history
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=response))
            
            return response
            
        except Exception as e:
            print(f"[Agent Error] {e}")
            return f"I encountered an error: {str(e)}"
    
    def reset(self):
        """Reset the conversation history"""
        self.chat_history = []
