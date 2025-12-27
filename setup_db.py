import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Config
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('Pme@010607')
DB_NAME = os.getenv('DB_NAME', 'mechcare_db')

def setup():
    print(f"Connecting to MySQL at {DB_HOST} as {DB_USER}...")
    
    # 1. Connect to MySQL Server (no DB selected yet)
    try:
        cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password='Pme@010607'
        )
        cursor = cnx.cursor()
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return

    # 2. Create Database
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"Database '{DB_NAME}' checked/created.")
        cnx.database = DB_NAME
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")
        return

    # 3. Read and Apply Schema
    print("Applying schema...")
    apply_sql_file(cursor, 'schema.sql')

    # 4. Read and Apply Seeds (Teams/Equip)
    print("Applying basic seeds...")
    apply_sql_file(cursor, 'seeds.sql')

    cnx.commit()
    cursor.close()
    cnx.close()
    
    # 5. Run User Seeding (uses App context)
    print("Seeding Users...")
    import sys
    os.system(f"{sys.executable} seed_users.py")
    
    print("\nSetup Complete! You can now run 'python app.py'")

def apply_sql_file(cursor, filename):
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found.")
        return

    with open(filename, 'r') as f:
        statements = f.read().split(';')
        for stmt in statements:
            if stmt.strip():
                try:
                    cursor.execute(stmt)
                except mysql.connector.Error as err:
                    print(f"Error executing statement: {err}")
                    print(f"Statement: {stmt[:50]}...")

if __name__ == "__main__":
    setup()
