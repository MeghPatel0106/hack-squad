# MechCare - Maintenance Management System

MechCare is a premium maintenance management web application built with Python Flask, MySQL, and Vanilla JavaScript.

## Features
- **Dashboard**: Real-time KPIs and charts.
- **Authentication**: Role-based login (Manager, Technician, User) & Google Auth support.
- **Responsive Design**: Works on Desktop, Tablet, and Mobile.
- **Kanban Board**: Drag-and-drop workflow.
- **Equipment Inventory**: Asset tracking with smart maintenance alerts.

## Prerequisites
- Python 3.x
- MySQL Server

## Setup Instructions

### 1. Database Setup
1.  Create database:
    ```sql
    CREATE DATABASE mechcare_db;
    ```
2.  Import schema and seeds:
    ```bash
    mysql -u root -p mechcare_db < schema.sql
    mysql -u root -p mechcare_db < seeds.sql
    ```

### 2. Application Setup
1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Configure `.env`:
    ```bash
    cp .env.example .env
    # Edit .env with DB credentials
    ```
3.  **Seed Users** (Crucial for Auth):
    ```bash
    python seed_users.py
    ```
    *This creates: manager@mechcare.com, user@mechcare.com etc. with password 'password'.*

### 3. Running the App
1.  Start the Flask server:
    ```bash
    python app.py
    ```
2.  Navigate to `http://127.0.0.1:8000`
3.  Login with:
    - **Email**: `manager@mechcare.com`
    - **Password**: `password`

## Security Notes
- Passwords are hashed using PBKDF2/SHA256.
- Routes are protected via `@login_required`.
- Input is sanitized via parameterized SQL queries.
