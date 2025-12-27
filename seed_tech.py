from app import app
from db import get_db
from werkzeug.security import generate_password_hash

def seed_tech():
    with app.app_context():
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        # 1. Create Team if not exists
        cursor.execute("SELECT id FROM MaintenanceTeam WHERE team_name = 'Alpha Team'")
        team = cursor.fetchone()
        if not team:
            cursor.execute("INSERT INTO MaintenanceTeam (team_name) VALUES ('Alpha Team')")
            team_id = cursor.lastrowid
            print("Created 'Alpha Team'")
        else:
            team_id = team['id']
            print("Found 'Alpha Team'")

        # 2. Create User
        email = 'tech@mechcare.com'
        cursor.execute("SELECT id FROM User WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            p_hash = generate_password_hash('password123')
            cursor.execute("INSERT INTO User (name, email, password_hash, role) VALUES (%s, %s, %s, 'Technician')", 
                           ('John Tech', email, p_hash))
            user_id = cursor.lastrowid
            print(f"Created User: {email} / password123")
            
            # 3. Create Technician linked to user
            cursor.execute("INSERT INTO Technician (name, team_id, user_id, role) VALUES (%s, %s, %s, 'Technician')", 
                           ('John Tech', team_id, user_id))
            print("Created Technician record linked to user")
            db.commit()
        else:
            print(f"User {email} already exists")

        cursor.close()

if __name__ == '__main__':
    seed_tech()
