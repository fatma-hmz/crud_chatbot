-- Insert employees (IT and Sales staff)
BEGIN;
INSERT INTO employees (firstname, lastname, email, phone, address, department, role, salary, hire_date)
VALUES
('John', 'Doe', 'john.doe@piterion.com', '123-456-7890', '3500 W 3rd St, Los Angeles, CA 90020', 'IT', 'Software Engineer', 60000, '2020-01-10'),
('Jane', 'Smith', 'jane.smith@piterion.com', '234-567-8901', '8700 W 3rd St, Beverly Hills, CA 90210', 'Sales', 'Sales Manager', 75000, '2018-05-20'),
('Alice', 'Johnson', 'alice.johnson@piterion.com', '345-678-9012', '5500 Wilshire Blvd, Los Angeles, CA 90036', 'IT', 'Data Analyst', 55000, '2021-09-15'),
('Bob', 'Williams', 'bob.williams@piterion.com', '456-789-0123', '123 S Figueroa St, Los Angeles, CA 90017', 'Sales', 'Sales Associate', 45000, '2022-03-01'),
('David', 'Brown', 'david.brown@piterion.com', '567-890-1234', '1234 Sunset Blvd, Los Angeles, CA 90026', 'IT', 'DevOps Engineer', 65000, '2019-07-15'),
('Emily', 'Davis', 'emily.davis@piterion.com', '678-901-2345', '987 Ocean Ave, Santa Monica, CA 90401', 'HR', 'HR Specialist', 55000, '2020-11-05'),
('Michael', 'Wilson', 'michael.wilson@piterion.com', '789-012-3456', '456 Hollywood Blvd, Los Angeles, CA 90028', 'IT', 'Software Engineer', 62000, '2021-02-20'),
('Sarah', 'Martinez', 'sarah.martinez@piterion.com', '890-123-4567', '765 Westwood Blvd, Los Angeles, CA 90024', 'Sales', 'Account Manager', 58000, '2022-06-10');

-- Insert projects
INSERT INTO projects (proj_name, description, manager, start_date, end_date, budget, nb_members)
VALUES
('Project A', 'An IT infrastructure upgrade project', (SELECT employee_id FROM employees WHERE email = 'john.doe@piterion.com'), '2023-01-01', '2023-06-30', 50000, 4),
('Project B', 'Sales campaign for new product launch', (SELECT employee_id FROM employees WHERE email = 'jane.smith@piterion.com'), '2023-02-01', '2023-08-30', 30000, 3),
('Project C', 'Cloud migration project for enterprise applications', (SELECT employee_id FROM employees WHERE email = 'david.brown@piterion.com'), '2023-03-01', '2023-09-30', 70000, 5),
('Project D', 'Company-wide HR digital transformation', (SELECT employee_id FROM employees WHERE email = 'emily.davis@piterion.com'), '2023-04-15', '2023-12-31', 40000, 4);

-- Insert tasks (linking employees to projects)
INSERT INTO tasks (employee_id, proj_id, description, work_hours, validation)
VALUES
((SELECT employee_id FROM employees WHERE email = 'john.doe@piterion.com'), (SELECT proj_id FROM projects WHERE proj_name = 'Project A'), 'Upgrade network infrastructure', 160, TRUE),
((SELECT employee_id FROM employees WHERE email = 'alice.johnson@piterion.com'), (SELECT proj_id FROM projects WHERE proj_name = 'Project A'), 'Analyze network performance', 120, FALSE),
((SELECT employee_id FROM employees WHERE email = 'jane.smith@piterion.com'), (SELECT proj_id FROM projects WHERE proj_name = 'Project B'), 'Plan sales strategy', 100, TRUE),
((SELECT employee_id FROM employees WHERE email = 'bob.williams@piterion.com'), (SELECT proj_id FROM projects WHERE proj_name = 'Project B'), 'Execute sales campaign', 150, FALSE),
((SELECT employee_id FROM employees WHERE email = 'david.brown@piterion.com'), (SELECT proj_id FROM projects WHERE proj_name = 'Project C'), 'Set up cloud infrastructure', 180, TRUE),
((SELECT employee_id FROM employees WHERE email = 'michael.wilson@piterion.com'), (SELECT proj_id FROM projects WHERE proj_name = 'Project C'), 'Develop cloud automation scripts', 160, FALSE),
((SELECT employee_id FROM employees WHERE email = 'emily.davis@piterion.com'), (SELECT proj_id FROM projects WHERE proj_name = 'Project D'), 'Implement HRMS system', 140, TRUE),
((SELECT employee_id FROM employees WHERE email = 'sarah.martinez@piterion.com'), (SELECT proj_id FROM projects WHERE proj_name = 'Project D'), 'Manage change communication', 130, FALSE);

-- Insert work and vacation records
INSERT INTO work_and_vacation (month_year, employee_id, regular_hours, overtime_hours, remaining_vacation, remaining_sick_leave)
VALUES
('2023-01', (SELECT employee_id FROM employees WHERE email = 'john.doe@piterion.com'), 240, 10, 5, 2, TRUE),
('2023-01', (SELECT employee_id FROM employees WHERE email = 'jane.smith@piterion.com'), 240, 8, 4, 1, TRUE),
('2023-02', (SELECT employee_id FROM employees WHERE email = 'alice.johnson@piterion.com'), 240, 12, 6, 0, FALSE),
('2023-02', (SELECT employee_id FROM employees WHERE email = 'bob.williams@piterion.com'), 240, 5, 8, 3, TRUE),
('2023-03', (SELECT employee_id FROM employees WHERE email = 'david.brown@piterion.com'), 240, 15, 6, 2, TRUE),
('2023-03', (SELECT employee_id FROM employees WHERE email = 'michael.wilson@piterion.com'), 240, 10, 5, 1, TRUE),
('2023-04', (SELECT employee_id FROM employees WHERE email = 'emily.davis@piterion.com'), 240, 8, 7, 0, TRUE),
('2023-04', (SELECT employee_id FROM employees WHERE email = 'sarah.martinez@piterion.com'), 240, 6, 9, 3, TRUE);

-- Insert skills for employees
INSERT INTO skills (employee_id, skill_name, proficiency_level, years_of_experience, availability)
VALUES
((SELECT employee_id FROM employees WHERE email = 'john.doe@piterion.com'), 'Python', 'Expert', 5),
((SELECT employee_id FROM employees WHERE email = 'john.doe@piterion.com'), 'Network Security', 'Advanced', 4),
((SELECT employee_id FROM employees WHERE email = 'jane.smith@piterion.com'), 'Sales Strategy', 'Expert', 8),
((SELECT employee_id FROM employees WHERE email = 'jane.smith@piterion.com'), 'Negotiation', 'Advanced', 6),
((SELECT employee_id FROM employees WHERE email = 'alice.johnson@piterion.com'), 'Data Analysis', 'Expert', 4),
((SELECT employee_id FROM employees WHERE email = 'alice.johnson@piterion.com'), 'SQL', 'Advanced', 3),
((SELECT employee_id FROM employees WHERE email = 'bob.williams@piterion.com'), 'Customer Relations', 'Intermediate', 2),
((SELECT employee_id FROM employees WHERE email = 'bob.williams@piterion.com'), 'Marketing', 'Intermediate', 3),
((SELECT employee_id FROM employees WHERE email = 'david.brown@piterion.com'), 'Cloud Computing', 'Expert', 6),
((SELECT employee_id FROM employees WHERE email = 'david.brown@piterion.com'), 'DevOps', 'Advanced', 5),
((SELECT employee_id FROM employees WHERE email = 'michael.wilson@piterion.com'), 'Java', 'Expert', 4),
((SELECT employee_id FROM employees WHERE email = 'michael.wilson@piterion.com'), 'Kubernetes', 'Advanced', 3),
((SELECT employee_id FROM employees WHERE email = 'emily.davis@piterion.com'), 'HR Management', 'Expert', 7),
((SELECT employee_id FROM employees WHERE email = 'emily.davis@piterion.com'), 'Employee Relations', 'Advanced', 6),
((SELECT employee_id FROM employees WHERE email = 'sarah.martinez@piterion.com'), 'Sales', 'Advanced', 5),
((SELECT employee_id FROM employees WHERE email = 'sarah.martinez@piterion.com'), 'Public Speaking', 'Intermediate', 4);

COMMIT;

