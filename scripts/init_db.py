import sys
import os

# Add the project root to the python path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.shared.db import init_db

def main():
    print("Starting database initialization...")
    try:
        # Point to the correct location of schema.sql relative to this script
        schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/shared/schema.sql'))
        init_db(schema_path)
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        print("Ensure you have a PostgreSQL database running and configured in your .env file.")

if __name__ == '__main__':
    main()
