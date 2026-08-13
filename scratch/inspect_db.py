import sqlite3
import pandas as pd
import os

db_path = r"c:\TA adam\output ta\keday70_v7\keday70.db"

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print("# Database Structure: keday70.db\n")

for table in tables:
    print(f"## Table: {table}")
    
    # Get schema
    cursor.execute(f"PRAGMA table_info('{table}');")
    schema_rows = cursor.fetchall()
    print("### Schema:")
    print("| CID | Name | Type | NotNull | PK |")
    print("|---|---|---|---|---|")
    for row in schema_rows:
        print(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[5]} |")
    
    # Get sample data
    cursor.execute(f"SELECT * FROM '{table}' LIMIT 5;")
    sample_rows = cursor.fetchall()
    cursor.execute(f"PRAGMA table_info('{table}');")
    cols = [col[1] for col in cursor.fetchall()]
    
    print("\n### Sample Data (First 5 rows):")
    print("| " + " | ".join(cols) + " |")
    print("| " + " | ".join(["---"] * len(cols)) + " |")
    for row in sample_rows:
        print("| " + " | ".join(str(v).replace("\n", " ") for v in row) + " |")
    print("\n---\n")

conn.close()
