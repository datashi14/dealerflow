import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import get_connection
from sqlalchemy import text

def init_macro_db():
    print("Initializing Macro/Reflexivity Layer Schema...")
    
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'macro_schema.sql')
    
    with open(schema_path, 'r') as f:
        sql = f.read()
        
    with get_connection() as conn:
        conn.execute(text(sql))
        conn.commit()
            
    print("Macro Schema applied successfully.")

if __name__ == "__main__":
    init_macro_db()
