from sqlalchemy import text
from backend.database import get_db, engine

def get_purchase_groups():
    """Fetch all purchase groups from database"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, code, name FROM purchase_groups WHERE status = '1'"))
            groups = [{"id": row[0], "code": row[1], "name": row[2]} for row in result]
            return groups
    except Exception as e:
        print(f"Error fetching purchase groups: {e}")
        return []

def get_suppliers_from_db(limit=10):
    """Fetch suppliers directly from database"""
    try:
        with engine.connect() as conn:
            query = text(f"SELECT id, company_name, email, phone_no FROM public_suppliers LIMIT {limit}")
            result = conn.execute(query)
            suppliers = [
                {"id": row[0], "name": row[1], "email": row[2], "phone": row[3]} 
                for row in result
            ]
            return suppliers
    except Exception as e:
        print(f"Error fetching suppliers from DB: {e}")
        return []

def get_payment_terms_from_db():
    """Fetch payment terms from database"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, code, name FROM payment_terms"))
            terms = [{"id": row[0], "code": row[1], "name": row[2]} for row in result]
            return terms
    except Exception as e:
        print(f"Error fetching payment terms: {e}")
        return []

def get_inco_terms_from_db():
    """Fetch inco terms from database"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, code, name FROM inco_term"))
            terms = [{"id": row[0], "code": row[1], "name": row[2]} for row in result]
            return terms
    except Exception as e:
        print(f"Error fetching inco terms: {e}")
        return []
