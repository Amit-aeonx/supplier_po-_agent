from sqlalchemy import text
from backend.database import engine

def check_master_tables():
    tables_to_check = [
        "purchase_organization", "purchase_organizations",
        "purchase_group", "purchase_groups",
        "payment_term", "payment_terms",
        "inco_term", "inco_terms",
        "project", "projects",
        "currency", "currencies",
        "service", "services",
        "material_group", "material_groups"
    ]
    
    print("--- 🔍 CHECKING FOR MASTER DATA TABLES 🔍 ---\n")
    
    try:
        with engine.connect() as conn:
            # Get all tables
            result = conn.execute(text("SHOW TABLES"))
            all_tables = [row[0] for row in result]
            
            found_tables = []
            for t in tables_to_check:
                # Simple substring match or exact match
                matches = [existing for existing in all_tables if t in existing.lower()]
                if matches:
                    found_tables.extend(matches)
            
            # Remove duplicates
            found_tables = list(set(found_tables))
            
            if found_tables:
                print(f"✅ FOUND {len(found_tables)} POTENTIAL MASTER TABLES:")
                for t in sorted(found_tables):
                    print(f"  - {t}")
            else:
                print("❌ NO obvious master data tables found")
                print("\nAll Tables in DB:")
                for t in all_tables:
                    print(f"  - {t}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_master_tables()
