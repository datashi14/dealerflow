import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_connection_string():
    """
    Retrieves the database connection string from environment variables.
    Expects 'PG_CONN_STRING' or individual params.
    """
    conn_string = os.getenv('PG_CONN_STRING')
    if conn_string:
        return conn_string
    
    # Fallback to individual credentials if provided
    user = os.getenv('PG_USER', 'postgres')
    password = os.getenv('PG_PASSWORD', 'postgres')
    host = os.getenv('PG_HOST', 'localhost')
    port = os.getenv('PG_PORT', '5432')
    dbname = os.getenv('PG_DBNAME', 'dealerflow')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Yields a connection object.
    """
    conn_string = get_connection_string()
    conn = None
    try:
        conn = psycopg2.connect(conn_string)
        yield conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise
    finally:
        if conn:
            conn.close()

def execute_query(query, params=None, fetch=False):
    """
    Executes a single query.
    If fetch is True, returns the result as a list of dictionaries.
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
            except psycopg2.Error as e:
                conn.rollback()
                print(f"Error executing query: {e}")
                raise

def init_db(schema_path='src/shared/schema.sql'):
    """
    Initializes the database by applying the schema.sql file.
    """
    if not os.path.exists(schema_path):
        print(f"Schema file not found at {schema_path}")
        return

    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    print(f"Applying schema from {schema_path}...")
    # We iterate strictly statement by statement if we want to handle errors granularly,
    # but for a schema file, running it as one block is often okay if it's just CREATE TABLE IF NOT EXISTS.
    # However, splitting by ';' can be safer for some drivers.
    # For now, let's execute the whole block.
    
    execute_query(schema_sql)
    print("Database initialized successfully.")
