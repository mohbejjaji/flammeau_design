import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Use the same logic as core/database.py to get the URL
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(DATABASE_URL)

new_columns = [
    ("customer_city", "VARCHAR"),
    ("operation_title", "VARCHAR"),
    ("external_ref", "VARCHAR"),
    ("delivery_delay", "VARCHAR"),
    ("payment_terms", "VARCHAR"),
    ("delivery_location", "VARCHAR")
]

with engine.connect() as conn:
    for col_name, col_type in new_columns:
        try:
            print(f"Adding column {col_name}...")
            conn.execute(text(f"ALTER TABLE quotes ADD COLUMN {col_name} {col_type}"))
            conn.commit()
            print(f"Column {col_name} added successfully.")
        except Exception as e:
            if "already exists" in str(e):
                print(f"Column {col_name} already exists, skipping.")
            else:
                print(f"Error adding {col_name}: {e}")

print("Migration completed!")
