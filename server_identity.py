from sqlalchemy import text
from backend.database import engine
import socket

print("--- 🔍 DATABASE LOCATION VERIFICATION 🔍 ---\n")

# 1. Check what the Python code sees as the target
print(f"Target Host in Config: {engine.url.host}")
print(f"Target Port in Config: {engine.url.port}")
print(f"Target Database:       {engine.url.database}")

# 2. Ask the Database Server for its identity
try:
    with engine.connect() as conn:
        # Get hostname from DB
        result = conn.execute(text("SELECT @@hostname"))
        db_hostname = result.scalar()
        
        # Get version
        result = conn.execute(text("SELECT @@version"))
        db_version = result.scalar()
        
        # Get data directory (often shows path like C:\ProgramData\MySQL...)
        try:
            result = conn.execute(text("SELECT @@datadir"))
            data_dir = result.scalar()
        except:
            data_dir = "Permission denied to view datadir"

        print(f"\n✅ CONNECTED SUCCESSFULLY")
        print(f"DB Server Hostname:  {db_hostname}")
        print(f"DB Server Version:   {db_version}")
        print(f"Data Directory:      {data_dir}")
        
        # 3. Resolve 'localhost' to IP to be sure
        local_ip = socket.gethostbyname('localhost')
        print(f"\nYour 'localhost' resolves to: {local_ip}")
        
        if engine.url.host in ['localhost', '127.0.0.1']:
            print("\n🟢 CONCLUSION: This is definitely your LOCAL machine.")
        else:
            print(f"\n🔴 CONCLUSION: This is a REMOTE server at {engine.url.host}")

except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")
