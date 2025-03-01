## Project Description

AI-powered chatbot to generate SQL queries and perform CRUD operations over a PostgreSQL database. Powered by an OpenAI model, the system enables seamless data management through advanced UI features, enhancing user experience and efficiency.

## Features

SQL Query Generation: Supports CREATE, SELECT, INSERT, and DELETE operations.

User Confirmation: Queries affecting the database require confirmation before execution.

Certainty Measure: Indicates the trustworthiness of generated queries.

Customizable Settings: Adjust model, temperature, max tokens, session budget, and validation threshold.

Database Viewer: Displays the database and its schema.

Session Cost Tracking: Monitors usage with budget limit warnings.

3M Analyzer (Min-Max-Mean): Calculates these metrics for any numeric field.

Smart Team Builder: Suggests required profiles, skills, and matches employees based on project needs.

Quick Viz: Generates graphs based on predefined queries for instant data visualization.

Chat History: Stores previous interactions for reference and continuity.


## Project Structure

![image](https://github.com/user-attachments/assets/3ae4ac97-7516-43ac-b136-6f34ef583f03)




## Setting Up Supabase with Docker

Follow these steps to set up Supabase using Docker and run the chatbot application.

1. Clone the Supabase Repository

    > git clone --depth 1 https://github.com/supabase/supabase

2. Navigate to the Docker Directory

    > cd supabase/docker

3. Copy the Example Environment Variables

    > cp .env.example .env

Modify the .env file if needed, especially updating SUPABASE_PUBLIC_URL and API_EXTERNAL_URL to your domain or IP address instead of http://localhost:8000.

4. Pull the Latest Docker Images

    > docker compose pull

5. Start the Supabase Services

    > docker compose up -d

After the services start, verify their status:

    > docker compose ps

All services should show a status of running (healthy).

6. Accessing Supabase Studio

Supabase Studio can be accessed via the API gateway on port 8000:

    Localhost: http://localhost:8000

Custom Domain/IP: Replace localhost with your domain or IP.

Login credentials are stored in the .env file:

Username: DASHBOARD_USERNAME

Password: DASHBOARD_PASSWORD

## Setting Up the Chatbot

1. Clone the Chatbot Repository

    > git clone https://git.piterion.com/fatma.hamza/employee_management_chatbot.git
    
    > cd project_folder

2. Create and Activate a Virtual Environment

    > python3 -m venv venv
    
    > source venv/bin/activate  

3. Run Initial Setup and Install Requirements

    > chmod +x setup.sh
    
    > ./setup.sh

### Database Setup

1. Connect to PostgreSQL Using Docker

    > docker exec -it supabase-db psql -U postgres -d postgres

This connects you to the default database (postgres).

2. Create a New Database

    > CREATE DATABASE test_db;

3. Create Tables

    > psql -h 172.20.0.4 -U postgres -d test_db -f create_tab.sql

4. Populate the Database

    > psql -h 172.20.0.4 -U postgres -d test_db -f populate_db.sql

5. Verify Database Setup

Switch to test_db:  \c test_db

List tables:   \dt

Display table fields:  \d table_name

### Running the Chatbot

Start the chatbot application:

    > python3 run.py

#### Testing the Backend

Use POST request to test functionality with postman:

> Endpoint: http://127.0.0.1:5000/crud

Body (JSON format):

{
  "message": "Type question here?"
}



> Endpoint: http://127.0.0.1:5000/execute

Body (JSON format):
{
  "generated_query": "ADD YOUR QUERY HERE",
  
  "confirm": true
}


> Endpoint: http://127.0.0.1:5000/build_team

Body (JSON format):
{
  "description": "ADD YOUR PROJECT DESCRIPTION HERE"
}



Send the request and check the response

#### User Interface

Accessible on http://localhost:8501/
