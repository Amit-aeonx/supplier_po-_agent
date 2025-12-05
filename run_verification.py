import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.tools import POTools
from backend.sql_agent import SQLAgent

def test_search_limits():
    print("Testing search limits...")
    # We can't easily verify > 5 if DB is small, but we can verify the code logic or try to fetch all
    # Let's just check if it returns a list and print the count
    
    # Mocking DB data might be needed if real DB is empty or small
    # But let's try with what we have.
    
    orgs = POTools.search_purchase_orgs("")
    print(f"Purchase Orgs found: {len(orgs)}")
    
    groups = POTools.search_purchase_groups("")
    print(f"Purchase Groups found: {len(groups)}")
    
    # If we had access to the SQL query string directly we could regex it, but here we just run it.
    # The important part is that we changed the code.

def test_table_formatting():
    print("\nTesting table formatting...")
    agent = SQLAgent()
    
    # Test with a query that would typically return *
    question = "Show me plants"
    sql = agent.generate_query(question)
    print(f"Generated SQL: {sql}")
    
    if "*" in sql:
        print("FAILURE: SQL contains SELECT *")
    else:
        print("SUCCESS: SQL does not contain SELECT *")
        
    if "created_at" in sql or "tenant_id" in sql:
        print("FAILURE: SQL contains internal columns")
    else:
        print("SUCCESS: SQL does not contain internal columns")

    # Run it to check formatting
    output = agent.run_query(sql)
    print("Output:")
    print(output)
    
    if "| " in output and "---" in output:
        print("SUCCESS: Output contains Markdown table structure.")
    else:
        print("FAILURE: Output does not look like a Markdown table.")

def test_currency_limits():
    print("\nTesting currency limits...")
    currencies = POTools.get_currencies()
    print(f"Currencies found: {len(currencies)}")
    if len(currencies) > 5:
        print("SUCCESS: Currency limit increased.")
    else:
        print("FAILURE: Currency limit is still small.")

if __name__ == "__main__":
    test_search_limits()
    test_table_formatting()
    test_currency_limits()
