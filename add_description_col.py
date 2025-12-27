import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def update_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'mechcare_db')
        )
        cursor = conn.cursor()
        print("Connected to DB.")

        # Check if description column exists in MaintenanceRequest
        cursor.execute("SHOW COLUMNS FROM MaintenanceRequest LIKE 'description'")
        if not cursor.fetchone():
            print("Adding description column to MaintenanceRequest...")
            cursor.execute("ALTER TABLE MaintenanceRequest ADD COLUMN description TEXT")
            conn.commit()
            print("Column added.")
        else:
            print("Column description already exists.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_db()
