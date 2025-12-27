from app import app
from db import get_db

def seed_equipment():
    with app.app_context():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # Ensure Alpha Team exists (it should from seed_tech, but let's be safe)
        cursor.execute("SELECT id FROM MaintenanceTeam WHERE team_name = 'Alpha Team'")
        team = cursor.fetchone()
        if not team:
            cursor.execute("INSERT INTO MaintenanceTeam (team_name) VALUES ('Alpha Team')")
            team_id = cursor.lastrowid
        else:
            team_id = team['id']
            
        equipment_data = [
            ('Office PC-01', 'PC-001', 'Computer', 'IT', 'Office'),
            ('Lathe Machine X1', 'MCH-001', 'Machine', 'Production', 'Shop Floor'),
            ('Delivery Van 05', 'VEH-005', 'Vehicle', 'Logistics', 'Garage')
        ]
        
        for name, serial, eq_type, dept, loc in equipment_data:
            # Check if exists
            cursor.execute("SELECT id FROM Equipment WHERE serial_number = %s", (serial,))
            if cursor.fetchone():
                print(f"Skipping {name} (already exists)")
                continue

            cursor.execute("""
                INSERT INTO Equipment (name, serial_number, equipment_type, department, location, maintenance_team_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, serial, eq_type, dept, loc, team_id))
            print(f"Created {name}")
            
        db.commit()
        cursor.close()
        print("Equipment seeding complete.")

if __name__ == '__main__':
    seed_equipment()
