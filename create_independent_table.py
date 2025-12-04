from sqlalchemy import text
from backend.database import engine

def create_independent_po_table():
    query = """
    CREATE TABLE IF NOT EXISTS independent_purchase_orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        po_number VARCHAR(50) UNIQUE NOT NULL,
        
        -- Header
        po_date DATE,
        validity_date DATE,
        po_type VARCHAR(50),
        supplier_id VARCHAR(255),
        supplier_name VARCHAR(255),
        currency VARCHAR(10),
        
        -- Basic Info
        purchase_org_id INT,
        purchase_org_code VARCHAR(50),
        plant_id INT,
        plant_code VARCHAR(50),
        purchase_group_id INT,
        purchase_group_code VARCHAR(50),
        
        -- Optional Fields
        project_id INT,
        project_name VARCHAR(255),
        payment_term_id INT,
        payment_term_code VARCHAR(50),
        inco_term_id INT,
        inco_term_code VARCHAR(50),
        payment_description TEXT,
        remarks TEXT,
        
        -- Line Items (Stored as JSON for simplicity in this demo)
        line_items JSON,
        
        -- Meta
        total_amount FLOAT,
        status VARCHAR(50) DEFAULT 'Created',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()
            print("✅ Table 'independent_purchase_orders' created successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_independent_po_table()
