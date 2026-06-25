import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Use direct URL for migration to avoid DNS issues
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and "pooler.supabase.com" in DATABASE_URL:
    # Convert pooler URL to direct URL
    # From: postgresql://user.ref:pass@aws-1-eu-west-2.pooler.supabase.com:6543/postgres
    # To: postgresql://postgres:pass@db.ref.supabase.co:5432/postgres
    try:
        parts = DATABASE_URL.split("@")
        user_part = parts[0].split("//")[1]
        user, ref = user_part.split(".")
        password = user_part.split(":")[1] if ":" in user_part else ""
        
        # Simpler parsing
        import re
        match = re.search(r"postgresql://([^:]+)\.([^:]+):([^@]+)@([^:]+):", DATABASE_URL)
        if match:
            user_name, ref, password, pooler_host = match.groups()
            DATABASE_URL = f"postgresql://postgres:{password}@db.{ref}.supabase.co:5432/postgres"
    except:
        pass

if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Adding column 'size' to 'quote_items'...")
        conn.execute(text("ALTER TABLE quote_items ADD COLUMN size VARCHAR"))
        conn.commit()
        print("Column 'size' added successfully.")
except Exception as e:
    if "already exists" in str(e):
        print("Column 'size' already exists, skipping.")
    else:
        print(f"Error: {e}")
