import streamlit as st
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smart_backend.smart_agent import SmartPOAgent

# Page config
st.set_page_config(
    page_title="Smart SupplierX Agent",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .rec-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
        transition: transform 0.2s;
    }
    .rec-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    .score-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .price-tag {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Agent
if "smart_agent" not in st.session_state:
    st.session_state.smart_agent = SmartPOAgent()

# Header
st.markdown("""
<div class="main-header">
    <h1>⚡ Smart SupplierX Agent</h1>
    <p>Describe what you need, and I'll find the best options.</p>
</div>
""", unsafe_allow_html=True)

# Main Input
query = st.text_input("What do you need?", placeholder="e.g., I need 10 laptops for the Noida office, fastest delivery")

if query:
    if "last_query" not in st.session_state or st.session_state.last_query != query:
        with st.spinner("Analyzing your request and ranking suppliers..."):
            # 1. Parse Intent
            intent = st.session_state.smart_agent.parse_intent(query)
            st.session_state.intent = intent
            
            # 2. Get Recommendations
            recs = st.session_state.smart_agent.get_recommendations(intent)
            st.session_state.recommendations = recs
            st.session_state.last_query = query

    # Display Results (Only if not in review mode)
    if st.session_state.get("recommendations") and not st.session_state.get("review_mode"):
        intent = st.session_state.intent
        st.info(f"Looking for **{intent.get('quantity')} x {intent.get('item_description')}** | Constraints: {intent.get('constraints')}")
        
        cols = st.columns(3)
        
        for idx, rec in enumerate(st.session_state.recommendations):
            with cols[idx]:
                bd = rec['breakdown']
                st.markdown(f"""
                <div class="rec-card">
                    <h3>{rec['supplier']['name']}</h3>
                    <p style="color: #6c757d;">{rec['material']['name']}</p>
                    <div class="price-tag">{rec['currency']} {rec['price']}</div>
                    <p>📦 Delivery: <strong>{rec['delivery_days']} days</strong></p>
                    <p>⭐ Quality: <strong>{rec['quality_score']}/100</strong></p>
                    <p>✅ Avail: <strong>{rec['availability_score']}%</strong></p>
                    <hr>
                    <p><span class="score-badge">Total Score: {rec['match_score']}</span></p>
                    <div style="font-size: 0.8rem; color: #666;">
                        Price: {bd['Price']}<br>
                        Deliv: {bd['Delivery']}<br>
                        Qual: {bd['Quality']}<br>
                        Avail: {bd['Avail']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select Option {idx+1}", key=f"btn_{idx}", use_container_width=True):
                    # Enter Review Mode
                    st.session_state.selected_rec = rec
                    st.session_state.review_mode = True
                    st.rerun()

    # Review & Edit Mode
    if st.session_state.get("review_mode") and st.session_state.get("selected_rec"):
        rec = st.session_state.selected_rec
        st.markdown("## 📝 Edit & Confirm Purchase Order")
        
        with st.form("po_review_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Supplier Details")
                st.text_input("Supplier Name", value=rec['supplier']['name'], disabled=True)
                st.text_input("Supplier ID", value=rec['supplier']['id'], disabled=True)
                
            with col2:
                st.subheader("Item Details")
                st.text_input("Material", value=rec['material']['name'], disabled=True)
                
                # Editable Fields
                new_qty = st.number_input("Quantity", min_value=1, value=int(st.session_state.intent.get('quantity', 1)))
                new_price = st.number_input("Unit Price (INR)", min_value=0.01, value=float(rec['price']))
                
                # Delivery Date Calculation
                default_date = datetime.now() + timedelta(days=rec['delivery_days'])
                new_date = st.date_input("Delivery Date", value=default_date)
            
            st.markdown("---")
            total_val = new_qty * new_price
            
            # Draft Preview
            st.markdown("### � Draft PO Preview")
            st.info(f"""
            **PO Summary:**
            - **Supplier:** {rec['supplier']['name']}
            - **Item:** {rec['material']['name']}
            - **Quantity:** {new_qty}
            - **Unit Price:** INR {new_price:,.2f}
            - **Total Value:** INR {total_val:,.2f}
            - **Delivery Date:** {new_date.strftime('%Y-%m-%d')}
            """)
            
            c1, c2 = st.columns([1, 4])
            with c1:
                submitted = st.form_submit_button("✅ Confirm & Create PO", type="primary")
            with c2:
                cancelled = st.form_submit_button("❌ Cancel")
                
            if submitted:
                # Update rec with edited values for creation
                rec['price'] = new_price
                rec['delivery_days'] = (new_date - datetime.now().date()).days
                
                with st.spinner("Creating Purchase Order..."):
                    result = st.session_state.smart_agent.create_po(rec, new_qty)
                    st.session_state.po_result = result
                    st.session_state.review_mode = False
                    st.rerun()
            
            if cancelled:
                st.session_state.review_mode = False
                del st.session_state.selected_rec
                st.rerun()

# Success Modal / Result
if "po_result" in st.session_state:
    res = st.session_state.po_result
    details = res['po_details']
    
    st.success(f"✅ Purchase Order Created Successfully! **{details['po_number']}**")
    
    st.markdown("### 📄 PO Summary")
    
    # Header Info
    c1, c2, c3 = st.columns(3)
    c1.metric("PO Number", details['po_number'])
    c2.metric("Date", details['created_at'].split(" ")[0])
    c3.metric("Status", "Created")
    
    # Supplier Info
    st.markdown("#### Supplier")
    st.markdown(f"**{details['supplier']['name']}** (ID: `{details['supplier']['id']}`)")
    
    # Line Items Table
    st.markdown("#### Line Items")
    items_data = []
    for item in details['items']:
        items_data.append({
            "Material": item['material'],
            "Code": item['code'],
            "Quantity": item['quantity'],
            "Unit Price": f"{item['currency']} {item['unit_price']}",
            "Total": f"{item['currency']} {item['total']}"
        })
    st.table(items_data)
    
    # Total
    total_amount = sum([item['total'] for item in details['items']])
    st.markdown(f"### 💰 Total Amount: {details['items'][0]['currency']} {total_amount:,.2f}")
    
    if st.button("Start Over"):
        del st.session_state.po_result
        del st.session_state.last_query
        del st.session_state.recommendations
        st.rerun()
