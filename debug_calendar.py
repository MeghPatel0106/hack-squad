from app import app
from db import get_db

def check_visibility():
    with app.app_context():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        print("\n--- 1. Search for Requests around Dec 27 ---")
        cursor.execute("SELECT id, subject, scheduled_date, team_id, technician_id, stage FROM MaintenanceRequest WHERE scheduled_date LIKE '2025-12-27%'")
        reqs = cursor.fetchall()
        for r in reqs:
            print(f"Request {r['id']}: '{r['subject']}' on {r['scheduled_date']} | Team: {r['team_id']} | Tech: {r['technician_id']} | Stage: {r['stage']}")

        if not reqs:
            print("No requests found for 2025-12-27.")
            # Check generally
            cursor.execute("SELECT id, subject, scheduled_date FROM MaintenanceRequest ORDER BY id DESC LIMIT 5")
            print("Latest 5 requests:", cursor.fetchall())

        print("\n--- 2. Check Technician 'kunj' ---")
        cursor.execute("SELECT u.id as user_id, u.role, t.id as tech_id, t.team_id, t.name FROM User u JOIN Technician t ON u.id = t.user_id WHERE u.email LIKE '%kunj%' OR t.name LIKE '%kunj%'")
        tech = cursor.fetchone()
        print("Technician:", tech)
        
        if tech and reqs:
            print("\n--- 3. Visibility Check ---")
            r = reqs[0]
            if tech['team_id'] == r['team_id']:
                print(f"MATCH: Tech Team ({tech['team_id']}) matches Request Team ({r['team_id']})")
            elif tech['tech_id'] == r['technician_id']:
                print(f"MATCH: Tech ({tech['tech_id']}) is assigned personally")
            else:
                 print(f"MISMATCH: Tech Team {tech['team_id']} != Request Team {r['team_id']} AND Tech {tech['tech_id']} != Assg {r['technician_id']}")
                 if tech['team_id'] is None:
                     print("Tech has NO TEAM. Should see ALL (Global View).")

if __name__ == '__main__':
    check_visibility()
