import os
import pandas as pd
from sqlalchemy import create_engine, text
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

def get_db_url():
    """
    Constructs DB URL from environment variables.
    """
    # If PG_CONN_STRING is set, use it (common in PaaS)
    if os.getenv("PG_CONN_STRING"):
        return os.getenv("PG_CONN_STRING")
    
    # Otherwise build from components
    user = os.getenv("PG_USER", "postgres")
    password = os.getenv("PG_PASSWORD", "password")
    host = os.getenv("PG_HOST", "localhost")
    port = os.getenv("PG_PORT", "5432")
    dbname = os.getenv("PG_DBNAME", "dealerflow")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

def get_engine():
    """
    Returns a SQLAlchemy engine.
    """
    return create_engine(get_db_url())

@contextmanager
def get_connection():
    """
    Context manager for raw connection (if needed).
    """
    engine = get_engine()
    with engine.connect() as conn:
        yield conn

def write_dataframe(df: pd.DataFrame, table_name: str, if_exists: str = 'append', index: bool = False):
    """
    Writes a pandas DataFrame to the database.
    """
    if df.empty:
        print(f"Skipping write to {table_name}: DataFrame is empty.")
        return

    engine = get_engine()
    try:
        df.to_sql(table_name, engine, if_exists=if_exists, index=index, method='multi')
        print(f"Successfully wrote {len(df)} rows to {table_name}.")
    except Exception as e:
        print(f"Error writing to {table_name}: {e}")
        raise

def execute_sql(sql: str, params: dict = None):
    """
    Executes a raw SQL statement.
    """
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})
