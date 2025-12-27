-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS AuditLog;
DROP TABLE IF EXISTS MaintenanceRequest;
DROP TABLE IF EXISTS Equipment;
DROP TABLE IF EXISTS WorkCenter;
DROP TABLE IF EXISTS EquipmentCategory;
DROP TABLE IF EXISTS Technician;
DROP TABLE IF EXISTS MaintenanceTeam;
DROP TABLE IF EXISTS User;

-- Create User table for Auth
CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Technician', 'Company User') DEFAULT 'Company User',
    google_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create MaintenanceTeam table
CREATE TABLE MaintenanceTeam (
    id INT AUTO_INCREMENT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE
);

-- Create Technician table
CREATE TABLE Technician (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    team_id INT,
    user_id INT UNIQUE, 
    role VARCHAR(100) DEFAULT 'Technician',
    avatar_url VARCHAR(255),
    FOREIGN KEY (team_id) REFERENCES MaintenanceTeam(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE SET NULL
);

-- Create WorkCenter Table
CREATE TABLE WorkCenter (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    tag VARCHAR(50),
    cost_per_hour DECIMAL(10, 2),
    capacity DECIMAL(10, 2),
    efficiency DECIMAL(5, 2),
    oee_target DECIMAL(5, 2)
);

-- Create EquipmentCategory Table
CREATE TABLE EquipmentCategory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Create Equipment table
CREATE TABLE Equipment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) UNIQUE NOT NULL,
    category_id INT,
    work_center_id INT,
    department VARCHAR(100),
    assigned_employee VARCHAR(100),
    purchase_date DATE,
    warranty_info TEXT,
    location VARCHAR(100),
    maintenance_team_id INT,
    default_technician_id INT,
    is_scrapped BOOLEAN DEFAULT FALSE,
    description TEXT,
    equipment_type ENUM('Machine', 'Vehicle', 'Computer') DEFAULT 'Machine',
    FOREIGN KEY (category_id) REFERENCES EquipmentCategory(id) ON DELETE SET NULL,
    FOREIGN KEY (work_center_id) REFERENCES WorkCenter(id) ON DELETE SET NULL,
    FOREIGN KEY (maintenance_team_id) REFERENCES MaintenanceTeam(id) ON DELETE SET NULL,
    FOREIGN KEY (default_technician_id) REFERENCES Technician(id) ON DELETE SET NULL
);

-- Create MaintenanceRequest table
CREATE TABLE MaintenanceRequest (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(200) NOT NULL,
    equipment_id INT NOT NULL,
    team_id INT,
    technician_id INT,
    created_by_user_id INT,
    request_type ENUM('Corrective', 'Preventive') NOT NULL,
    stage ENUM('New', 'In Progress', 'Repaired', 'Scrap') DEFAULT 'New',
    scheduled_date DATE,
    duration_hours DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES Equipment(id) ON DELETE CASCADE,
    FOREIGN KEY (team_id) REFERENCES MaintenanceTeam(id) ON DELETE SET NULL,
    FOREIGN KEY (technician_id) REFERENCES Technician(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES User(id) ON DELETE SET NULL
);

-- Create AuditLog table
CREATE TABLE AuditLog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(255) NOT NULL,
    target_type VARCHAR(50),
    target_id INT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE SET NULL
);
