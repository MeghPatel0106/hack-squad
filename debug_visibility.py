from app import app
from db import get_db

def debug_data():
    with app.app_context():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        print("--- LATEST REQUESTS ---")
        cursor.execute("SELECT id, subject, team_id, technician_id, created_by_user_id FROM MaintenanceRequest ORDER BY id DESC LIMIT 3")
        for r in cursor.fetchall():
            print(r)
            
        print("\n--- TECHNICIANS ---")
        cursor.execute("SELECT id, name, user_id, team_id FROM Technician")
        for t in cursor.fetchall():
            print(t)
            
        print("\n--- TEAMS ---")
        cursor.execute("SELECT * FROM MaintenanceTeam")
        for t in cursor.fetchall():
            print(t)

        cursor.close()

if __name__ == '__main__':
    debug_data()
