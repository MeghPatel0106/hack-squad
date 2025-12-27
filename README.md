# MechCare – Maintenance Management System

MechCare is a full-stack maintenance management web application designed to simplify and organize equipment maintenance operations for companies.  
It provides a structured workflow for handling equipment repairs, preventive maintenance, technician assignments, and long-term asset tracking through a modern, role-based system.

The system is built using **Python (Flask)** for backend logic, **MySQL** for data storage, and **HTML, CSS, and JavaScript** for a responsive and interactive user interface.

---

## Project Vision

The main goal of MechCare is to eliminate manual maintenance tracking and replace it with a centralized digital system where:

- Every maintenance request is traceable  
- Every technician has a clear work schedule  
- Every equipment item has a complete service history  
- Every repair follows a controlled and transparent workflow  

This results in improved operational efficiency, reduced equipment downtime, and better decision-making for organizations.

---

## Core Features

### Role-Based System
MechCare uses a strict role-based architecture with three roles:
- **Administrator**
- **Company User**
- **Technician**

Each role has its own dashboard, permissions, and responsibilities.

---

### Calendar-Driven Maintenance Scheduling
All maintenance requests are created directly from the **Calendar**.  
Users select the date first, ensuring that all repair activities are fully scheduled and visible across the system.

Each scheduled repair appears on:
- Calendar view  
- Kanban workflow board  
- User request history  

---

### Preventive & Corrective Maintenance
The system supports two types of maintenance:

- **Preventive Maintenance** – Routine equipment inspection and servicing  
- **Corrective Maintenance** – Repairing broken or malfunctioning equipment  

This classification allows companies to reduce unexpected breakdowns and extend equipment lifespan.

---

### Intelligent Workflow Management
Maintenance requests move through the following controlled stages:

**New → In Progress → Repaired → Scrap**

Once a request reaches **Scrap**, the equipment is permanently marked as non-repairable and cannot re-enter the workflow.  
This prevents incorrect handling of damaged assets.

---

### Automatic Team & Technician Assignment
When a maintenance request is created, the system automatically assigns:
- The correct maintenance team  
- The appropriate technician  

Assignments are based on the equipment type and predefined department rules, eliminating manual errors.

---

### Technician Work Management
Technicians have access to:
- Their personal repair schedule  
- Assigned equipment details  
- Location information  
- Kanban board for task progress updates  

This ensures clear communication and efficient field operations.

---

### Equipment & Asset Tracking
MechCare manages multiple equipment categories such as:
- Machines  
- Vehicles  
- Computers  

Each equipment record includes location, assigned team, service history, and current status.

---

### Security & Permissions
All actions in the system are protected by backend role enforcement:
- Only company users can create requests  
- Only technicians can update repair stages  
- Only administrators manage teams and system configuration  

This guarantees data integrity and secure operations.

---

### Responsive Interface
The application works seamlessly across:
- Desktop  
- Tablet  
- Mobile  

allowing teams to operate from office, factory floor, or field locations.

---

## User Roles Overview

### Administrator
Controls system configuration, manages teams, technicians, and equipment assignments.

### Company User
Creates maintenance requests, schedules repairs, and monitors equipment condition.

### Technician
Executes assigned maintenance tasks and updates repair progress.

---

---

## Database Access (For Jury / Evaluation)

MechCare uses **MySQL** as the backend database.

For security reasons, database credentials and direct database access are **not shared** in this repository.  
Each evaluator is expected to configure the database **locally** on their own system.

### Database Setup Steps

1. Install and start **MySQL Server** on your system.

2. Create the database:
3. Import the database schema (if `schema.sql` is provided):
   mysql -u root -p mechcare_db < schema.sql

4. Update database connection details in the project configuration file
(such as `db.py` or `database.py`):
host = "localhost"
user = "root"
password = "Pme@010607"
database = "mechcare_db"


5. Run the application as described in the execution instructions.

### Evaluation Notes

- The system is designed to run with a **local MySQL database**
- No shared or remote database is required
- This approach ensures data security and independent evaluation

---


## Conclusion

MechCare transforms maintenance operations into a structured, transparent, and efficient digital process.  
It bridges communication between management, technicians, and equipment systems, creating a reliable platform for long-term operational success.
