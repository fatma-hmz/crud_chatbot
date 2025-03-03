import psycopg2
#from database.db_config import DB_CONFIG
import logging
import pandas as pd

from st_supabase_connection import SupabaseConnection
from supabase import create_client, Client


# Set up logging configuration
logging.basicConfig(level=logging.DEBUG,  
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])  

logger = logging.getLogger(__name__)



import streamlit as st

import psycopg2
from urllib.parse import quote_plus

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
        key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None



        
def execute_query(sql_query):
    """Executes a single SQL query."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        print("Executing...\n", sql_query)
        cur.execute(sql_query)
        conn.commit()  # Commit after each query
        print("Query executed successfully!")
        return {"success": True, "message": "Query executed successfully"}
    
    except Exception as e:
        conn.rollback()  # Rollback on failure
        return {"error": str(e), "message": f"Error with query: {sql_query}"}
    
    finally:
        cur.close()
        conn.close()


        

def get_database_schema(): 
    """Fetches the full database schema, including primary keys, foreign keys, and column data types."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch database name
    cur.execute("SELECT current_database();")
    db_name = cur.fetchone()[0]

    # Fetch tables, columns, and column data types
    cur.execute("""
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        ORDER BY table_name, ordinal_position;
    """)
    
    schema = {}
    for table, column, data_type in cur.fetchall():
        if table not in schema:
            schema[table] = {"columns": [], "primary_key": None, "foreign_keys": []}
        schema[table]["columns"].append({"column_name": column, "data_type": data_type})
    
    # Fetch primary keys
    cur.execute("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public';
    """)
    for table, primary_key in cur.fetchall():
        if table in schema:
            schema[table]["primary_key"] = primary_key
    
    # Fetch foreign keys
    cur.execute("""
        SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table, ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public';
    """)
    
    for table, column, foreign_table, foreign_column in cur.fetchall():
        if table in schema:
            schema[table]["foreign_keys"].append(f"{column} → {foreign_table}.{foreign_column}")
            
    cur.close()
    conn.close()
    
    # Return schema as a dictionary
    return db_name, schema



def fetch_from_db(sql_query):
    """Executes an SQL query and fetches results."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(sql_query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def get_database_data():
    """Fetches all data from all tables in the database in real-time."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch all table names
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public';
    """)
    tables = [row[0] for row in cur.fetchall()]
    
    db_data = {}
    
    for table in tables:
        cur.execute(f"SELECT * FROM {table};")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        db_data[table] = {"columns": columns, "rows": rows}
    
    db_name, schema = get_database_schema()  
    cur.close()
    conn.close()
    
    return db_data, schema




def get_build_team_data():
    # Define the SQL query
    sql_query = """
    SELECT 
        e.employee_id,  -- Include employee ID for reference
        e.role, 
        e.firstname,
        e.lastname,
        s.skill_name, 
        s.proficiency_level, 
        s.years_of_experience, 
        t.description AS validated_task
    FROM employees e
    LEFT JOIN skills s ON e.employee_id = s.employee_id
    LEFT JOIN tasks t ON e.employee_id = t.employee_id AND t.validation = TRUE
    LEFT JOIN work_and_vacation w ON e.employee_id = w.employee_id
    WHERE w.availability = TRUE;  -- Only consider available employees
    """
                                                           ##### Build a system to track employee attendance, calculate hours worked, and generate payroll. Requirements: Track work hours and holidays.  
                                                           # Calculate wages and generate payroll reports.
    # Fetch the data from the database
    data = fetch_from_db(sql_query)
    
    # Convert data into DataFrame for easy manipulation
    columns = [
        'employee_id', 'role', 'firstname', 'lastname', 'skill_name', 
        'proficiency_level', 'years_of_experience', 'validated_task'
    ]
    df = pd.DataFrame(data, columns=columns)
    
    # Handle any missing or null values if needed (e.g., for `validated_task`)
    df.fillna('No Task', inplace=True)
    
    formatted_data = convert_data_for_llm(df)
    
    return formatted_data

def convert_data_for_llm(df):
    formatted_data = ""
    
    for _, row in df.iterrows():
        formatted_data += f"Employee ID: {row['employee_id']}\n"
        formatted_data += f"Name: {row['firstname']} {row['lastname']}\n"
        formatted_data += f"Role: {row['role']}\n"
        formatted_data += f"Skills: {row['skill_name']} (Proficiency: {row['proficiency_level']}, Experience: {row['years_of_experience']} years)\n"
        formatted_data += f"Validated Task: {row['validated_task']}\n"
        formatted_data += "-" * 20 + "\n"
    
    return formatted_data
