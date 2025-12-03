from typing import Dict, List, Optional
import json
import datetime
from backend.tools import POTools
from backend.llm import get_llm

class POAgent:
    """Conversational agent for PO creation with Bedrock and Fallbacks"""
    
    def __init__(self):
        self.tools = POTools()
        self.llm = get_llm()
        self.state = {
            "step": "start",
            "extracted_data": {},
            "validation_status": {},
            "final_payload": {}
        }
    
    def process_message(self, user_input: str) -> str:
        """Process user message through the 7-step flow"""
        
        step = self.state["step"]
        
        # STEP 1: User Input & Extraction (if starting)
        if step == "start":
            return self._step_extraction(user_input)
        
        # Handle validation questions
        elif step == "validating_supplier":
            return self._handle_supplier_selection(user_input)
            
        elif step == "validating_plant":
            return self._handle_plant_selection(user_input)
            
        elif step == "validating_material":
            return self._handle_material_selection(user_input)
            
        elif step == "validating_date":
             return self._handle_date_correction(user_input)
             
        elif step == "confirmation":
            return self._handle_confirmation(user_input)
            
        else:
            return "I'm lost. Let's start over. Tell me what you want to order."

    def _step_extraction(self, user_input: str) -> str:
        """Step 2: LLM Extraction"""
        prompt = f"""
        Extract the following fields from the user's request into a JSON object:
        - supplier_name (string or null)
        - plant_name (string or null)
        - material_name (string or null)
        - quantity (number or null)
        - price (number or null)
        - delivery_date (YYYY-MM-DD or null)
        
        User Request: "{user_input}"
        
        Return ONLY the JSON.
        """
        
        try:
            response = self.llm.invoke(prompt)
            # Clean up response to get just JSON
            json_str = response.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "{" not in json_str:
                return "I couldn't understand that. Please try again."
                
            data = json.loads(json_str)
            self.state["extracted_data"] = data
            print(f"[DEBUG] Extracted: {data}")
            
            # Move to validation
            return self._step_validation()
            
        except Exception as e:
            print(f"[ERROR] Extraction failed: {e}")
            return "Sorry, I had trouble understanding that. Could you rephrase?"

    def _step_validation(self) -> str:
        """Step 3: Validation Block"""
        data = self.state["extracted_data"]
        
        # 3.1 Supplier Validation
        if not self.state.get("supplier_valid"):
            if not data.get("supplier_name"):
                return "I need a supplier name. Who is this order for?"
            
            suppliers = self.tools.search_suppliers(data["supplier_name"])
            
            if len(suppliers) == 0:
                return f"I couldn't find a supplier named '{data['supplier_name']}'. Please check the name."
            elif len(suppliers) == 1:
                self.state["final_payload"]["supplier_id"] = suppliers[0]["id"]
                self.state["final_payload"]["supplier_name"] = suppliers[0]["name"]
                self.state["supplier_valid"] = True
            else:
                self.state["step"] = "validating_supplier"
                self.state["supplier_options"] = suppliers
                options = "\n".join([f"{i+1}. {s['name']}" for i, s in enumerate(suppliers)])
                return f"I found multiple suppliers. Please choose one:\n{options}"

        # 3.2 Plant Validation
        if not self.state.get("plant_valid"):
            if not data.get("plant_name"):
                # Default or ask? Let's ask.
                return "Which plant is this for?"
                
            plants = self.tools.search_plants(data["plant_name"])
            
            if len(plants) == 0:
                return f"I couldn't find a plant named '{data['plant_name']}'."
            elif len(plants) == 1:
                self.state["final_payload"]["plant_id"] = plants[0]["id"]
                self.state["final_payload"]["plant_name"] = plants[0]["name"]
                self.state["plant_valid"] = True
            else:
                self.state["step"] = "validating_plant"
                self.state["plant_options"] = plants
                options = "\n".join([f"{i+1}. {p['name']}" for i, p in enumerate(plants)])
                return f"I found multiple plants. Please choose one:\n{options}"

        # 3.3 Material Validation
        if not self.state.get("material_valid"):
            if not data.get("material_name"):
                return "What material do you want to order?"
                
            materials = self.tools.search_materials(data["material_name"])
            
            if len(materials) == 0:
                return f"I couldn't find material '{data['material_name']}'."
            elif len(materials) == 1:
                self.state["final_payload"]["material_name"] = materials[0]["name"]
                self.state["material_valid"] = True
            else:
                self.state["step"] = "validating_material"
                self.state["material_options"] = materials
                options = "\n".join([f"{i+1}. {m['name']}" for i, m in enumerate(materials)])
                return f"I found multiple materials. Please choose one:\n{options}"

        # 3.5 Delivery Date Validation
        if not self.state.get("date_valid"):
            date_str = data.get("delivery_date")
            if not date_str:
                # Default to 7 days from now
                date_str = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
            
            try:
                # Validate format
                d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                # Business Rule: Date cannot be in past
                if d < datetime.datetime.now():
                    self.state["step"] = "validating_date"
                    return "Delivery date cannot be in the past. Please enter a future date (YYYY-MM-DD)."
                
                self.state["final_payload"]["delivery_date"] = date_str
                self.state["date_valid"] = True
            except ValueError:
                self.state["step"] = "validating_date"
                return "Invalid date format. Please use YYYY-MM-DD."

        # Price fallback
        if not data.get("price"):
            self.state["final_payload"]["price"] = 100.0 # Mock default
        else:
             self.state["final_payload"]["price"] = data["price"]

        # Quantity fallback
        if not data.get("quantity"):
             self.state["final_payload"]["quantity"] = 10 # Mock default
        else:
             self.state["final_payload"]["quantity"] = data["quantity"]

        # Calculate Total
        self.state["final_payload"]["total"] = float(self.state["final_payload"]["quantity"]) * float(self.state["final_payload"]["price"])

        # All valid, move to confirmation
        self.state["step"] = "confirmation"
        return self._build_confirmation_msg()

    def _handle_supplier_selection(self, user_input: str) -> str:
        if user_input.isdigit():
            idx = int(user_input) - 1
            options = self.state["supplier_options"]
            if 0 <= idx < len(options):
                self.state["final_payload"]["supplier_id"] = options[idx]["id"]
                self.state["final_payload"]["supplier_name"] = options[idx]["name"]
                self.state["supplier_valid"] = True
                self.state["step"] = "start" # Return to main loop to continue validation
                return self._step_validation()
        return "Invalid selection. Please choose a number."

    def _handle_plant_selection(self, user_input: str) -> str:
        if user_input.isdigit():
            idx = int(user_input) - 1
            options = self.state["plant_options"]
            if 0 <= idx < len(options):
                self.state["final_payload"]["plant_id"] = options[idx]["id"]
                self.state["final_payload"]["plant_name"] = options[idx]["name"]
                self.state["plant_valid"] = True
                self.state["step"] = "start"
                return self._step_validation()
        return "Invalid selection. Please choose a number."

    def _handle_material_selection(self, user_input: str) -> str:
        if user_input.isdigit():
            idx = int(user_input) - 1
            options = self.state["material_options"]
            if 0 <= idx < len(options):
                self.state["final_payload"]["material_name"] = options[idx]["name"]
                self.state["material_valid"] = True
                self.state["step"] = "start"
                return self._step_validation()
        return "Invalid selection. Please choose a number."

    def _handle_date_correction(self, user_input: str) -> str:
        self.state["extracted_data"]["delivery_date"] = user_input.strip()
        self.state["step"] = "start"
        return self._step_validation()

    def _build_confirmation_msg(self) -> str:
        p = self.state["final_payload"]
        return f"""
        All set! Here is the PO details:
        
        Supplier: {p['supplier_name']}
        Plant: {p['plant_name']}
        Material: {p['material_name']}
        Quantity: {p['quantity']}
        Price: {p['price']}
        Total: {p['total']}
        Delivery: {p['delivery_date']}
        
        Type 'yes' to create this PO.
        """

    def _handle_confirmation(self, user_input: str) -> str:
        if user_input.lower() in ['yes', 'y', 'confirm']:
            po_number = self.tools.create_po(self.state["final_payload"])
            
            # Reset
            self.state = {
                "step": "start",
                "extracted_data": {},
                "validation_status": {},
                "final_payload": {}
            }
            
            return f"🎉 PO Created Successfully! PO Number: {po_number}"
        else:
            return "Cancelled. Type a new request to start over."
