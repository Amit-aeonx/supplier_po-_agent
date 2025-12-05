import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.sql_agent import SQLAgent

def inspect_schema():
    from backend.database import engine
    from sqlalchemy import text
    print("--- ALL TABLES ---")
    table_names = []
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        for row in result:
            table_name = row[0]
            print(table_name)
            table_names.append(table_name)

        print("\n--- PLANT_ID COLUMN DETAILS ---")
        for t in table_names:
            print(f"\nTable: {t}")
            result = conn.execute(text(f"SHOW COLUMNS FROM {t} LIKE 'plant_id'"))
            found_plant_id = False
            for row in result:
                found_plant_id = True
                print(f"  Column: {row[0]}, Type: {row[1]}, Null: {row[2]}, Key: {row[3]}, Default: {row[4]}, Extra: {row[5]}")
            if not found_plant_id:
                print("  No 'plant_id' column found.")

if __name__ == "__main__":
    inspect_schema()
