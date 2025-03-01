-- test database schema


CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Employees Table
CREATE TABLE employees (
    employee_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    address TEXT,
    department TEXT,
    role TEXT,
    salary DECIMAL,
    hire_date DATE
);

-- Projects Table
CREATE TABLE projects (
    proj_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proj_name TEXT NOT NULL,
    description TEXT,
    manager UUID,  -- Foreign key to the employees table (project manager)
    start_date DATE,
    end_date DATE,
    budget DECIMAL,
    nb_members INT,
    FOREIGN KEY (manager) REFERENCES employees(employee_id)  -- Link manager to an employee
);

-- Tasks Table (Links employees to projects)
CREATE TABLE tasks (
    task_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL,  -- Foreign key to employees table
    proj_id UUID NOT NULL,      -- Foreign key to projects table
    description TEXT NOT NULL,
    work_hours INT DEFAULT 0, -- Work hours invested in this specific task
    validation BOOLEAN DEFAULT FALSE,  -- Default to unvalidated unless complete by assignee and approved by manager
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (proj_id) REFERENCES projects(proj_id)
);

-- Work and Vacation Table
CREATE TABLE work_and_vacation (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    month_year TEXT NOT NULL,  -- Format 'YYYY-MM'
    employee_id UUID NOT NULL,  -- Foreign key to employees table
    regular_hours INT DEFAULT 240,  -- Default to 240 regular hours
    overtime_hours INT DEFAULT 0,  -- Default to 0 overtime hours
    remaining_vacation INT DEFAULT 0,
    remaining_sick_leave INT DEFAULT 0,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- Skills and availibility
CREATE TABLE skills (
    skill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL,
    skill_name TEXT NOT NULL,
    proficiency_level TEXT CHECK (proficiency_level IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
    years_of_experience INTEGER CHECK (years_of_experience >= 0),
    availability BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
);

