import sqlite3
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(backend_dir, "cynera.db")
print(f"Migrating database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def add_col_if_missing(table, col, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cursor.fetchall()]
    if col not in cols:
        print(f"Adding {table}.{col} ({col_type})")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
    else:
        print(f"Column {table}.{col} already exists.")

# Profiles
add_col_if_missing('profiles', 'job_title', 'VARCHAR(100)')
add_col_if_missing('profiles', 'phone', 'VARCHAR(50)')
add_col_if_missing('profiles', 'is_verified', 'BOOLEAN DEFAULT 1')
add_col_if_missing('profiles', 'two_factor_enabled', 'BOOLEAN DEFAULT 0')

# Organizations
add_col_if_missing('organizations', 'org_type', "VARCHAR(100) DEFAULT 'Enterprise'")
add_col_if_missing('organizations', 'industry', "VARCHAR(100) DEFAULT 'Technology'")
add_col_if_missing('organizations', 'country', "VARCHAR(100) DEFAULT 'Global'")
add_col_if_missing('organizations', 'website', 'VARCHAR(255)')
add_col_if_missing('organizations', 'org_size', "VARCHAR(50) DEFAULT '10-50'")
add_col_if_missing('organizations', 'owner_id', 'VARCHAR(36)')
add_col_if_missing('organizations', 'is_active', 'BOOLEAN DEFAULT 1')
add_col_if_missing('organizations', 'updated_at', 'DATETIME')

conn.commit()
conn.close()
print("Migration completed successfully!")

