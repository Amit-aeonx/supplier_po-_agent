import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from backend.llm import get_llm
from backend.tools import POTools

from backend.sql_agent import SQLAgent

class POAgent:
    def __init__(self):
        self.llm = get_llm()
        self.tools = POTools()
        self.sql_agent = SQLAgent()
        self.state = {
            "step": "start",
            "po_mode": "independent", # Default to independent
            "header": {
                "po_date": datetime.now().strftime("%Y-%m-%d"),
                "validity_date": None,
                "po_type": None,
                "supplier": None,
                "currency": None
            },
            "org_data": {
                "plant": None,
                "purchase_org": None,
                "purchase_group": None
            },
            "line_items": [],
            "current_item": {},
            "history": []
        }

    def extract_entities(self, user_input: str) -> Dict:
        """Extract PO entities from natural language using Bedrock"""
        prompt = f"""
        Extract Purchase Order entities from the user input.
        Return JSON ONLY. No markdown.
        
        Fields to extract (if present):
        - intent: "create_po" or "question"
        - supplier: name of supplier
        - plant: name of plant
        - material: name of material
        - quantity: number
        - po_type: "Standard", "Service", etc.
        
        User Input: "{user_input}"
        
        Example JSON:
        {{
            "intent": "create_po",
            "supplier": "Avians",
            "plant": "Noida",
            "material": "MS Pipe",
            "quantity": "50"
        }}
        """
        
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = self.sql_agent.bedrock.invoke_model(
                modelId=self.sql_agent.model_id,
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            text_resp = response_body['content'][0]['text'].strip()
            # Cleanup json
            text_resp = text_resp.replace("```json", "").replace("```", "").strip()
            return json.loads(text_resp)
        except Exception as e:
            print(f"[ERROR] extract_entities: {e}")
            return {}

    def process_message(self, user_input: str) -> str:
        """Process user message and return bot response"""
        
        # Global Question Detection (Escape Hatch)
        # If the user asks a question, answer it and repeat the current step's prompt
        question_indicators = ["how", "what", "show", "list", "give", "count", "tell", "where"]
        is_question = any(user_input.lower().startswith(w) for w in question_indicators) or "?" in user_input
        
        if is_question and self.state["step"] != "start":
            answer = self.sql_agent.answer_question(user_input)
            if "couldn't generate" not in answer:
                # Return answer + reminder of current step
                current_prompt = self._get_current_step_prompt()
                return f"{answer}\n\n---\n(Resuming...)\n{current_prompt}"

        step = self.state["step"]
        
        # --- STEP 1: START & HEADER ---
        if step == "start":
            # 1. Extract Entities
            entities = self.extract_entities(user_input)
            print(f"[DEBUG] Extracted: {entities}")
            
            if entities.get("intent") == "question":
                 return self.sql_agent.answer_question(user_input)
            
            if entities.get("intent") == "create_po" or any(w in user_input.lower() for w in ["create", "start", "po"]):
                self.state["step"] = "header_supplier"
                self.state["extracted"] = entities # Store for later steps
                
                # Auto-fill Supplier if found
                if entities.get("supplier"):
                    suppliers = self.tools.search_suppliers(entities["supplier"])
                    if len(suppliers) == 1:
                        self.state["header"]["supplier"] = suppliers[0]
                        self.state["step"] = "header_type" # Skip to next
                        
                # Auto-fill PO Type if found
                if entities.get("po_type"):
                     # Simple validation could be added here
                     self.state["header"]["po_type"] = entities["po_type"]
                     if self.state["step"] == "header_type":
                         self.state["step"] = "header_currency"

                # If we skipped supplier, return next prompt
                if self.state["step"] == "header_type":
                    return f"Supplier **{self.state['header']['supplier']['name']}** selected.\n\nSelect **PO Type**:"
                elif self.state["step"] == "header_currency":
                     return f"Supplier **{self.state['header']['supplier']['name']}** and Type **{self.state['header']['po_type']}** selected.\n\nSelect **Currency**:"
                
                return "Let's create an Independent PO.\n\nFirst, **which Supplier** is this for? (Type name to search)"
            else:
                # Fallback to Q&A
                return self.sql_agent.answer_question(user_input)
            
        elif step == "header_supplier":
            return self._handle_selection(
                user_input, 
                self.tools.search_suppliers, 
                "header", "supplier", 
                "header_type", 
                "Selected: **{name}**\n\nSelect **PO Type**:"
            )

        elif step == "header_type":
            # Accept all 8 PO types from SupplierX
            valid_types = ["Asset", "Service", "Regular Purchase", "Internal Order Material", 
                          "Internal Order Service", "Network", "Network Service", "Cost Center Material"]
            
            po_type = user_input.title()
            if po_type not in valid_types:
                return f"Please choose one of: {', '.join(valid_types)}"
            
            self.state["header"]["po_type"] = po_type
            self.state["step"] = "header_currency"
            return "What **Currency** should be used? (e.g., INR, USD)"

        elif step == "header_currency":
            self.state["header"]["currency"] = user_input.upper()
            self.state["header"]["validity_date"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            self.state["step"] = "org_plant"
            return f"Currency set to **{user_input.upper()}**.\n\nNow, which **Plant** is this for?"

        # --- STEP 2: ORG DATA ---
        elif step == "org_plant":
            return self._handle_selection(
                user_input,
                self.tools.search_plants,
                "org_data", "plant",
                "org_purch_org",
                "Selected Plant: **{name}**\n\nSelect **Purchase Organization**:"
            )

        elif step == "org_purch_org":
            return self._handle_selection(
                user_input,
                self.tools.search_purchase_orgs,
                "org_data", "purchase_org",
                "org_purch_group",
                "Selected Org: **{name}**\n\nSelect **Purchase Group**:"
            )

        elif step == "org_purch_group":
            return self._handle_selection(
                user_input,
                self.tools.search_purchase_groups,
                "org_data", "purchase_group",
                "optional_fields",
                "Org Data saved.\n\nDo you want to add **optional fields** (Projects, Payment Terms, Inco Terms)? Type 'yes' or 'skip'."
            )

        # --- STEP 2.5: OPTIONAL FIELDS ---
        elif step == "optional_fields":
            if "skip" in user_input.lower():
                self.state["step"] = "item_material"
                return "--- Line Item 1 ---\n\nWhat **Material/Service** do you want to add?"
            elif "yes" in user_input.lower():
                self.state["step"] = "optional_project"
                return "Enter **Project Name** (or type 'skip'):"
            else:
                return "Please type 'yes' to add optional fields or 'skip' to continue."

        elif step == "optional_project":
            if "skip" not in user_input.lower():
                self.state["optional"] = {"project": user_input}
            self.state["step"] = "optional_payment"
            return "Enter **Payment Term** (or type 'skip'):"

        elif step == "optional_payment":
            if "skip" not in user_input.lower():
                if "optional" not in self.state:
                    self.state["optional"] = {}
                self.state["optional"]["payment_term"] = user_input
            self.state["step"] = "optional_inco"
            return "Enter **Inco Term** (or type 'skip'):"

        elif step == "optional_inco":
            if "skip" not in user_input.lower():
                if "optional" not in self.state:
                    self.state["optional"] = {}
                self.state["optional"]["inco_term"] = user_input
            self.state["step"] = "item_material"
            return "--- Line Item 1 ---\n\nWhat **Material/Service** do you want to add?"

        # --- STEP 3: LINE ITEMS ---
        elif step == "item_material":
            # Check if we have pre-filled details from start
            if "initial_details" in self.state and not user_input:
                user_input = self.state.pop("initial_details") # Use and remove
            
            # Custom handling for material to store in current_item
            materials = self.tools.search_materials(user_input)
            if not materials:
                return f"I couldn't find any material matching '{user_input}'. Try 'MS Pipe' or 'Steel'."
            
            # Try exact match first (case-insensitive)
            selected = next((m for m in materials if m['name'].lower() == user_input.lower()), None)
            
            # If no exact match, check partial matches
            if not selected:
                partial_matches = [m for m in materials if user_input.lower() in m['name'].lower()]
                if len(partial_matches) == 1:
                    selected = partial_matches[0]
            
            # If still no match but only 1 result total, auto-select
            if not selected and len(materials) == 1:
                selected = materials[0]
            
            if selected:
                self.state["current_item"]["material"] = selected
                self.state["step"] = "item_qty"
                return f"Selected: **{selected['name']}**\n\nEnter **Quantity**:"
            else:
                # Multiple matches - frontend will show buttons
                return f"I found multiple matches for '{user_input}'. Please select one."

        elif step == "item_qty":
            try:
                qty = float(user_input)
                self.state["current_item"]["quantity"] = qty
                self.state["step"] = "item_price"
                return "Enter **Unit Price**:"
            except:
                return "Please enter a valid number."

        elif step == "item_price":
            try:
                price = float(user_input)
                item = self.state["current_item"]
                item["price"] = price
                item["total"] = item["quantity"] * price
                
                # Add to list
                self.state["line_items"].append(item)
                self.state["current_item"] = {} # Reset
                
                self.state["step"] = "add_more_check"
                return f"Item added! Total: {item['total']}\n\nDo you want to **add another item**? (yes/no)"
            except:
                return "Please enter a valid price."

        elif step == "add_more_check":
            if "yes" in user_input.lower():
                self.state["step"] = "item_material"
                return f"--- Line Item {len(self.state['line_items']) + 1} ---\n\nWhat **Material**?"
            else:
                self.state["step"] = "remarks"
                return "Any **Remarks** for this PO? (or type 'skip')"

        # --- STEP 3.5: REMARKS ---
        elif step == "remarks":
            if "skip" not in user_input.lower():
                self.state["remarks"] = user_input
            self.state["step"] = "confirm"
            return self._generate_summary()

        # --- STEP 4: CONFIRM ---
        elif step == "confirm":
            if "yes" in user_input.lower() or "create" in user_input.lower():
                # Save to DB
                optional = self.state.get("optional", {})
                po_data = {
                    "po_date": self.state["header"]["po_date"],
                    "validity_date": self.state["header"]["validity_date"],
                    "po_type": self.state["header"]["po_type"],
                    "supplier_id": self.state["header"]["supplier"]["id"],
                    "supplier_name": self.state["header"]["supplier"]["name"],
                    "currency": self.state["header"]["currency"],
                    "purchase_org_id": self.state["org_data"]["purchase_org"]["id"],
                    "purchase_org_code": self.state["org_data"]["purchase_org"].get("code"),
                    "plant_id": self.state["org_data"]["plant"]["id"],
                    "plant_code": self.state["org_data"]["plant"].get("code", "P01"),
                    "purchase_group_id": self.state["org_data"]["purchase_group"]["id"],
                    "purchase_group_code": self.state["org_data"]["purchase_group"].get("code"),
                    "project_name": optional.get("project"),
                    "payment_term_code": optional.get("payment_term"),
                    "inco_term_code": optional.get("inco_term"),
                    "remarks": self.state.get("remarks"),
                    "line_items": self.state["line_items"],
                    "total_amount": sum(i["total"] for i in self.state["line_items"])
                }
                
                po_number = self.tools.create_independent_po(po_data)
                
                self.state["step"] = "start" # Reset
                return f"🎉 **Independent PO Created!**\nPO Number: `{po_number}`\n\nType 'start' to create another."
            else:
                return "Cancelled. Type 'start' to start over."

        return "I didn't understand. Please try again."

    def _handle_selection(self, user_input, search_func, state_category, state_key, next_step, success_msg):
        """Helper to handle search-and-select logic"""
        results = search_func(user_input)
        
        if not results:
            return f"I couldn't find any match for '{user_input}'. Please try again."
        
        # Try exact match first (case-insensitive)
        selected = next((r for r in results if r['name'].lower() == user_input.lower()), None)
        
        # If no exact match, check partial matches
        if not selected:
            partial_matches = [r for r in results if user_input.lower() in r['name'].lower()]
            if len(partial_matches) == 1:
                selected = partial_matches[0]
        
        # If still no match but only 1 result total, auto-select
        if not selected and len(results) == 1:
            selected = results[0]
            
        if selected:
            self.state[state_category][state_key] = selected
            self.state["step"] = next_step
            return success_msg.format(name=selected['name'])
        else:
            # Multiple matches - frontend will show buttons
            return f"I found multiple matches for '{user_input}'. Please select one."

    def _generate_summary(self) -> str:
        h = self.state["header"]
        o = self.state["org_data"]
        items = self.state["line_items"]
        total = sum(i["total"] for i in items)
        
        summary = f"""**📋 Final PO Review**

**Header Details:**
- **Supplier:** {h['supplier']['name']}
- **Type:** {h['po_type']}
- **Currency:** {h['currency']}
- **PO Date:** {h['po_date']}
- **Validity:** {h['validity_date']}

**Organization Data:**
- **Plant:** {o['plant']['name']}
- **Purch Org:** {o['purchase_org']['name']} ({o['purchase_org'].get('code', 'N/A')})
- **Purch Group:** {o['purchase_group']['name']} ({o['purchase_group'].get('code', 'N/A')})

**Line Items:**
"""
        for idx, i in enumerate(items, 1):
            summary += f"{idx}. **{i['material']['name']}**\n   Qty: {i['quantity']} | Price: {i['price']} | Total: {i['total']}\n"
            
        summary += f"\n**💰 Grand Total: {total} {h['currency']}**\n\nEverything looks good? Type **'Yes'** to create PO."""
        return summary

    def _get_current_step_prompt(self) -> str:
        """Helper to get the prompt for the current step without processing input"""
        step = self.state["step"]
        
        if step == "header_supplier":
            return "First, **which Supplier** is this for? (Type name to search)"
        elif step == "header_type":
            return "Selected: **{name}**\n\nSelect **PO Type**:".format(name=self.state["header"]["supplier"]["name"])
        elif step == "header_currency":
            return "What **Currency** should be used? (e.g., INR, USD)"
        elif step == "org_plant":
            return f"Currency set to **{self.state['header']['currency']}**.\n\nNow, which **Plant** is this for?"
        elif step == "org_purch_org":
            return "Select **Purchase Organization**:"
        elif step == "org_purch_group":
            return "Select **Purchase Group**:"
        elif step == "optional_fields":
            return "Org Data saved.\n\nDo you want to add **optional fields** (Projects, Payment Terms, Inco Terms)? Type 'yes' or 'skip'."
        elif step == "optional_project":
            return "Enter **Project Name** (or type 'skip'):"
        elif step == "optional_payment":
            return "Enter **Payment Term** (or type 'skip'):"
        elif step == "optional_inco":
            return "Enter **Inco Term** (or type 'skip'):"
        elif step == "item_material":
            return f"--- Line Item {len(self.state['line_items']) + 1} ---\n\nWhat **Material/Service** do you want to add?"
        elif step == "item_qty":
            return f"Selected: **{self.state['current_item']['material']['name']}**\n\nEnter **Quantity**:"
        elif step == "item_price":
            return "Enter **Unit Price**:"
        elif step == "add_more_check":
            return f"Item added! Total: {self.state['current_item'].get('total', 0)}\n\nDo you want to **add another item**? (yes/no)"
        elif step == "remarks":
            return "Any **Remarks** for this PO? (or type 'skip')"
        elif step == "confirm":
            return self._generate_summary()
            
        return "How can I help you?"
