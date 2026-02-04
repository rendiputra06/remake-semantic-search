from backend.db import init_db
import os

if __name__ == "__main__":
    print("Starting database migration...")
    init_db()
    print("Migration finished.")
