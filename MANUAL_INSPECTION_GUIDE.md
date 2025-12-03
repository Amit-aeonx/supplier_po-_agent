# Manual API Inspection Guide

Follow these steps to capture the exact API request details from your SupplierX application:

## Step 1: Login to SupplierX
1. Open your browser and go to: `https://dev.supplierx.cloud/login`
2. Login with your credentials

## Step 2: Open Developer Tools
1. Press **F12** to open Developer Tools
2. Click on the **Network** tab
3. (Optional) Click the **Clear** button (🚫) to clear existing network logs

## Step 3: Navigate to PO Creation Page
1. Go to: `https://dev.supplierx.cloud/supplier/purchase-order-create?returnTab=4`
2. Or navigate through the UI to the Purchase Order creation page

## Step 4: Fill Out the PO Form
Fill in the form with test data. Pay attention to:
- **PO Type** (Independent/PR-Based)
- **PO Date**
- **Validity End Date**
- **Supplier** selection
- **Purchase Group** (THIS IS IMPORTANT - note what value you select)
- **Payment Terms**
- **Inco Terms**
- **Items** (add at least one item)
- Any other required fields

## Step 5: Submit and Capture the Request
1. Click the **Submit** or **Create PO** button
2. In the Network tab, look for a request to:
   - `/api/v1/supplier/purchase-order/create` or
   - Any URL containing `purchase-order/create`
3. Click on that request to view its details

## Step 6: Extract Request Headers
In the request details, find the **Headers** tab and copy:

```
Authorization: Bearer <your_token_here>
x-session-key: <your_session_key_here>
Content-Type: <content_type_here>
```

**Update your `.env` file with these values:**
```bash
SUPPLIERX_API_TOKEN=<paste_token_here_WITHOUT_Bearer_prefix>
SUPPLIERX_SESSION_KEY=<paste_session_key_here>
```

## Step 7: Extract Request Payload
In the request details, find the **Payload** or **Request** tab and copy ALL the fields being sent.

Look for fields like:
- `supplier_id`
- `payment_term`
- `inco_term`
- `currency`
- `po_type`
- `po_date`
- `validityEnd`
- `purchase_group` ⭐ **IMPORTANT**
- `items`
- Any other fields

## Step 8: Note the Data Types and Format
Pay attention to:
- Are dates in format `YYYY-MM-DD` or `DD/MM/YYYY`?
- Is `supplier_id` a number or string?
- Is `purchase_group` a number, string, or object?
- Is `items` sent as JSON string or JSON array?
- What is the Content-Type? (multipart/form-data, application/json, etc.)

## Step 9: Check the Response
Look at the response to see:
- If it was successful (200/201 status)
- What the response structure looks like
- Where the PO number is in the response

## Step 10: Update the Code
Once you have all this information, update:

1. **`.env` file** with fresh token and session key
2. **`backend/tools_api.py`** with:
   - Correct field names
   - Correct data types
   - Correct default values (especially `purchase_group`)
   - Correct Content-Type if needed

---

## Quick Test After Updates

Run this command to test the API:
```bash
python backend/tools_api.py
```

This will show you detailed debug output of the request and response.

---

## Common Issues

### 401 Unauthorized
- Token expired (tokens usually expire after a few hours)
- Wrong token format (should NOT include "Bearer " in .env)
- Missing or wrong session key

### 400 Bad Request
- Missing required fields
- Wrong data type (e.g., sending string when number expected)
- Invalid values (e.g., wrong `purchase_group` ID)
- Wrong date format

### 404 Not Found
- Wrong API endpoint URL
- Wrong HTTP method (GET vs POST)

---

## Example of What You're Looking For

In the Network tab, you should see something like:

**Request URL:**
```
https://dev.api.supplierx.aeonx.digital/api/v1/supplier/purchase-order/create
```

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
x-session-key: 84df9d0c70ebcbcb86afa4c6b61f51f7451e605d...
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary...
```

**Request Payload (Form Data):**
```
supplier_id: 123
payment_term: Net 30
inco_term: FOB
currency: INR
po_type: material
po_date: 2025-12-02
validityEnd: 2026-01-01
purchase_group: 5
items: [{"name":"Laptop","quantity":50,"unit_price":873,"total":43650}]
```

Copy ALL of these details!
