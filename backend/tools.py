from sqlalchemy import text
from backend.database import engine
from typing import List, Dict
from datetime import datetime

class POTools:
    """Custom tools for PO creation"""
    
    @staticmethod
    def get_suppliers(limit: int = 10) -> List[Dict]:
        """Fetch suppliers from database"""
        query = """
        SELECT id, supplier_name, emailID, mobile
        FROM supplier_details
        LIMIT :limit
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), {"limit": limit})
                return [{
                    "id": row[0],
                    "name": row[1],
                    "email": row[2],
                    "phone": row[3]
                } for row in result]
        except Exception as e:
            print(f"[ERROR] get_suppliers: {e}")
            return []

    @staticmethod
    def search_suppliers(query_str: str) -> List[Dict]:
        """Search suppliers by name"""
        query = """
        SELECT id, supplier_name, emailID
        FROM supplier_details
        WHERE supplier_name LIKE :search
        LIMIT 50
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), {"search": f"%{query_str}%"})
                return [{
                    "id": row[0],
                    "name": row[1],
                    "email": row[2]
                } for row in result]
        except Exception as e:
            print(f"[ERROR] search_suppliers: {e}")
            return []

    @staticmethod
    def search_plants(query_str: str) -> List[Dict]:
        """Search plants by name"""
        # Assuming 'plants' table exists, otherwise fallback or mock
        query = """
        SELECT id, plant_name, plant_code
        FROM plants
        WHERE plant_name LIKE :search
        LIMIT 50
        """
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), {"search": f"%{query_str}%"})
                return [{
                    "id": row[0],
                    "name": row[1],
                    "code": row[2]
                } for row in result]
        except Exception as e:
            print(f"[WARN] search_plants failed (using mock): {e}")
            # Mock fallback if table missing
            mock_plants = [
                {"id": 1, "name": "Noida Plant", "code": "P01"},
                {"id": 2, "name": "Delhi Plant", "code": "P02"},
                {"id": 3, "name": "Mumbai Plant", "code": "P03"}
            ]
            return [p for p in mock_plants if query_str.lower() in p['name'].lower()]

    @staticmethod
    def search_materials(query_str: str) -> List[Dict]:
        """Search materials by name"""
        if not query_str:
            query = "SELECT id, name, code, price FROM materials LIMIT 50"
            params = {}
        else:
            query = """
            SELECT id, name, code, price
            FROM materials 
            WHERE name LIKE :search OR code LIKE :search 
            LIMIT 50
            """
            params = {"search": f"%{query_str}%"}
            
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                return [{
                    "id": row[0],
                    "name": row[1],
                    "code": row[2],
                    "price": row[3] or 0
                } for row in result]
        except Exception as e:
            print(f"[WARN] search_materials failed (using mock): {e}")
            # Mock fallback
            mock_materials = [
                {"id": 1, "name": "MS Pipe", "code": "M01", "price": 100},
                {"id": 2, "name": "Steel Rod", "code": "M02", "price": 200},
                {"id": 3, "name": "Cement", "code": "M03", "price": 300}
            ]
            return [m for m in mock_materials if query_str.lower() in m['name'].lower()]

    @staticmethod
    def search_purchase_orgs(query_str: str = "") -> List[Dict]:
        """Search purchase organizations"""
        if not query_str:
            query = "SELECT id, code, description FROM purchase_organization LIMIT 50"
            params = {}
        else:
            query = "SELECT id, code, description FROM purchase_organization WHERE description LIKE :search OR code LIKE :search LIMIT 50"
            params = {"search": f"%{query_str}%"}
            
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                return [{"id": row[0], "code": row[1], "name": row[2]} for row in result]
        except Exception as e:
            print(f"[ERROR] search_purchase_orgs: {e}")
            return []

    @staticmethod
    def search_purchase_groups(query_str: str = "") -> List[Dict]:
        """Search purchase groups"""
        if not query_str:
            query = "SELECT id, code, name FROM purchase_groups LIMIT 50"
            params = {}
        else:
            query = "SELECT id, code, name FROM purchase_groups WHERE name LIKE :search OR code LIKE :search LIMIT 50"
            params = {"search": f"%{query_str}%"}
            
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query), params)
                return [{"id": row[0], "code": row[1], "name": row[2]} for row in result]
        except Exception as e:
            print(f"[ERROR] search_purchase_groups: {e}")
            return []

    @staticmethod
    def get_payment_terms() -> List[Dict]:
        """Fetch payment terms"""
        query = "SELECT id, code, name FROM payment_terms LIMIT 5"
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query))
                return [{"id": row[0], "code": row[1], "name": row[2]} for row in result]
        except Exception as e:
            print(f"[ERROR] get_payment_terms: {e}")
            return []
            
    @staticmethod
    def get_currencies() -> List[Dict]:
        """Fetch currencies"""
        query = "SELECT id, code, name FROM currencies LIMIT 50"
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query))
                return [{"id": row[0], "code": row[1], "name": row[2]} for row in result]
        except Exception as e:
            print(f"[ERROR] get_currencies: {e}")
            return []

    @staticmethod
    def create_independent_po(po_data: Dict) -> str:
        """Create independent purchase order"""
        import json
        import random
        
        po_number = f"IND-PO-{random.randint(10000, 99999)}"
        
        query = """
        INSERT INTO independent_purchase_orders (
            po_number, po_date, validity_date, po_type, 
            supplier_id, supplier_name, currency,
            purchase_org_id, purchase_org_code,
            plant_id, plant_code,
            purchase_group_id, purchase_group_code,
            line_items, total_amount, status
        ) VALUES (
            :po_number, :po_date, :validity_date, :po_type,
            :supplier_id, :supplier_name, :currency,
            :purchase_org_id, :purchase_org_code,
            :plant_id, :plant_code,
            :purchase_group_id, :purchase_group_code,
            :line_items, :total_amount, 'Created'
        )
        """
        
        try:
            with engine.connect() as conn:
                conn.execute(text(query), {
                    "po_number": po_number,
                    "po_date": po_data.get("po_date"),
                    "validity_date": po_data.get("validity_date"),
                    "po_type": po_data.get("po_type", "Standard"),
                    "supplier_id": po_data.get("supplier_id"),
                    "supplier_name": po_data.get("supplier_name"),
                    "currency": po_data.get("currency", "INR"),
                    "purchase_org_id": po_data.get("purchase_org_id"),
                    "purchase_org_code": po_data.get("purchase_org_code"),
                    "plant_id": po_data.get("plant_id"),
                    "plant_code": po_data.get("plant_code"),
                    "purchase_group_id": po_data.get("purchase_group_id"),
                    "purchase_group_code": po_data.get("purchase_group_code"),
                    "line_items": json.dumps(po_data.get("line_items", []), default=str),
                    "total_amount": po_data.get("total_amount", 0.0)
                })
                conn.commit()
                return po_number
        except Exception as e:
            print(f"[ERROR] create_independent_po: {e}")
            return f"ERROR-{e}"

    @staticmethod
    def create_po(po_data: Dict) -> str:
        """Create purchase order in local database"""
        import json
        import random
        
        po_number = f"PO-{random.randint(10000, 99999)}"
        
        query = """
        INSERT INTO agent_purchase_orders (
            po_number, supplier_id, supplier_name, plant_id, plant_name,
            material_name, quantity, unit_price, total_amount, delivery_date,
            status, raw_payload
        ) VALUES (
            :po_number, :supplier_id, :supplier_name, :plant_id, :plant_name,
            :material_name, :quantity, :unit_price, :total_amount, :delivery_date,
            'Created', :raw_payload
        )
        """
        
        try:
            with engine.connect() as conn:
                conn.execute(text(query), {
                    "po_number": po_number,
                    "supplier_id": po_data.get("supplier_id"),
                    "supplier_name": po_data.get("supplier_name"),
                    "plant_id": po_data.get("plant_id"),
                    "plant_name": po_data.get("plant_name"),
                    "material_name": po_data.get("material_name"),
                    "quantity": po_data.get("quantity"),
                    "unit_price": po_data.get("price"),
                    "total_amount": po_data.get("total"),
                    "delivery_date": po_data.get("delivery_date"),
                    "raw_payload": json.dumps(po_data, default=str)
                })
                conn.commit()
                return po_number
        except Exception as e:
            print(f"[ERROR] create_po: {e}")
            return f"ERROR-{e}"

