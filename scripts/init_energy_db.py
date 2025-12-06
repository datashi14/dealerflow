import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import get_connection
from sqlalchemy import text

def init_energy_db():
    print("Initializing Energy Layer Schema...")
    
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'energy_schema.sql')
    
    with open(schema_path, 'r') as f:
        sql = f.read()
        
    with get_connection() as conn:
        # Execute raw SQL
        conn.execute(text(sql))
        conn.commit() # Ensure commit for DDL
            
    print("Energy Schema applied successfully.")

if __name__ == "__main__":
    init_energy_db()
