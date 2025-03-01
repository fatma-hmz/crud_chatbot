import sys
import os
import streamlit as st
import logging
import requests
import json
import datetime


# Add the parent directory to sys.path so the 'database' module can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import the function
from database.db_utils import get_database_schema, get_database_data, fetch_from_db

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG,  # Set logging level to DEBUG (you can change this as needed)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])  # Output logs to the console

logger = logging.getLogger(__name__)



# Function to display database schema modal
def show_schema_modal():
    db_name, schema = get_database_schema()

    if st.session_state.schema_modal_open:
        modal_html = f"""
        <div style="position: fixed; top: 30%; left: 30%; width: 50%; height: 50%; 
                    background-color: white; padding: 20px; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 100; overflow: auto;">
            <h2>Database: {db_name}</h2>
            <div>
        """
        for table, details in schema.items():
            modal_html += f"<h4>Table: {table}</h4>"
            modal_html += "<p><strong>Columns:</strong></p>"
            
            # Iterate through each column and its type
            for column_info in details['columns']:
                column_name = column_info['column_name']
                column_type = column_info['data_type']
                
                modal_html += f"{column_name} ({column_type}) | "
                
            modal_html += f"<br> <br>"
            
            if details['primary_key']:
                modal_html += f"<p><strong>Primary Key:</strong> {details['primary_key']}</p>"
            if details['foreign_keys']:
                modal_html += "<p><strong>Foreign Keys:</strong></p>"
                for fk in details['foreign_keys']:
                    modal_html += f"<p>{fk}</p>"
            modal_html += "<hr>"

        modal_html += "</div></div>"
        st.markdown(modal_html, unsafe_allow_html=True)

        if st.button("Hide Schema ❌", key="close-schema-modal"):
            st.session_state.schema_modal_open = False




# Function to display database data modal
def show_db_modal():
    db_data, schema = get_database_data()

    if isinstance(db_data, dict) and st.session_state.db_modal_open:
        modal_html = f"""
        <div style="position: fixed; top: 30%; left: 27%; width: 70%; height: 50%; 
                    background-color: white; padding: 20px; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 100; overflow: auto;">
            <h2>View Database</h2>
            <div style="position: absolute; top: 10px; right: 10px; background-color: white; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                <div><span style="background-color: #DBEDF3; padding: 2px 5px; border-radius: 3px;">Primary Key</span></div>
                <div><span style="background-color: #E0E0E0; padding: 2px 5px; border-radius: 3px;">Foreign Key</span></div>
            </div>
        """
        tab_names = list(db_data.keys())  
        selected_table = st.selectbox("Select Table", tab_names)  

        table_schema = schema.get(selected_table, {})
        modal_html += f"<h4>Table: {selected_table}</h4>"
        modal_html += "<table style='width:100%; border-collapse: collapse;'>"
        modal_html += "<thead><tr>"

        for column in db_data[selected_table]["columns"]:
            header_style = ""
            if column == table_schema.get("primary_key"):
                header_style = "background-color: #DBEDF3; color: black;"
            elif any(fk.startswith(column) for fk in table_schema.get("foreign_keys", [])):
                header_style = "background-color: #E0E0E0; color: black;"
            modal_html += f"<th style='border: 1px solid #ddd; padding: 8px; text-align: left; {header_style}'>{column}</th>"

        modal_html += "</tr></thead><tbody>"

        for row in db_data[selected_table]["rows"]:
            modal_html += "<tr>"
            for cell in row:
                modal_html += f"<td style='border: 1px solid #ddd; padding: 8px;'>{cell}</td>"
            modal_html += "</tr>"

        modal_html += "</tbody></table><hr></div></div>"
        st.markdown(modal_html, unsafe_allow_html=True)

        if st.button("Hide Data ❌", key="close-db-modal"):
            st.session_state.db_modal_open = False

        
        
        
    
    

# Function for dynamic OpenaAI cost Estimation     
       
OPENAI_PRICING_base = {
    "gpt-4o-2024": (2.50, 1.25, 10.00),
    "gpt-4o-mini": (0.15, 0.075, 0.60),
    "gpt-4-turbo": (10.00, 10.00, 30.00),
    "gpt-4": (30.00, 30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 0.50, 1.50),
}


OPENAI_PRICING = {
    "gpt-4o-2024-08-06": (2.50, 1.25, 10.00),
    "gpt-4o-mini-2024-07-18": (0.15, 0.075, 0.60),
    "gpt-4-turbo-2024-04-09": (10.00, 10.00, 30.00),
    "gpt-4-0613": (30.00, 30.00, 60.00),
    "gpt-3.5-turbo-0125": (0.50, 0.50, 1.50),
}


import re

def calculate_cost(response_data):
    """Calculates and updates the session cost based on token usage."""
    request_cost = 0
    if "model" not in response_data.keys():
        logger.debug(f" \n \n !!Warning: Model not identified!")
        return  request_cost
    #model = "-".join(response_data['model'].split("-")[:3]) 
    model= response_data['model']
    prompt_tokens = response_data['prompt_tokens']
    completion_tokens = response_data['completion_tokens']
    cached_tokens = response_data['cached_tokens']
    
    logger.debug(f" \n \n this is how model name is formatted {model}")
    
    # Determine pricing for selected model
    if model in OPENAI_PRICING:
        input_price, cached_input_price, output_price = OPENAI_PRICING[model]
    else:
        logger.debug(f" \n \n !! Model {model} not found in pricing table!")
        return  request_cost

    # Cost Calculation
    input_cost = ((prompt_tokens - cached_tokens) * input_price) / 1000000
    cached_cost = (cached_tokens * cached_input_price) / 1000000
    output_cost = (completion_tokens * output_price) / 1000000

    # Update total session cost
    request_cost = input_cost + cached_cost + output_cost

    return round(request_cost, 6)  


### Function for the 3M Analyser

def fetch_min_max_for_field(table, field):
    """Fetch the Min, Max, and corresponding name for Min, Max."""
    if table == "projects":
        # For projects, we need to get the project name along with the min/max value
        query = f"""
            SELECT proj_name, {field} 
            FROM {table} 
            WHERE {field} = (SELECT MIN({field}) FROM {table})
            OR {field} = (SELECT MAX({field}) FROM {table});
        """
    elif table == "employees":
        # For employees, we need to get the employee name along with the min/max value
        query = f"""
            SELECT CONCAT(firstname, ' ', lastname) AS employee_name, {field} 
            FROM {table} 
            WHERE {field} = (SELECT MIN({field}) FROM {table})
            OR {field} = (SELECT MAX({field}) FROM {table});
        """
    elif table == "tasks" or table == "work_and_vacation":
        # For tasks and work_and_vacation, replace NULL with 0 for hour fields and get the corresponding names
        query = f"""
            SELECT CONCAT(e.firstname, ' ', e.lastname) AS employee_name, 
                   COALESCE(t.{field}, 0) AS {field} 
            FROM {table} t
            JOIN employees e ON e.employee_id = t.employee_id
            WHERE COALESCE(t.{field}, 0) = (SELECT MIN(COALESCE({field}, 0)) FROM {table})
            OR COALESCE(t.{field}, 0) = (SELECT MAX(COALESCE({field}, 0)) FROM {table});
        """
    else:
        # Handle other cases as needed
        query = f"""
            SELECT {field} 
            FROM {table} 
            WHERE {field} = (SELECT MIN({field}) FROM {table})
            OR {field} = (SELECT MAX({field}) FROM {table});
        """

    return fetch_from_db(query)





def show_team_builder_modal():
    """Displays the Team Builder modal window with the response."""
    if "team_composition" in st.session_state:
        response_data = st.session_state["team_composition"]  # Should be a dictionary

        # Ensure response_data is a dictionary
        if isinstance(response_data, dict):
            ideal_team_composition = response_data.get("Ideal Team Composition", "")
            matching_employees = response_data.get("Matching Employees", "")
        else:
            ideal_team_composition = "Invalid response format"
            matching_employees = ""

        # Modal HTML styling for the window
        modal_html = f"""
        <div style="position: fixed; top: 22%; left: 35%; width: 50%; height: 65%; 
                    background-color: white; padding: 20px; border-radius: 10px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2); z-index: 100; overflow: auto;">  
            <h2>🚀 Build Your Project Team</h2>  
            <div style="position: absolute; top: 10px; right: 10px; background-color: white; padding: 10px; border: 1px solid #ddd; border-radius: 5px;"></div>
            <div style="margin-top: 20px;">  
                <div>{ideal_team_composition}</div>
                <div>{matching_employees}</div>
            </div>
        </div>
        """
        st.markdown(modal_html, unsafe_allow_html=True)






# Function to handle the team building logic
def handle_team_building():
    """Handles the logic for building the team and showing the response in the modal."""
    
    # Get project description input from the side panel
    project_description = st.text_area(
        "Describe your project:",
        value=st.session_state.get("project_description", ""),
        key="project_desc_input"
    )

    # Store input in session state
    if project_description:
        st.session_state["project_description"] = project_description

    # Create two columns for the buttons to be displayed side by side
    col1, col2 = st.columns(2)

    with col1:
        # Handle the "Build Team" button click
        if st.button("🚀 Build Team", key="build_team_btn"):
            if st.session_state["project_description"].strip():
                # API call to build the team
                response  = requests.post(
                    "http://localhost:5000/build_team",
                    json={"description": st.session_state["project_description"] ,  "model": st.session_state["model"], "temperature": st.session_state.temperature, "certainty_threshold": st.session_state.certainty_threshold ,  "api_key": st.session_state.api_key}
                )
                result = response.json()

                if response.status_code == 200:

                    st.session_state["team_composition"] = result  
  
                    st.session_state.team_builder_response_data = result["team_builder_response_data"] 
                    logger.debug(f" \n \n \n               §§§   !!  RESPONSE DATA FROM PANEL FUNCTION : {st.session_state.team_builder_response_data} \n")
                    st.session_state.total_cost += calculate_cost(st.session_state.team_builder_response_data)
                    st.session_state.api_calls += 1

                    # Show the modal
                    st.session_state["team_builder_modal_open"] = True
                    st.rerun()  # Refresh the page and show the modal
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")

    with col2:
        # Handle hiding the modal (if "Hide" button is clicked)
        if st.button("❌ Hide", key="close_team_modal"):
            st.session_state["team_builder_modal_open"] = False
            st.rerun()  # Refresh to hide the modal





CHAT_HISTORY_FILE = "frontend/chat_history.json"

def load_chat_sessions():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as file:
            try:
                sessions = json.load(file)
                # Filter out sessions older than 3 days
                seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
                return {session_id: chat for session_id, chat in sessions.items()
                        if datetime.datetime.fromisoformat(chat["timestamp"]) > seven_days_ago}
            except json.JSONDecodeError:
                return {}
    return {}

# Save chat sessions to file
def save_chat_sessions():
    with open(CHAT_HISTORY_FILE, "w") as file:
        json.dump(st.session_state.chat_sessions, file, indent=4)
        
# Clear saved history        
def clear_history():
    """Deletes all sessions from the JSON file except for the current session."""
    if st.session_state.active_session in st.session_state.chat_sessions:
        current_session_data = {st.session_state.active_session: st.session_state.chat_sessions[st.session_state.active_session]}
    else:
        current_session_data = {}

    # Overwrite the JSON file with only the active session
    with open(CHAT_HISTORY_FILE, "w") as file:
        json.dump(current_session_data, file, indent=4)

    # Update session state to keep only the active session
    st.session_state.chat_sessions = current_session_data
    st.rerun()  # Refresh UI
