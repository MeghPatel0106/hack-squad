from db import get_db, init_db
from werkzeug.security import generate_password_hash
import os
from flask import Flask

app = Flask(__name__)
# Mock config for script context
app.config['SECRET_KEY'] = 'dev' 

# Initialize DB connection manually since we are outside request context
# But db.py uses 'g' which needs app context
# So we wrap in app.context

def seed_users():
    with app.app_context():
        # Force init db connection
        # db.py get_db uses g.db
        
        db = get_db()
        cursor = db.cursor()

        # Create Users
        users = [
            ('System Administrator', 'admin@mechcare.com', 'password123', 'Admin'),
        ]
        
        print("Seeding Users...")
        for name, email, pwd, role in users:
            try:
                p_hash = generate_password_hash(pwd)
                cursor.execute("INSERT INTO User (name, email, password_hash, role) VALUES (%s, %s, %s, %s)", (name, email, p_hash, role))
                print(f"Created {role}: {email}")
            except Exception as e:
                print(f"Skipped {email}: {e}")
        
        db.commit() # Important for transaction
        cursor.close()
        print("Done.")

if __name__ == '__main__':
    seed_users()
