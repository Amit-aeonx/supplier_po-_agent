"""
LangChain SQL Chain for Text-to-SQL queries
"""
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from langchain_agent.llm import get_llm_with_credentials

load_dotenv()


def get_database():
    """Create SQLDatabase connection"""
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "1234567890")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "supplierx_development")
    
    connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}"
    
    # Only include relevant tables
    include_tables = [
        "supplier_details",
        "plants",
        "materials",
        "purchase_organization",
        "purchase_groups",
        "independent_purchase_orders"
    ]
    
    return SQLDatabase.from_uri(
        connection_string,
        include_tables=include_tables,
        sample_rows_in_table_info=3
    )


class SQLChain:
    """Text-to-SQL chain using LangChain"""
    
    def __init__(self):
        self.llm = get_llm_with_credentials()
        self.db = get_database()
        
        # Create the SQL query chain
        self.query_chain = create_sql_query_chain(self.llm, self.db)
        
        # Answer prompt
        self.answer_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that answers questions about the database.
Given the following SQL query and its results, provide a natural language answer.

SQL Query: {query}
Results: {result}

Provide a clear, concise answer to the original question."""),
            ("human", "{question}")
        ])
    
    def run(self, question: str) -> str:
        """Execute a natural language query and return the answer"""
        try:
            # Generate SQL query
            sql_response = self.query_chain.invoke({"question": question})
            
            print(f"[DEBUG] Raw SQL Response: {sql_response}")
            
            # Clean the query - multiple strategies
            sql_query = sql_response.strip()
            
            # Remove markdown code blocks
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            
            # Remove "SQLQuery:" prefix if present
            if "SQLQuery:" in sql_query:
                sql_query = sql_query.split("SQLQuery:")[-1].strip()
            
            # Extract SQL using regex (SELECT, INSERT, UPDATE, DELETE, SHOW, DESCRIBE)
            import re
            sql_pattern = r'(SELECT|INSERT|UPDATE|DELETE|SHOW|DESCRIBE|EXPLAIN)[\s\S]*?(?:;|$)'
            matches = re.findall(sql_pattern, sql_query, re.IGNORECASE)
            
            if matches:
                # Take the first SQL statement found
                sql_query = matches[0].strip()
            else:
                # Fallback: take first line that looks like SQL
                lines = sql_query.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and any(keyword in line.upper() for keyword in ["SELECT", "SHOW", "DESCRIBE"]):
                        sql_query = line
                        break
            
            # Remove trailing semicolon
            sql_query = sql_query.rstrip(";").strip()
            
            # Validate it's not empty or just a keyword
            if not sql_query or len(sql_query) < 10:
                return "I couldn't generate a valid SQL query for that question. Please try rephrasing."
            
            print(f"[DEBUG] Cleaned SQL: {sql_query}")
            
            # Execute the query
            result = self.db.run(sql_query)
            
            # Format the answer
            answer_chain = self.answer_prompt | self.llm | StrOutputParser()
            answer = answer_chain.invoke({
                "query": sql_query,
                "result": result,
                "question": question
            })
            
            return f"**Query:** `{sql_query}`\n\n{answer}"
            
        except Exception as e:
            print(f"[SQL Error] {e}")
            return f"❌ I couldn't answer that question.\n\n**Error:** {str(e)}\n\n**Tip:** Try asking: 'Show me all purchase orders' or 'List materials'"


# Singleton instance
_sql_chain = None

def get_sql_chain():
    """Get or create the SQL chain singleton"""
    global _sql_chain
    if _sql_chain is None:
        _sql_chain = SQLChain()
    return _sql_chain
