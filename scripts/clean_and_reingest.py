import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db import get_connection

def clean_tables():
    print("Cleaning raw_futures (GOLD) and raw_fx (AUDUSD) to allow full re-ingestion...")
    with get_connection() as conn:
        with conn.begin():
            conn.execute(text("DELETE FROM raw_futures WHERE underlying='GOLD'"))
            conn.execute(text("DELETE FROM raw_fx WHERE pair='AUDUSD'"))
            
    print("Tables cleaned.")

if __name__ == "__main__":
    clean_tables()
