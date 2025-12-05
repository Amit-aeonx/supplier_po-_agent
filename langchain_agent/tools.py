"""
LangChain Tools for PO Agent
Wraps the existing POTools as LangChain Tools
"""
from langchain_core.tools import tool
from typing import List, Dict
import sys
import os

# Add parent directory to path to import existing tools
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.tools import POTools

# Initialize the existing tools
po_tools = POTools()


@tool
def search_suppliers(query: str) -> str:
    """Search for suppliers by name. Returns a list of matching suppliers with their IDs and names."""
    results = po_tools.search_suppliers(query)
    if not results:
        return f"No suppliers found matching '{query}'"
    return "\n".join([f"- {r['name']} (ID: {r['id']})" for r in results])


@tool
def search_plants(query: str) -> str:
    """Search for plants by name. Returns a list of matching plants with their IDs, names, and codes."""
    results = po_tools.search_plants(query)
    if not results:
        return f"No plants found matching '{query}'"
    return "\n".join([f"- {r['name']} (ID: {r['id']}, Code: {r.get('code', 'N/A')})" for r in results])


@tool
def search_materials(query: str) -> str:
    """Search for materials by name. Returns a list of matching materials with their IDs, names, codes, and prices."""
    results = po_tools.search_materials(query)
    if not results:
        return f"No materials found matching '{query}'"
    return "\n".join([f"- {r['name']} (ID: {r['id']}, Code: {r['code']}, Price: {r['price']})" for r in results])


@tool
def search_purchase_orgs(query: str = "") -> str:
    """Search for purchase organizations. Returns a list of matching organizations with their IDs and names."""
    results = po_tools.search_purchase_orgs(query)
    if not results:
        return f"No purchase organizations found"
    return "\n".join([f"- {r['name']} (ID: {r['id']}, Code: {r.get('code', 'N/A')})" for r in results])


@tool
def search_purchase_groups(query: str = "") -> str:
    """Search for purchase groups. Returns a list of matching groups with their IDs and names."""
    results = po_tools.search_purchase_groups(query)
    if not results:
        return f"No purchase groups found"
    return "\n".join([f"- {r['name']} (ID: {r['id']}, Code: {r.get('code', 'N/A')})" for r in results])


@tool
def get_po_types() -> str:
    """Get the list of available PO types for Independent PO creation."""
    types = [
        "Asset",
        "Service", 
        "Regular Purchase",
        "Internal Order Material",
        "Internal Order Service",
        "Network",
        "Network Service",
        "Cost Center Material"
    ]
    return "Available PO Types:\n" + "\n".join([f"- {t}" for t in types])


@tool
def get_po_details(po_number: str) -> str:
    """
    Get the details of a specific Purchase Order by PO number.
    Returns all information about the PO including supplier, items, amounts, etc.
    """
    from backend.database import engine
    from sqlalchemy import text
    
    try:
        query = """
        SELECT 
            po_number,
            po_date,
            validity_date,
            po_type,
            supplier_name,
            currency,
            plant_code,
            purchase_org_code,
            purchase_group_code,
            total_amount,
            remarks,
            status
        FROM independent_purchase_orders
        WHERE po_number = :po_number
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query), {"po_number": po_number})
            row = result.fetchone()
            
            if not row:
                return f"❌ No purchase order found with PO Number: {po_number}"
            
            # Format the response
            details = f"""
📋 **Purchase Order Details**

**PO Number:** {row[0]}
**PO Date:** {row[1]}
**Validity Date:** {row[2]}
**PO Type:** {row[3]}

**Supplier:** {row[4]}
**Currency:** {row[5]}

**Organization:**
- Plant Code: {row[6]}
- Purchase Org Code: {row[7]}
- Purchase Group Code: {row[8]}

**Total Amount:** {row[9]} {row[5]}
**Status:** {row[11] or 'Active'}
**Remarks:** {row[10] or 'None'}
"""
            return details
            
    except Exception as e:
        return f"❌ Error retrieving PO details: {str(e)}"


@tool
def create_purchase_order(
    supplier_id: str,
    supplier_name: str,
    po_type: str,
    currency: str,
    plant_id: str,
    plant_code: str,
    purchase_org_id: str,
    purchase_org_code: str,
    purchase_group_id: str,
    purchase_group_code: str,
    material_name: str,
    quantity: float,
    unit_price: float,
    remarks: str = ""
) -> str:
    """
    Create a new Independent Purchase Order with the provided details.
    All required fields must be provided.
    Note: IDs can be strings (UUIDs) or integers.
    """
    from datetime import datetime, timedelta
    
    po_data = {
        "po_date": datetime.now().strftime("%Y-%m-%d"),
        "validity_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "po_type": po_type,
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "currency": currency,
        "purchase_org_id": purchase_org_id,
        "purchase_org_code": purchase_org_code,
        "plant_id": plant_id,
        "plant_code": plant_code,
        "purchase_group_id": purchase_group_id,
        "purchase_group_code": purchase_group_code,
        "line_items": [{
            "material": {"name": material_name},
            "quantity": quantity,
            "price": unit_price,
            "total": quantity * unit_price
        }],
        "total_amount": quantity * unit_price,
        "remarks": remarks
    }
    
    po_number = po_tools.create_independent_po(po_data)
    return f"✅ Purchase Order Created Successfully!\nPO Number: {po_number}"


# List of all tools for the agent
ALL_TOOLS = [
    search_suppliers,
    search_plants,
    search_materials,
    search_purchase_orgs,
    search_purchase_groups,
    get_po_types,
    get_po_details,
    create_purchase_order
]
