from sqlalchemy import text
from backend.database import engine

def inspect_columns():
    tables = [
        "purchase_organization",
        "purchase_groups",
        "payment_terms",
        "inco_term",
        "po_projects",
        "currencies"
    ]
    
    print("--- 🔍 INSPECTING TABLE COLUMNS 🔍 ---\n")
    
    with engine.connect() as conn:
        for t in tables:
            print(f"\nTable: {t}")
            try:
                # Get columns
                result = conn.execute(text(f"SHOW COLUMNS FROM {t}"))
                for row in result:
                    print(f"  - {row[0]} ({row[1]})")
                
                # Get sample data
                result = conn.execute(text(f"SELECT * FROM {t} LIMIT 1"))
                row = result.fetchone()
                if row:
                    print(f"  SAMPLE: {row}")
            except Exception as e:
                print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    inspect_columns()
