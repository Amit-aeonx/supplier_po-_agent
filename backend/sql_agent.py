import boto3
import json
import os
from sqlalchemy import text
from backend.database import engine
from typing import Optional

class SQLAgent:
    def __init__(self):
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
        )
        self.model_id = os.getenv('CLAUDE_SONNET_MODEL_ID', 'anthropic.claude-3-5-sonnet-20240620-v1:0')

    def get_schema(self) -> str:
        """Get schema for relevant tables"""
        # We only expose safe tables for querying
        tables = [
            "plants", 
            "supplier_details", 
            "independent_purchase_orders",
            "purchase_organization",
            "purchase_groups",
            "materials"
        ]
        
        schema_info = []
        try:
            with engine.connect() as conn:
                for t in tables:
                    try:
                        # Get columns
                        result = conn.execute(text(f"SHOW COLUMNS FROM {t}"))
                        
                        # Filter out internal/technical columns
                        excluded = ['created_at', 'updated_at', 'isDeleted', 'tenant_id', 'modifiedBy', 
                                   'mrp_activated', 'default_mrp_area', 'default_mrp_type']
                        
                        cols = [f"{row[0]} ({row[1]})" for row in result if row[0] not in excluded]
                        schema_info.append(f"Table {t}: {', '.join(cols)}")
                    except Exception as e:
                        # Skip tables that don't exist
                        continue
        except Exception as e:
            print(f"[ERROR] get_schema: {e}")
            
        return "\n".join(schema_info) if schema_info else "No tables available"

    def generate_query(self, question: str) -> Optional[str]:
        """Generate SQL query from natural language"""
        schema = self.get_schema()
        
        prompt = f"""
        You are a SQL expert. Convert the user's question into a valid MySQL query.
        
        Database Schema:
        {schema}
        
        Rules:
        1. Return ONLY the SQL query. No markdown, no explanation.
        2. Use only SELECT statements. No INSERT, UPDATE, DELETE.
        3. If the question cannot be answered with the schema, return "NO_QUERY".
        4. Limit results to 10 rows unless specified otherwise.
        5. NEVER use SELECT *. Always select specific, relevant columns (e.g., id, name, code, city, status).
        6. For 'supplier_details', use 'name' column for supplier name.
        7. For 'plants', use 'name' column for plant name.
        8. Use LIKE %...% for text searches (case insensitive).
        
        User Question: "{question}"
        """
        
        print(f"[DEBUG] Sending prompt to Bedrock for: {question}")
        
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=body
            )
            
            response_body = json.loads(response.get('body').read())
            sql = response_body['content'][0]['text'].strip()
            
            # Cleanup
            sql = sql.replace("```sql", "").replace("```", "").strip()
            print(f"[DEBUG] Generated SQL: {sql}")
            
            if "NO_QUERY" in sql or not sql.lower().startswith("select"):
                print(f"[WARN] Invalid SQL generated: {sql}")
                return None
                
            return sql
            
        except Exception as e:
            print(f"[ERROR] generate_query: {e}")
            return None

    def run_query(self, sql: str) -> str:
        """Execute SQL query and return formatted string results"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = [dict(row._mapping) for row in result]
                
                if not rows:
                    return "No results found."
                
                # Format as a Markdown table
                output = f"Found {len(rows)} results:\n\n"
                
                # Get headers from first row
                headers = list(rows[0].keys())
                
                # Create Markdown table header
                header_row = "| " + " | ".join(headers) + " |"
                separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
                output += f"{header_row}\n{separator_row}\n"
                
                # Create table body
                for row in rows:
                    row_values = [str(row.get(h, "")) for h in headers]
                    output += "| " + " | ".join(row_values) + " |\n"
                    
                return output
                
        except Exception as e:
            return f"Error executing query: {e}"

    def answer_question(self, question: str) -> str:
        """End-to-end question answering"""
        sql = self.generate_query(question)
        if not sql:
            return "I couldn't generate a query for that. Please try asking differently."
        
        print(f"[DEBUG] Generated SQL: {sql}")
        return self.run_query(sql)
