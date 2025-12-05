from backend.database import engine
from sqlalchemy import text
import json

def get_latest_po():
    try:
        with engine.connect() as conn:
            # Check Org and Group
            org = conn.execute(text("SELECT id, code FROM purchase_organization LIMIT 1")).fetchone()
            group = conn.execute(text("SELECT id, code FROM purchase_groups LIMIT 1")).fetchone()
            
            print(f"Org: ID={org[0]} (Type: {type(org[0])})")
            print(f"Group: ID={group[0]} (Type: {type(group[0])})")
            
            if result:
                # Convert row to dict
                columns = result._mapping.keys()
                po_data = dict(zip(columns, result))
                
                print(f"\n✅ Found Latest PO: {po_data['po_number']}")
                print("-" * 30)
                print(f"ID: {po_data['id']}")
                print(f"Date: {po_data['po_date']}")
                print(f"Supplier: {po_data['supplier_name']} ({po_data['supplier_id']})")
                print(f"Plant: {po_data['plant_code']}")
                print(f"Org: {po_data['purchase_org_code']}")
                print(f"Group: {po_data['purchase_group_code']}")
                print(f"Total Amount: {po_data['currency']} {po_data['total_amount']}")
                print(f"Status: {po_data['status']}")
                print("-" * 30)
                
                # Parse Line Items
                if po_data['line_items']:
                    try:
                        items = json.loads(po_data['line_items'])
                        print("\nLine Items:")
                        for item in items:
                            print(f" - {item['material_name']} (Qty: {item['quantity']}) @ {item['price']}")
                    except:
                        print(f"Raw Line Items: {po_data['line_items']}")
            else:
                print("❌ No Purchase Orders found in 'independent_purchase_orders' table.")
                
    except Exception as e:
        print(f"Error fetching PO: {e}")

if __name__ == "__main__":
    get_latest_po()
