import sqlite3
import os
import sys

# Добавляем корневую директорию в путь, чтобы импортировать CONFIG
sys.path.append(os.getcwd())

from common.config import CONFIG

def migrate():
    db_path = CONFIG.database.path
    print(f"Migrating database at {db_path}...")
    
    if not os.path.exists(db_path):
        print("Database file not found. It will be created when the bot starts.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Добавляем streak_count
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN streak_count INTEGER DEFAULT 0 NOT NULL")
        print("Added streak_count column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("streak_count column already exists")
        else:
            print(f"Error adding streak_count: {e}")
        
    # 2. Добавляем last_activity_date
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_activity_date TEXT")
        print("Added last_activity_date column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("last_activity_date column already exists")
        else:
            print(f"Error adding last_activity_date: {e}")

    # 3. Добавляем activity_history
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN activity_history JSON DEFAULT '[]' NOT NULL")
        print("Added activity_history column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("activity_history column already exists")
        else:
            print(f"Error adding activity_history: {e}")
        
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
