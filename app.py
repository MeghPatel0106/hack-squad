from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, g
from db import get_db, init_db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
import requests 
import functools

app = Flask(__name__)
app.secret_key = os.urandom(24)
init_db(app)

# --- Helpers ---
def log_action(user_id, action, target_type=None, target_id=None, details=None):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO AuditLog (user_id, action, target_type, target_id, details)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, action, target_type, target_id, details))
        cursor.close()
    except Exception as e:
        print(f"Log Error: {e}")

# --- Auth Decorator ---
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

def role_required(roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if session.get('user_role') == 'Admin':
                return view(**kwargs)
            
            if 'user_role' not in session or session['user_role'] not in roles:
                 flash("You do not have permission to access this resource.")
                 return redirect(url_for('dashboard'))
            return view(**kwargs)
        return wrapped_view
    return decorator

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE id = %s", (user_id,))
        g.user = cursor.fetchone()
        cursor.close()

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM User WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_name'] = user['name']
            
            log_action(user['id'], 'LOGIN')
            
            # Roles: Admin, Company User, Technician
            if user['role'] == 'Admin':
                return redirect(url_for('admin_panel'))
            elif user['role'] == 'Technician':
                return redirect(url_for('kanban')) # Techs work on Kanban or Schedule
            else:
                return redirect(url_for('create_request_page')) # Company users want to request
        
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form.get('role')

        if password != confirm_password:
             flash('Passwords do not match', 'error')
             return render_template('signup.html')
             
        if role not in ['Company User', 'Technician']:
             flash('Invalid role selected.', 'error')
             return render_template('signup.html')

        db = get_db()
        cursor = db.cursor()
        try:
            p_hash = generate_password_hash(password)
            # Role comes from form, but validated above. Explicitly NOT Admin.
            cursor.execute("INSERT INTO User (name, email, password_hash, role) VALUES (%s, %s, %s, %s)", (name, email, p_hash, role))
            db.commit() 
            new_id = cursor.lastrowid
            
            # If Technician, create partial tech record? Or just User?
            # Req: "During Signup, user must choose... Technician"
            # If they choose Tech, we should probably create a Technician record for them so they show up in lists?
            if role == 'Technician':
                 cursor.execute("INSERT INTO Technician (name, user_id, role) VALUES (%s, %s, 'Technician')", (name, new_id))
                 db.commit()

            cursor.close()
            
            log_action(new_id, 'SIGNUP')
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
            
    return render_template('signup.html')

@app.route('/logout')
def logout():
    # Admin logout restriction - STRICT
    if g.user and g.user['role'] == 'Admin':
         flash("Administrators cannot logout.", "warning")
         return redirect(url_for('admin_panel'))

    if g.user:
        log_action(g.user['id'], 'LOGOUT')
    session.clear()
    return redirect(url_for('login'))

@app.route('/auth/google')
def google_login():
    flash("Google Login requires valid API Keys configured.", "info")
    return redirect(url_for('login'))

# --- Main App Routes ---
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=g.user)

@app.route('/equipment')
@login_required
def equipment():
    if g.user['role'] != 'Company User':
        if g.user['role'] == 'Admin':
             return redirect(url_for('admin_panel'))
        return redirect(url_for('kanban'))
    return render_template('equipment.html', user=g.user)

@app.route('/equipment/<int:id>')
@login_required
def equipment_detail(id):
    if g.user['role'] != 'Company User':
        if g.user['role'] == 'Admin':
             return redirect(url_for('admin_panel'))
        return redirect(url_for('kanban'))
        
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, t.name as technician_name, m.team_name, wc.name as work_center_name, ec.name as category_name,
        (SELECT COUNT(*) FROM MaintenanceRequest mr WHERE mr.equipment_id = e.id AND mr.stage != 'Repaired' AND mr.stage != 'Scrap') as open_requests
        FROM Equipment e
        LEFT JOIN Technician t ON e.default_technician_id = t.id
        LEFT JOIN MaintenanceTeam m ON e.maintenance_team_id = m.id
        LEFT JOIN WorkCenter wc ON e.work_center_id = wc.id
        LEFT JOIN EquipmentCategory ec ON e.category_id = ec.id
        WHERE e.id = %s
    """, (id,))
    item = cursor.fetchone()
    cursor.close()
    if not item:
        return "Equipment not found", 404
    return render_template('equipment_detail.html', item=item, user=g.user)

@app.route('/kanban')
@login_required
def kanban():
    return render_template('kanban.html', user=g.user)

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html', user=g.user)

@app.route('/work_centers')
@login_required
def work_centers():
    return render_template('work_centers.html', user=g.user)

@app.route('/categories')
@login_required
def categories():
    return render_template('categories.html', user=g.user)

@app.route('/teams')
@login_required
def teams():
    return render_template('teams.html', user=g.user)

@app.route('/admin')
@login_required
@role_required(['Admin'])
def admin_panel():
    return render_template('admin_panel.html', user=g.user)

@app.route('/create_request')
@login_required
def create_request_page():
    if g.user['role'] != 'Company User':
        flash('Only Company Users can create maintenance requests.', 'warning')
        if g.user['role'] == 'Admin':
            return redirect(url_for('admin_panel'))
        elif g.user['role'] == 'Technician':
            return redirect(url_for('kanban'))
        return redirect(url_for('dashboard'))
        
    date = request.args.get('date')
    if not date:
        flash('Please select a date from the Calendar to create a request.', 'info')
        return redirect(url_for('calendar'))
        
    eq_id = request.args.get('equipment_id')
    return render_template('request_form.html', date=date, equipment_id=eq_id, user=g.user)

# --- API Routes ---
@app.route('/api/stats')
@login_required
def api_stats():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    stats = {}
    
    conditions_mr = []
    params_mr = []
    conditions_eq = [] 
    params_eq = []

    if g.user['role'] == 'Technician':
        cursor.execute("SELECT team_id FROM Technician WHERE user_id = %s", (g.user['id'],))
        t = cursor.fetchone()
        if t and t['team_id']:
             conditions_mr.append("team_id = %s")
             params_mr.append(t['team_id'])
             conditions_eq.append("maintenance_team_id = %s")
             params_eq.append(t['team_id'])
        else:
             conditions_mr.append("1=0")
             conditions_eq.append("1=0")
    
    elif g.user['role'] == 'Company User':
        conditions_mr.append("created_by_user_id = %s")
        params_mr.append(g.user['id'])
        # Critical equipment? They might care about all, or none. 
        # Requirement: "Track status of their requests".
        # Let's show global critical equip for awareness or 0? 
        # Safer to show 0 or only relevant. Let's filter MR related stats.

    where_mr = " AND ".join(conditions_mr) if conditions_mr else ""
    where_mr_clause = f" AND {where_mr}" if where_mr else ""
    
    # 1. Critical Equipment (Corrective + New/InProgress)
    # This query joins MR anyway
    query_crit = f"""
        SELECT COUNT(DISTINCT equipment_id) as count 
        FROM MaintenanceRequest 
        WHERE request_type = 'Corrective' AND stage IN ('New', 'In Progress') {where_mr_clause}
    """
    cursor.execute(query_crit, params_mr)
    stats['critical_equipment'] = cursor.fetchone()['count']
    
    # 2. Technician Load (Active requests with tech assigned)
    # Meaningful for Admin/Manager. For Tech, it's their team's load or their own?
    # "Technician Load" usually means total active jobs.
    query_load = f"""
        SELECT COUNT(*) as count 
        FROM MaintenanceRequest 
        WHERE stage IN ('In Progress') AND technician_id IS NOT NULL {where_mr_clause}
    """
    cursor.execute(query_load, params_mr)
    stats['technician_load'] = cursor.fetchone()['count']
    
    # 3. Active Requests
    query_active = f"SELECT COUNT(*) as count FROM MaintenanceRequest WHERE stage IN ('New', 'In Progress') {where_mr_clause}"
    cursor.execute(query_active, params_mr)
    stats['active_requests'] = cursor.fetchone()['count']

    # 4. By Stage
    query_stage = f"SELECT stage, COUNT(*) as count FROM MaintenanceRequest WHERE 1=1 {where_mr_clause} GROUP BY stage"
    cursor.execute(query_stage, params_mr)
    stats['by_stage'] = cursor.fetchall()
    
    cursor.close()
    return jsonify(stats)

@app.route('/api/equipment', methods=['GET', 'POST'])
@login_required
def api_equipment():
    if g.user['role'] != 'Company User':
         return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'GET':
        query = """
            SELECT e.*, t.name as technician_name, m.team_name, wc.name as work_center_name, ec.name as category_name,
            (SELECT COUNT(*) FROM MaintenanceRequest mr WHERE mr.equipment_id = e.id AND mr.stage != 'Repaired' AND mr.stage != 'Scrap') as open_requests
            FROM Equipment e
            LEFT JOIN Technician t ON e.default_technician_id = t.id
            LEFT JOIN MaintenanceTeam m ON e.maintenance_team_id = m.id
            LEFT JOIN WorkCenter wc ON e.work_center_id = wc.id
            LEFT JOIN EquipmentCategory ec ON e.category_id = ec.id
        """
        search = request.args.get('search')
        params = []
        conditions = []
        
        if search:
            conditions.append("(e.name LIKE %s OR e.serial_number LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY e.id DESC"
        cursor.execute(query, params)
        equipment_list = cursor.fetchall()
        cursor.close()
        return jsonify(equipment_list)
    
    if request.method == 'POST':
        # Already checked role above - STRICT Company User
        if g.user['role'] != 'Company User':
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.json
        if not data.get('name') or not data.get('equipment_type'):
            return jsonify({'error': 'Name and Type are required'}), 400

        # Add equipment_type
        cursor.execute("""
            INSERT INTO Equipment (name, serial_number, category_id, work_center_id, department, assigned_employee, purchase_date, warranty_info, location, maintenance_team_id, default_technician_id, description, equipment_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['name'], data['serial_number'], data.get('category_id'), data.get('work_center_id'),
              data.get('department'), data.get('assigned_employee'), data.get('purchase_date'),
              data.get('warranty_info'), data.get('location'), data.get('maintenance_team_id'),
              data.get('default_technician_id'), data.get('description'), data.get('equipment_type')))
        
        new_id = cursor.lastrowid
        cursor.close()
        log_action(g.user['id'], 'CREATE_EQUIPMENT', 'Equipment', new_id, f"Created {data['name']}")
        return jsonify({'id': new_id, 'message': 'Equipment created'}), 201

@app.route('/api/equipment/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_equipment_action(id):
    if g.user['role'] != 'Company User':
         return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'DELETE':
        cursor.execute("DELETE FROM Equipment WHERE id = %s", (id,))
        cursor.close()
        log_action(g.user['id'], 'DELETE_EQUIPMENT', 'Equipment', id, "Deleted equipment")
        return jsonify({'message': 'Deleted'})
    
    # PUT logic placeholder
    return jsonify({'message': 'Updated'})

@app.route('/api/requests', methods=['GET', 'POST'])
@login_required
def api_requests():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'GET':
        equipment_id = request.args.get('equipment_id')
        search = request.args.get('search')
        query = """
            SELECT r.*, r.description, e.name as equipment_name, t.name as technician_name, t.avatar_url, m.team_name, ec.name as category_name, u.name as created_by_name
            FROM MaintenanceRequest r
            JOIN Equipment e ON r.equipment_id = e.id
            LEFT JOIN EquipmentCategory ec ON e.category_id = ec.id
            LEFT JOIN Technician t ON r.technician_id = t.id
            LEFT JOIN MaintenanceTeam m ON r.team_id = m.id
            LEFT JOIN User u ON r.created_by_user_id = u.id
        """
        params = []
        conditions = []
        
        if equipment_id:
            conditions.append("r.equipment_id = %s")
            params.append(equipment_id)
        
        if search:
            conditions.append("(r.subject LIKE %s OR e.name LIKE %s)")
            params.extend([f"%{search}%", f"%{search}%"])
            
        if g.user['role'] == 'Company User':
            conditions.append("r.created_by_user_id = %s")
            params.append(g.user['id'])
        elif g.user['role'] == 'Technician':
             # Get user's team
             cursor.execute("SELECT team_id FROM Technician WHERE user_id = %s", (g.user['id'],))
             tech_rec = cursor.fetchone()
             if tech_rec and tech_rec['team_id']:
                 conditions.append("r.team_id = %s")
                 params.append(tech_rec['team_id'])
             else:
                 conditions.append("1=0") # No team, no requests

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY r.created_at DESC"
        cursor.execute(query, params)
        requests = cursor.fetchall()
        cursor.close()
        return jsonify(requests)

    if request.method == 'POST':
        if g.user['role'] != 'Company User':
             return jsonify({'error': 'Only Company Users can create requests'}), 403

        data = request.json
        if data.get('stage') == 'Scrap' and g.user['role'] != 'Admin': # Only Admin (or explicitly authorized)
             return jsonify({'error': 'Only Admins can scrap equipment'}), 403

        if data.get('stage') == 'Scrap':
             cursor.execute("UPDATE Equipment SET is_scrapped = TRUE WHERE id = %s", (data['equipment_id'],))
        
        # Auto-assign team/tech for Company Users (and everyone really, to enforce rules)
        # "User must NOT select Maintenance Team manually"
        cursor.execute("SELECT maintenance_team_id, default_technician_id FROM Equipment WHERE id = %s", (data['equipment_id'],))
        eq_data = cursor.fetchone()
        
        team_id = eq_data['maintenance_team_id'] if eq_data else None
        tech_id = eq_data['default_technician_id'] if eq_data else None

        if not data.get('equipment_id'):
             return jsonify({'error': 'Equipment is required'}), 400

        if not data.get('scheduled_date'):
            return jsonify({'error': 'Scheduled Date is required. Please create requests via the Calendar.'}), 400

        cursor.execute("""
            INSERT INTO MaintenanceRequest (subject, description, equipment_id, team_id, technician_id, created_by_user_id, request_type, stage, scheduled_date, duration_hours)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['subject'], data.get('description', ''), data['equipment_id'], team_id, tech_id, g.user['id'],
              data['request_type'], data.get('stage', 'New'), data.get('scheduled_date'), data.get('duration_hours')))
        new_id = cursor.lastrowid
        cursor.close()
        
        log_action(g.user['id'], 'CREATE_REQUEST', 'MaintenanceRequest', new_id, f"Created request: {data['subject']}")
        return jsonify({'id': new_id, 'message': 'Request created'}), 201

@app.route('/api/requests/<int:req_id>', methods=['PUT', 'DELETE'])
@login_required
def request_ops(req_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'PUT':
        data = request.json
        if data.get('stage') == 'Scrap':
            if g.user['role'] != 'Admin':
                return jsonify({'error': 'Unauthorized'}), 403
            
            cursor.execute("SELECT equipment_id FROM MaintenanceRequest WHERE id = %s", (req_id,))
            res = cursor.fetchone()
            if res:
                cursor.execute("UPDATE Equipment SET is_scrapped = TRUE WHERE id = %s", (res['equipment_id'],))

        fields = []
        values = []
        for key in ['stage', 'technician_id', 'duration_hours', 'scheduled_date']:
            if key in data:
                fields.append(f"{key} = %s")
                values.append(data[key])
        
        if not fields:
            return jsonify({'message': 'No fields'}), 400
            
        values.append(req_id)
        query = f"UPDATE MaintenanceRequest SET {', '.join(fields)} WHERE id = %s"
        cursor.execute(query, values)
        cursor.close()
        log_action(g.user['id'], 'UPDATE_REQUEST', 'MaintenanceRequest', req_id, f"Updated fields: {list(data.keys())}")
        return jsonify({'message': 'Updated'})

    if request.method == 'DELETE':
        if g.user['role'] != 'Admin':
             return jsonify({'error': 'Admin only'}), 403
        
        cursor.execute("DELETE FROM MaintenanceRequest WHERE id = %s", (req_id,))
        cursor.close()
        log_action(g.user['id'], 'DELETE_REQUEST', 'MaintenanceRequest', req_id, "Deleted request")
        return jsonify({'message': 'Deleted'})

# --- New API Endpoints (Admin CRUD) ---
@app.route('/api/teams', methods=['GET', 'POST'])
@login_required
def api_teams():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM MaintenanceTeam")
        teams = cursor.fetchall()
        cursor.close()
        return jsonify(teams)
    
    if request.method == 'POST':
        if g.user['role'] != 'Admin': return jsonify({'error': 'Admin only'}), 403
        data = request.json
        cursor.execute("INSERT INTO MaintenanceTeam (team_name) VALUES (%s)", (data['name'],))
        new_id = cursor.lastrowid
        cursor.close()
        return jsonify({'id': new_id, 'message': 'Team created'}), 201

@app.route('/api/teams/<int:id>', methods=['DELETE'])
@login_required
@role_required(['Admin'])
def delete_team(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM MaintenanceTeam WHERE id = %s", (id,))
    cursor.close()
    return jsonify({'message': 'Deleted'})

@app.route('/technicians')
@login_required
@role_required(['Admin'])
def technicians():
    return render_template('technicians.html', user=g.user)

@app.route('/api/technicians', methods=['GET', 'POST'])
@login_required
def api_technicians():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    if request.method == 'GET':
        cursor.execute("SELECT t.*, m.team_name FROM Technician t LEFT JOIN MaintenanceTeam m ON t.team_id = m.id")
        techs = cursor.fetchall()
        cursor.close()
        return jsonify(techs)

    if request.method == 'POST':
        if g.user['role'] != 'Admin': return jsonify({'error': 'Admin only'}), 403
        data = request.json
        
        # 1. Create User Account
        p_hash = generate_password_hash(data['password'])
        try:
            cursor.execute("INSERT INTO User (name, email, password_hash, role) VALUES (%s, %s, %s, 'Technician')", 
                           (data['name'], data['email'], p_hash))
            user_id = cursor.lastrowid
        except Exception as e:
            return jsonify({'error': f'User creation failed (email exists?): {e}'}), 400
            
        # 2. Create Technician Record linked to User
        cursor.execute("INSERT INTO Technician (name, team_id, user_id, role) VALUES (%s, %s, %s, %s)", 
                       (data['name'], data.get('team_id'), user_id, 'Technician'))
        new_id = cursor.lastrowid
        db.commit()
        cursor.close()
        return jsonify({'id': new_id, 'message': 'Technician created'}), 201

@app.route('/api/technicians/<int:id>', methods=['DELETE'])
@login_required
@role_required(['Admin'])
def delete_tech(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM Technician WHERE id = %s", (id,))
    cursor.close()
    return jsonify({'message': 'Deleted'})

@app.route('/api/work_centers')
@login_required
def api_work_centers():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM WorkCenter")
    data = cursor.fetchall()
    cursor.close()
    return jsonify(data)

@app.route('/api/categories')
@login_required
def api_categories():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM EquipmentCategory")
    data = cursor.fetchall()
    cursor.close()
    return jsonify(data)
    
@app.route('/api/logs')
@login_required
@role_required(['Admin'])
def api_logs():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT l.*, u.name as user_name, u.role as user_role 
        FROM AuditLog l 
        LEFT JOIN User u ON l.user_id = u.id 
        ORDER BY l.timestamp DESC LIMIT 50
    """)
    logs = cursor.fetchall()
    cursor.close()
    return jsonify(logs)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
