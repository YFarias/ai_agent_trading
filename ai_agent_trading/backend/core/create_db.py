# backend/core/create_db.py

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.database import create_db_and_tables
    print("Successfully imported 'create_db_and_tables' from 'core.database'.")
except ImportError as e:
    print("Failed to import required modules. Please check your installation.")
    print(f"Error: {e}")
    sys.exit(1)

if __name__ == "__main__":
    try:
        create_db_and_tables()
        print("Database and tables created successfully.")
    except Exception as e:
        print("An error occurred while creating the database and tables.")
        print(f"Error: {e}")
        sys.exit(1)
