"""Quick script to test database connection."""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env file")
    exit(1)

try:
    print("🔌 Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"📊 PostgreSQL version: {version}")
        
        # Check if tables exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print(f"📋 Found {len(tables)} table(s): {', '.join(tables)}")
        else:
            print("⚠️  No tables found. Run 'alembic upgrade head' to create them.")
            
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)
