"""
Setup script for PO Agent - Creates the agent_purchase_orders table
Run this once to initialize the database for the agent
"""
from sqlalchemy import text
from backend.database import engine

def setup_database():
    """Create agent_purchase_orders table"""
    
    create_query = """
    CREATE TABLE IF NOT EXISTS agent_purchase_orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        po_number VARCHAR(50) UNIQUE NOT NULL,
        supplier_id VARCHAR(255),
        supplier_name VARCHAR(255),
        plant_id INT,
        plant_name VARCHAR(255),
        material_name VARCHAR(255),
        quantity FLOAT,
        unit_price FLOAT,
        total_amount FLOAT,
        delivery_date DATE,
        status VARCHAR(50) DEFAULT 'Created',
        raw_payload TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_po_number (po_number),
        INDEX idx_supplier_id (supplier_id)
    )
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_query))
            conn.commit()
            print("✅ Table 'agent_purchase_orders' created successfully!")
            
            # Verify
            result = conn.execute(text("SHOW TABLES LIKE 'agent_purchase_orders'"))
            if result.fetchone():
                print("✅ Verified: Table exists in database")
                
                # Show structure
                result = conn.execute(text("DESCRIBE agent_purchase_orders"))
                print("\nTable structure:")
                for row in result:
                    print(f"  - {row[0]} ({row[1]})")
            else:
                print("❌ Warning: Could not verify table creation")
                
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Setting up PO Agent database...")
    print(f"Database: supplierx_development")
    print(f"Host: localhost\n")
    
    if setup_database():
        print("\n🎉 Setup complete! You can now use the PO agent.")
    else:
        print("\n❌ Setup failed. Please check the error above.")
