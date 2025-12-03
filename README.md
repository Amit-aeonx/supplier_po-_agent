# Supplier PO Agent 🤖

AI-powered Purchase Order creation chatbot using AWS Bedrock Claude Sonnet and MySQL.

## Features

✅ Natural Language Processing - Create POs using plain English  
✅ Smart Validation - Validates suppliers, plants, and materials from database  
✅ Click-to-Select UI - Interactive buttons for quick selection  
✅ Database Storage - Stores POs in local MySQL database  

## Tech Stack

- **Backend:** Python, SQLAlchemy, AWS Bedrock (Claude Sonnet)
- **Frontend:** Streamlit
- **Database:** MySQL (local)

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file with:
```
MYSQL_DB=your_database
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
AWS_REGION=us-east-1
AWS_ACCESS_KEY=your_aws_key
AWS_SECRET_KEY=your_aws_secret
CLAUDE_SONNET_MODEL_ID=your_model_arn
```

### 3. Setup Database
```bash
python setup_database.py
```

### 4. Run Application
```bash
streamlit run frontend/app.py
```

Visit: `http://localhost:8501`

## Usage

**Option 1: Natural Language**
```
Create a PO for 120 MS Pipe for JINDAL supplier to Noida plant on 2025-12-20
```

**Option 2: Click-to-Select**
- Agent asks questions
- Click on suggested suppliers/plants/materials
- Confirm to create PO

## Database Schema

**Table:** `agent_purchase_orders`
- Stores all POs created by the agent
- Contains: PO number, supplier, plant, material, quantities, dates

## Project Structure

```
po-chatbot/
├── backend/
│   ├── agent.py          # Agent logic with 7-step flow
│   ├── database.py       # MySQL connection
│   ├── llm.py           # Bedrock integration
│   └── tools.py         # Validation & PO tools
├── frontend/
│   └── app.py           # Streamlit UI
├── setup_database.py    # Database setup script
├── requirements.txt     # Python dependencies
└── .env                # Configuration (not in repo)
```

## Security

⚠️ **Important:** Never commit `.env` file - it contains sensitive credentials

## License

MIT
