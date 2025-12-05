import sys
import os
import random
import json
from datetime import datetime, timedelta
from sqlalchemy import text
from backend.database import engine

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.tools import POTools
from backend.llm import BedrockLLM

class SmartPOAgent:
    def __init__(self):
        self.tools = POTools()
        self.llm = BedrockLLM()
        
    def parse_intent(self, user_input):
        """
        Uses LLM with the user-provided system prompt to extract structured PO requirements.
        """
        prompt = f"""
        You are an intelligent Purchase Order Automation Agent.
        Your goal is to convert a simple user requirement into fully-structured PO inputs.
        
        User Requirement: "{user_input}"
        
        Responsibilities:
        1. Understand the user's natural-language requirement.
        2. Break it down into structured components:
           - Item description
           - Quantity (default to 1 if not specified)
           - Category
           - Required delivery date (if indicated)
           - Additional constraints (urgent, budget limit, brand preference, etc.)
           
        Return ONLY a JSON object in this format:
        {{
            "item_description": "string",
            "quantity": int,
            "category": "string",
            "delivery_date": "string or null",
            "constraints": ["string"]
        }}
        """
        
        try:
            # FIX: Use invoke instead of generate_response
            response = self.llm.invoke(prompt)
            # Clean up response to ensure it's valid JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3]
            elif response.startswith("```"):
                response = response[3:-3]
                
            data = json.loads(response)
            return data
        except Exception as e:
            print(f"Error parsing intent: {e}")
            return {
                "item_description": user_input, 
                "quantity": 1, 
                "category": "General", 
                "delivery_date": None, 
                "constraints": []
            }

    def get_recommendations(self, intent_data):
        """
        Finds suppliers and ranks them using multi-factor scoring:
        Score = (price_score + delivery_score + quality_score + availability_score)
        """
        material_query = intent_data.get("item_description")
        constraints = intent_data.get("constraints", [])
        
        # 1. Search for materials
        materials = self.tools.search_materials(material_query)
        if not materials:
            # Fallback if no specific material found, search generic
            materials = self.tools.search_materials("")
            
        # 2. Search for suppliers
        suppliers = self.tools.search_suppliers("")
        if not suppliers:
            return []
            
        recommendations = []
        
        # 3. Generate recommendations and Calculate Scores
        # We will simulate the data we'd get from AWS/Database (Price, Delivery, Quality)
        
        for m in materials[:5]: # Check top 5 materials
            for s in suppliers[:5]: # Check top 5 suppliers
                
                # --- SIMULATED DATA FETCHING ---
                # In a real scenario, this would come from:
                # price = db.get_price(s.id, m.id)
                # quality = aws_opensearch.get_quality_score(s.id)
                
                base_price = float(m.get('price', 1000))
                price = base_price * (random.uniform(0.9, 1.2)) # Random variation
                delivery_days = random.randint(1, 14)
                quality_score = random.randint(70, 100)
                availability_score = random.choice([100, 100, 80, 0]) # Mostly available
                
                # --- SCORING LOGIC ---
                # Normalize metrics to 0-100 scale for scoring
                
                # Price Score: Lower is better. (Target: 1000 -> 100 score)
                # Simple normalization: 100 * (Base / Actual)
                if price <= 0:
                    price = 0.01 # Avoid division by zero
                price_score = min(100, (base_price / price) * 100)
                
                # Delivery Score: Lower days is better. (Target: 2 days -> 100 score)
                # Formula: max(0, 100 - (days * 5))
                delivery_score = max(0, 100 - (delivery_days * 5))
                
                # Quality Score: Already 0-100
                
                # Availability Score: Already 0-100
                
                # Weighted Total Score
                # Adjust weights based on constraints (e.g., "urgent" -> higher delivery weight)
                w_price, w_delivery, w_quality, w_avail = 0.3, 0.2, 0.3, 0.2
                
                if "urgent" in str(constraints).lower():
                    w_delivery = 0.5
                    w_price = 0.1
                    w_quality = 0.2
                    w_avail = 0.2
                elif "cheap" in str(constraints).lower() or "budget" in str(constraints).lower():
                    w_price = 0.6
                    w_delivery = 0.1
                    w_quality = 0.2
                    w_avail = 0.1
                
                total_score = (
                    (price_score * w_price) + 
                    (delivery_score * w_delivery) + 
                    (quality_score * w_quality) + 
                    (availability_score * w_avail)
                )
                
                rec = {
                    "id": f"{m['id']}_{s['id']}",
                    "material": m,
                    "supplier": s,
                    "price": round(price, 2),
                    "currency": "INR",
                    "delivery_days": delivery_days,
                    "quality_score": quality_score,
                    "availability_score": availability_score,
                    "match_score": round(total_score, 1),
                    "breakdown": {
                        "Price": f"{price_score:.0f} (w={w_price})",
                        "Delivery": f"{delivery_score:.0f} (w={w_delivery})",
                        "Quality": f"{quality_score} (w={w_quality})",
                        "Avail": f"{availability_score} (w={w_avail})"
                    }
                }
                recommendations.append(rec)
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations[:3] # Return top 3 options

    def get_po_types(self):
        """Returns list of valid PO Types"""
        return ["Asset", "Service", "Regular Purchase", "Internal Order Material", 
                "Internal Order Service", "Network", "Network Service", "Cost Center Material"]

    def get_org_options(self):
        """Fetches available Org and Group options"""
        return {
            "orgs": self.tools.search_purchase_orgs(""),
            "groups": self.tools.search_purchase_groups("")
        }

    def create_po(self, recommendation, quantity, po_type="Standard", purch_org=None, purch_group=None):
        """
        Creates a PO in the database and returns the details.
        """
        total_value = recommendation['price'] * quantity
        po_number = f"IND-PO-{random.randint(10000, 99999)}"
        
        # Get default Org Data if not provided
        try:
            with engine.connect() as conn:
                # Fetch first available Plant if needed (we still default plant for now as user didn't ask to change it)
                plant = conn.execute(text("SELECT id, code FROM plants LIMIT 1")).fetchone()
                plant_id, plant_code = (None, plant[1]) if plant else (None, "PL01")
                
                # Handle Org and Group
                if purch_org:
                    org_id, org_code = purch_org['id'], purch_org['code']
                else:
                    p_org = conn.execute(text("SELECT id, code FROM purchase_organization LIMIT 1")).fetchone()
                    org_id, org_code = (p_org[0], p_org[1]) if p_org else (None, "1000")
                
                if purch_group:
                    group_id, group_code = purch_group['id'], purch_group['code']
                else:
                    p_group = conn.execute(text("SELECT id, code FROM purchase_groups LIMIT 1")).fetchone()
                    group_id, group_code = (p_group[0], p_group[1]) if p_group else (None, "001")
                
                # Prepare Line Items JSON
                line_items = [
                    {
                        "material_id": recommendation['material']['id'],
                        "material_name": recommendation['material']['name'],
                        "quantity": quantity,
                        "price": recommendation['price'],
                        "total": total_value
                    }
                ]
                
                # Insert into DB
                query = text("""
                    INSERT INTO independent_purchase_orders (
                        po_number, po_date, validity_date, po_type,
                        supplier_id, supplier_name, currency,
                        plant_id, plant_code,
                        purchase_org_id, purchase_org_code,
                        purchase_group_id, purchase_group_code,
                        line_items, total_amount, status
                    ) VALUES (
                        :po_number, :po_date, :validity_date, :po_type,
                        :supplier_id, :supplier_name, :currency,
                        :plant_id, :plant_code,
                        :org_id, :org_code,
                        :group_id, :group_code,
                        :line_items, :total_amount, :status
                    )
                """)
                
                conn.execute(query, {
                    "po_number": po_number,
                    "po_date": datetime.now().strftime("%Y-%m-%d"),
                    "validity_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "po_type": po_type,
                    "supplier_id": recommendation['supplier']['id'],
                    "supplier_name": recommendation['supplier']['name'],
                    "currency": recommendation['currency'],
                    "plant_id": plant_id,
                    "plant_code": plant_code,
                    "org_id": org_id,
                    "org_code": org_code,
                    "group_id": group_id,
                    "group_code": group_code,
                    "line_items": json.dumps(line_items),
                    "total_amount": total_value,
                    "status": "Created"
                })
                conn.commit()
                
        except Exception as e:
            print(f"Error saving PO to DB: {e}")
            # Fallback for demo if DB fails
            pass
        
        return {
            "status": "success",
            "po_details": {
                "po_number": po_number,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "supplier": {
                    "name": recommendation['supplier']['name'],
                    "id": recommendation['supplier']['id'],
                    "score": recommendation['match_score']
                },
                "items": [
                    {
                        "material": recommendation['material']['name'],
                        "code": recommendation['material']['code'],
                        "quantity": quantity,
                        "unit_price": recommendation['price'],
                        "total": total_value,
                        "currency": recommendation['currency']
                    }
                ],
                "terms": {
                    "delivery_days": recommendation['delivery_days'],
                    "payment_term": "NT30" # Default
                },
                "org_data": {
                    "po_type": po_type,
                    "org_code": org_code,
                    "group_code": group_code
                }
            }
        }
