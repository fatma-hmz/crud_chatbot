import streamlit as st
import requests
import openai
import sys
import os
import logging
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import datetime
import uuid
from tabulate import tabulate    

# Add the parent directory to sys.path so the 'database' module can be found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_utils import get_database_schema, get_database_data, fetch_from_db
from frontend.panel_functions import show_db_modal, show_schema_modal, calculate_cost, fetch_min_max_for_field, show_team_builder_modal, load_chat_sessions, save_chat_sessions, handle_team_building, clear_history

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG,  # Set logging level to DEBUG (you can change this as needed)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])  # Output logs to the console

logger = logging.getLogger(__name__)



# Set Streamlit page configuration
st.set_page_config(page_title="crud_chatbot", layout="wide")

# Custom CSS for layout and input field styling
st.markdown(""" 
    <style>
        /* Main layout */
        .container {
            display: flex;
            flex-direction: row;
        }

        /* Sidebar settings panel */
        .sidebar {
            width: 25%;
            background: #f0f0f0;
            padding: 0px;
            border-radius: 10px;
            margin-right: 20px;
        }
        
        .company-logo {
            margin-top: -10px;  /* Remove top margin */
            padding: 0 0;  /* Add minimal padding for spacing */
            border-radius: 8px;
            background-color: #d9d9d9;
        }

        /* Chat section */
        .chat-section {
            width: 75%;
            display: flex;
            flex-direction: column;
        }

        /* Chatbox */
        .chat-container {
            height: 800px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 10px;
            background: #ffffff;  /* White background */
        }

        /* Message wrapper */
        .message-wrapper {
            display: flex;
            align-items: flex-start;
            margin: 10px;
            margin-bottom: 15px; 
        }

        /* User and bot icons */
        .user-icon, .bot-icon {
            font-size: 30px;
            margin-right: 10px;
            flex-shrink: 0;
        }

        /* User messages */
        .user-message {
            background-color: #D0E3FF;  /* Light Blue */
            border-radius: 10px;
            padding: 10px;
            max-width: 80%;
        }

        /* Bot messages */
        .bot-message {
            background-color: #0078D4;
            border-radius: 10px;
            padding: 10px;
            max-width: 80%;
        }

        /* Input field styling */
        .input-container {
            display: flex;
            width: 80%;
            margin-top: 10px;
            align-items: center;  /* Ensure alignment of input field and button */
        }

        .input-field {
            flex-grow: 1;
            padding: 12px;
            border-radius: 20px;
            border: 1px solid  #0078D4;
            font-size: 16px;
            outline: none;
        }

        .send-button {
            background-color: #0078D4;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 20px;
            margin-left: 10px;
            cursor: pointer;
            font-size: 16px;
        }

        .send-button:hover {
            background-color: #005a9e;
        }    
        
        .block-container {
            padding-top: 5px;
        }    
        
    </style>
""", unsafe_allow_html=True)




def format_dict(data: dict):
    return {
        "Query Validation": (
            f"Valid based on threshold {data.get('certainty_threshold', 'N/A') * 100:.1f}%"
            if data.get("valid_prob_threshold")  
            else f"Invalid based on threshold {data.get('certainty_threshold', 'N/A') * 100:.1f}%"
        ) if data.get("certainty_threshold") is not None else "N/A",
        "Certainty Rate": f"{data.get('avg_prob', 0) * 100:.1f}%" if data.get("avg_prob") is not None else "N/A",
        "Finish Reason": data.get('finish_reason', 'N/A'),
        "Model": data.get('model', 'N/A'),
        "Temperature": data.get('temparature', 'N/A')
    }

    
    
def format_bot_response(fetched_data):
    if isinstance(fetched_data, str):
        # If the response is a string, return it as-is
        return fetched_data
    elif isinstance(fetched_data, list):
        # If the response is a list, format it into a readable string
        formatted_response = ""
        for item in fetched_data:
            if isinstance(item, list):
                formatted_response += " \n - "
                # Join elements of each list with " | " and ensure each entry is on a new line
                formatted_response += "  |  ".join([str(i) for i in item]) 
                formatted_response += " \n "
            else:
                formatted_response += str(item) + "\n"
        return formatted_response.strip()
    elif isinstance(fetched_data, dict):
        # If the response is a dictionary, format each key-value pair
        return "\n".join([f"{key}: {value}" for key, value in fetched_data.items()])
    else:
        # For unsupported types, return a generic message
        return str(fetched_data)
    
    
    
# Page Title with Custom Logo

import base64

# Function to convert image to Base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Convert logo to Base64
logo_base64 = get_base64_image("frontend/logo.png")

# Display title, logo, and description in one row
st.markdown(f"""
    <div style="margin-top: 40px; display: flex; align-items: left; justify-content: left; gap: 20px; width: 100%; background-color: white; ">
        <img src="data:image/png;base64,{logo_base64}" width="140">
        <div>
            <h1 style="margin: 0; font-size: 30px;color: #737373;">Pit-SQLizer Chatbot</h1>
            <p style="margin: 0; font-size: 18px; color: #737373;">
                Your AI-powered SQL assistant for seamless database interactions.<br>
                Effortlessly manage employee records, streamline operations, and unlock smart insights!
            </p>
        </div>
    </div>
    <br> <br>
""", unsafe_allow_html=True)

# Page footer
st.markdown(f"""
    <div style="
        position: fixed; bottom: 0; left: 0; width: 100%; 
        background-color: #f0f2f6; padding: 8px 0; 
        text-align: center; font-size: 14px; color: #555;
        border-top: 1px solid #ddd; z-index: 1000;
    ">
        © 2025 Piterion GmbH - All Rights Reserved
    </div>
""", unsafe_allow_html=True)





# Side Panel

# Company Logo

#company_logo_base64 = get_base64_image("frontend/company.png")
#st.sidebar.markdown(
#    f"""
#    <div class="company-logo">
#        <div style="display: flex; justify-content: center;">
#            <img src="data:image/png;base64,{company_logo_base64}" width="450">
#        </div>
#    </div>
#    <br>
#    """, 
#    unsafe_allow_html=True
#)




# Initialize chat sessions
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = load_chat_sessions()

# Initialize active session
if "active_session" not in st.session_state:
    new_session_id = str(uuid.uuid4())[:8]  # Unique short session ID
    st.session_state.active_session = new_session_id
    st.session_state.chat_sessions[new_session_id] = {"messages": [], "timestamp": datetime.datetime.now().isoformat()}
    save_chat_sessions()

if "show_buttons" not in st.session_state:  # to display buttons for select queries
    st.session_state.show_buttons = False

if "confirmation_needed" not in st.session_state:
    st.session_state.confirmation_needed = False

if "team_builder_response_data" not in st.session_state:
    st.session_state.team_builder_response_data = None
      
# Sidebar for selecting old sessions
st.sidebar.title("💬 Chat Sessions")


# Format session options as "id - timestamp"
session_options = [
    f"{session_id} - {st.session_state.chat_sessions[session_id]['timestamp'][:19]}"  
    for session_id in st.session_state.chat_sessions.keys()
][::-1]

# Use columns to align elements horizontally
col1, col2 = st.sidebar.columns([3, 1])  # Adjust width ratio as needed

# Select a session (dropdown)
with col1:
    selected_session_label = st.selectbox("Select a session", session_options, index=0, label_visibility="collapsed")

# Clear history button
with col2:
    if st.button("🗑️", key="clear_history_btn", help="Clear Chat History"):  
        clear_history()

# Extract the session ID from the formatted label
selected_session = selected_session_label.split(" - ")[0]

# Switch session correctly
if selected_session != st.session_state.active_session:
    st.session_state.active_session = selected_session
    st.session_state.messages = st.session_state.chat_sessions[selected_session].get("messages", [])
    st.session_state.show_buttons = st.session_state.chat_sessions[selected_session].get("show_buttons", True)
    st.session_state.confirmation_needed = st.session_state.chat_sessions[selected_session].get("confirmation_needed", False)
    st.session_state.generated_query = st.session_state.chat_sessions[selected_session].get("generated_query", "")
    st.session_state.response_data = st.session_state.chat_sessions[selected_session].get("response_data", {})
    st.session_state.total_cost = st.session_state.chat_sessions[selected_session].get("total_cost", 0.0)





st.sidebar.title("⚡ Control Panel")

# Set default values in session state
if "model" not in st.session_state:
    st.session_state.model = "gpt-4o-mini"
    st.session_state.temperature = 0.5
    st.session_state.max_tokens = 100
    st.session_state.api_key = ""
    
# Initialize cost tracking    
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0  
if "session_budget" not in st.session_state:
    st.session_state.session_budget = 1
if "api_calls" not in st.session_state:
    st.session_state.api_calls = 0    
if "certainty_threshold" not in st.session_state:
    st.session_state.certainty_threshold = 0.95




# Sidebar with collapsed sections
with st.sidebar:

            
    # Initialize session state for modals
    if "schema_modal_open" not in st.session_state:
       st.session_state.schema_modal_open = False
    if "db_modal_open" not in st.session_state:
       st.session_state.db_modal_open = False    
        
    # database viewer section    
    # Combined Section for Database and Schema
    with st.expander("📂 **Database Viewer**", expanded=False):
        col1, col2 = st.columns(2)

        # Button to refresh and show database
        with col1:
            if st.button("📋 View Database", key="open-db"):
                st.session_state.db_modal_open = True
            show_db_modal()  # Function to display DB modal

        # Button to view database schema
        with col2:
            if st.button("📊 View Schema", key="open-schema"):
                st.session_state.schema_modal_open = True
            show_schema_modal()  # Function to display Schema modal          
            

    
    
    
    

    ### Section for 3M Analyser
    
    # Dynamically create the numeric_fields dictionary from the schema
    numeric_fields = {}
    db_name, schema = get_database_schema()
    
    # Populate numeric_fields based on the schema
    for table, details in schema.items():
        numeric_fields[table] = [column_info['column_name'] for column_info in details['columns'] if column_info['data_type'] in ['integer', 'numeric', 'float', 'decimal']]

    with st.expander("🔍 **3M Analyser: Min - Max - Mean**", expanded=False):
        # Table selection
        table = st.selectbox("Select Table", list(numeric_fields.keys()), key="table_select_3M")

        # Field selection based on chosen table
        field = st.selectbox("Select Numeric Field", numeric_fields[table])

        # Execute Query Button
        if st.button("Compute 3M"):
            # Fetch Min, Max values and corresponding names
            results = fetch_min_max_for_field(table, field)

            if results:
                min_name, min_val = results[0]
                max_name, max_val = results[1]

                # Fetch Mean Value (we will compute Mean separately)
                sql_query = f"""
                    SELECT AVG({field}) 
                    FROM {table}
                """
                mean_result = fetch_from_db(sql_query)
                mean_val = mean_result[0][0] if mean_result else 0

                # Display results
                st.write(f"### {field.replace('_', ' ').title()} Statistics")
                st.write(f"**Minimum:** {min_val} ({min_name})")
                st.write(f"**Maximum:** {max_val} ({max_name})")
                st.write(f"**Mean:** {mean_val:.2f}")
                    
                    
    ### Section "Quick Viz"

    with st.expander("📊 **Quick Viz**", expanded=False):

        db_name, schema = get_database_schema()

        # Predefined human-readable queries and their SQL queries
        queries = {
            "📈 Salary distribution by department": {
                "sql": """
                    SELECT 
                        department, 
                        CONCAT(FLOOR(salary / 1000) * 1000, ' - ', (FLOOR(salary / 1000) + 1) * 1000) AS salary_range, 
                        COUNT(*) AS num_employees
                    FROM employees
                    GROUP BY department, salary_range
                    ORDER BY salary_range, department;

                """,
                "columns": ["Department", "Salary Range", "Num Employees"],
                "chart_type": "bar"
            },
            "📊 Number of employees per role": {
                "sql": """
                    SELECT role, COUNT(*) AS num_employees 
                    FROM employees
                    GROUP BY role
                    ORDER BY num_employees DESC
                """,
                "columns": ["Role", "Num Employees"],
                "chart_type": "pie"
            },
            "📉 Project budget distribution": {
                "sql": """
                    SELECT proj_name, budget 
                    FROM projects
                    ORDER BY budget DESC
                """,
                "columns": ["Project Name", "Budget"],
                "chart_type": "line"
            },
            "⏳ Work hours by employee": {
                "sql": """
                    SELECT e.firstname || ' ' || e.lastname AS employee, 
                        SUM(t.work_hours) AS total_hours
                    FROM tasks t
                    JOIN employees e ON t.employee_id = e.employee_id
                    GROUP BY employee
                    ORDER BY total_hours DESC
                """,
                "columns": ["Employee", "Total Hours"],
                "chart_type": "bar"
            }
        }

        # Select predefined query
        selected_query = st.selectbox("Choose a query", list(queries.keys()), key="viz_query")

        if st.button("Generate Quick Visualization"):
            sql_query = queries[selected_query]["sql"]
            chart_type = queries[selected_query]["chart_type"]
            column_names = queries[selected_query]["columns"]

            results = fetch_from_db(sql_query)

            if results:
                # Convert results to DataFrame with correct column names
                df = pd.DataFrame(results, columns=column_names)
                st.write(df)
                # Generate appropriate chart
                if chart_type == "bar":
                    fig = px.bar(
                        df, 
                        x=df.columns[0], 
                        y=df.columns[1], 
                        color=df.columns[1],  # Color by value
                        labels={df.columns[1]: "Count"}, 
                        title=selected_query,
                        color_continuous_scale="Blues"  # Use shades of blue
                    )

                elif chart_type == "pie":
                    fig = px.pie(
                        df, 
                        names=df.columns[0], 
                        values=df.columns[1], 
                        title=selected_query,
                        color_discrete_sequence=px.colors.sequential.Blues  # Blue shades for pie
                    )

                elif chart_type == "line":
                    fig = px.line(
                        df, 
                        x=df.columns[0], 
                        y=df.columns[1], 
                        markers=True, 
                        title=selected_query
                    )
                    fig.update_traces(line=dict(color="royalblue"))  # Set line color

                # ✅ Display the chart
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("⚠️ No data available for this visualization.")
                
                
                
                
                
    ### Section "Smart Team Builder" 
    if "team_builder_modal_open" not in st.session_state:
        st.session_state.team_builder_modal_open = False
    if "project_description" not in st.session_state:
        st.session_state.project_description = ""

  
    # Show Smart Features UI for project description and team building
    with st.expander("👨‍💻 **Smart Team Builder**", expanded=False):

        # Handle team building logic (side panel)
        handle_team_building()
        
    # Show Team Builder modal if the flag is set
    if st.session_state.team_builder_modal_open:
        show_team_builder_modal()  # Function to display the team builder modal




    ### Direct SQL Query Execution
    
    with st.expander("🖋️ **Execute SQL**", expanded=False):
        # SQL query input section
        sql_query = st.text_area("Enter your SELECT query below:", height=100)

        if st.button("Run"):
            if sql_query.strip():
                try:
                    # Assuming fetch_from_db executes the query and returns results
                    results = fetch_from_db(sql_query)

                    if results:
                        # Convert the list of results to a pandas DataFrame
                        results_df = pd.DataFrame(results)
                        
                        # Check if the results are duplicated and only display unique rows
                        unique_results = results_df.drop_duplicates()

                        st.write("### Query Results")
                        st.dataframe(unique_results)  # Display unique results

                    else:
                        st.write("No results returned for the query.")
                except Exception as e:
                    st.error(f"Error executing query: {e}")
            else:
                st.warning("Please enter a valid SQL query.")





    ### Settings
    with st.expander("⚙️ **Settings**", expanded=False):  # Collapsible settings panel with bold title
        # Model selection
        model = st.selectbox( "Select Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],  index=["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"].index(st.session_state.get("model", "gpt-4o-mini")) )

        # API Key input with built-in eye icon for visibility toggle
        api_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.api_key)

        # Temperature and max tokens sliders
        col1, col2 = st.columns([0.9, 0.1])  # Create two columns to align the "i" icon next to the slider
        with col1:
            temperature = st.slider("Temperature", 0.0, 1.0, st.session_state.temperature, 0.1)
        with col2:
            st.markdown('<div style="font-size: 20px; color: #5e5e5e; cursor: pointer;" title="The temperature controls randomness in the model’s responses. A higher value (closer to 1) makes output more random, while a lower value (closer to 0) makes it more deterministic.">❓</div>', unsafe_allow_html=True)

        # Max tokens slider
        max_tokens = st.slider("Max Tokens", 50, 300, st.session_state.max_tokens, 50)

        # Session Budget (0 to 3 Euros)
        session_budget = st.slider("Session Budget (€)", 0.0, 5.0, float(st.session_state.get("session_budget", 1.0)), 0.1)

        # Certainty Threshold (0 to 1)
        certainty_threshold = st.slider("Certainty Threshold", 0.5, 1.0, st.session_state.get("certainty_threshold", 0.95), 0.05)


        if st.button("Apply"):
            st.session_state.model = model
            st.session_state.api_key = api_key 
            st.session_state.temperature = temperature
            st.session_state.max_tokens = max_tokens  
            st.session_state.session_budget = session_budget
            st.session_state.certainty_threshold = certainty_threshold
            st.rerun()
            
        # Reset button
        if st.button("Reset to Default"):
            st.session_state.model = "gpt-4o-mini"
            st.session_state.temperature = 0.5
            st.session_state.max_tokens = 100
            st.session_state.session_budget = 1.0
            st.session_state.certainty_threshold = 0.95
            st.session_state.api_key = ""

            # Re-initialize widgets with the default values
            st.rerun()
            
            

                
                
    ### API Cost Estimation Section
    with st.expander("💰 **API Cost Tracking**", expanded=False):  
        session_budget = st.session_state.session_budget
        st.write(f"**Session Budget:** €{session_budget:.2f}")
        cost = st.session_state.total_cost
        st.write(f"**Session Cost:** €{cost:.6f}")
        api_call = st.session_state.api_calls 
        st.write(f"**Total API Calls:** {api_call}")
            
        # Calculate the percentage of the cost % budget
        percentage = (cost / session_budget) * 100  
        remaining = max(100 - percentage, 0)  # Ensure remaining is non-negative

        
        # Format the percentage to show 4 decimal places
        formatted_percentage = f"{percentage:.4f}"

        # Create a placeholder for the donut chart
        cost_chart_placeholder = st.empty()  
        
        if cost >= session_budget:
            exceeded = percentage - 100  # How much it has exceeded
            remaining = 0  
            colors = ["#d9534f", "#E0E0E0"]  # Red for exceeded
            labels = ["Exceeded", ""]
            center_text = f"Exceeded\n{100+exceeded:.2f}%"
        else:
            colors = ["#AED6E8", "#E0E0E0"]  # Default blue for budget tracking
            labels = ["", ""]
            center_text = f"Remaining\n{remaining:.2f}%"

        # Create the donut chart and update it
        with cost_chart_placeholder:
            fig, ax = plt.subplots(figsize=( 4, 4))  

            # Remove white background
            fig.patch.set_visible(False)

            # Create the pie chart
            wedges, texts = ax.pie(
                [min(percentage, 100), remaining],
                labels=labels,  
                startangle=90,
                colors=colors,  # Switch to red if budget is exceeded
                wedgeprops={"width": 0.6},
            )

            # Add a circle in the center to make it a donut chart
            circle = plt.Circle((0, 0), 0.55, color='white', linewidth=2, edgecolor='black')
            ax.add_artist(circle)

            # Display remaining or exceeded percentage in the center
            ax.text(0, 0, center_text, ha='center', va='center', fontsize=14, color='black')

            # Display the donut chart
            st.pyplot(fig)

        # Check if the cost exceeds the budget
        if cost > session_budget:
            st.warning(f"⚠️ Warning: The session cost has exceeded the budget!")
        elif cost > session_budget * 0.9:
            st.warning(f"⚠️ Warning: Budget almost reached!")            



   


# Initialize confirmation state
if "generated_query" not in st.session_state:
    st.session_state.generated_query = None
if "response_data" not in st.session_state:
    st.session_state.response_data = None    
#if "confirmation_needed" not in st.session_state:
    #st.session_state.confirmation_needed = False
if "show_query" not in st.session_state:
    st.session_state.show_query = False
if "show_data" not in st.session_state:
    st.session_state.show_data = False
if "user_input" not in st.session_state:
    st.session_state.user_input = None    
#if "show_buttons" not in st.session_state:  # to display buttons for select queries
    st.session_state.show_buttons = False
#if "show_more" not in st.session_state:
    st.session_state.show_more = False
    

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I assist you?"}]


# Define the paths to the custom icons
user_icon_base64 = get_base64_image("frontend/user_icon.png")
bot_icon_base64 = get_base64_image("frontend/bot_icon.png")

user_icon_path = "frontend/user_icon.png"
bot_icon_path = "frontend/bot_icon.png"


# Display chat messages from session history
# Display chat messages from session history
for message in st.session_state.messages:
    avatar_path = user_icon_path if message["role"] == "user" else bot_icon_path

    with st.chat_message(message["role"], avatar=avatar_path): 
        st.markdown(message["content"])

        
        
        

# User input
user_input = st.chat_input("Type your question & Submit")

if user_input:

     # Add user input to the current conversation history on UI
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.user_input = user_input

    timestamp = datetime.datetime.now().isoformat()
    
    # Save user message to the correct session
    st.session_state.chat_sessions[st.session_state.active_session]["messages"].append(
        {"role": "user", "content": user_input, "timestamp": timestamp}
    )
    save_chat_sessions()
    
    # Display "Thinking..." while processing
    with st.chat_message("assistant", avatar = bot_icon_path):
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("Thinking...")

    # Backend API call
    api_url = "http://127.0.0.1:5000/crud"
    payload = {"message": user_input, "model": st.session_state.model, "temperature": st.session_state.temperature, "max_tokens": st.session_state.max_tokens, "certainty_threshold": st.session_state.certainty_threshold ,  "api_key": st.session_state.api_key}
    response = requests.post(api_url, json=payload)
    # Remove "Thinking..." message
    thinking_placeholder.empty()

    # Process response
    bot_response = "Error: Could not fetch response from backend."
    if response.status_code == 200:
        #st.session_state.show_buttons = True  this allow to display button even for non select sueries
        result = response.json()
        st.session_state.response_data = result["response_data"]     
        
        if "fetched_data" in result:
            fetched_data = result["fetched_data"]
            bot_response = format_bot_response(fetched_data)
            st.session_state.show_buttons = True   
            st.session_state.generated_query = result["generated_query"]
                
        elif "generated_query" in result:
            st.session_state.confirmation_needed = True  
            st.session_state.generated_query = result["generated_query"]      
            bot_response = f"Generated Query:  `{result['generated_query']}`  {result['confirmation_message']}"  
            st.session_state.show_buttons = False
            
        st.session_state.response_data = result["response_data"]        
        st.session_state.total_cost += calculate_cost(result["response_data"])
        st.session_state.api_calls += 1
    
    # Add Bot response to UI    
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    
    # Add assistant response along with response_data to the session messages
    st.session_state.chat_sessions[st.session_state.active_session]["messages"].append(
        {
            "role": "assistant",
            "content": bot_response,
            "response_data": result.get("response_data", None) 
            #"timestamp": timestamp
            #"generated_query": st.session_state.get("generated_query", None)
            
        }
    )
    
    # Save latest session status to load
    st.session_state.chat_sessions[st.session_state.active_session]["confirmation_needed"] = st.session_state.get("confirmation_needed", False)
    st.session_state.chat_sessions[st.session_state.active_session]["show_buttons"] = st.session_state.get("show_buttons", False)
    st.session_state.chat_sessions[st.session_state.active_session]["generated_query"] = st.session_state.generated_query
    st.session_state.chat_sessions[st.session_state.active_session]["response_data"] = st.session_state.response_data
    st.session_state.chat_sessions[st.session_state.active_session]["total_cost"] = st.session_state.total_cost


    save_chat_sessions()

    # Refresh UI
    st.rerun()

# --- AFTER THE RERUN, PERSIST THE BUTTONS ---
if st.session_state.get("show_buttons", False):
    with st.container():
        display_query_button, show_more_button = st.columns(2)
        with display_query_button:
            if st.button("🧐 Query", use_container_width=True):
                st.code(st.session_state.generated_query, language="sql")
        with show_more_button:
            if st.button("⏬ More", use_container_width=True):
                st.json(format_dict(st.session_state.response_data))
                
    

# Handle confirmation step
if st.session_state.confirmation_needed and st.session_state.generated_query:
    with st.container():
        col1, col2, col3, col4, col5, col6 = st.columns(6)  
        with col2:
            confirm = st.button("✅ Confirm", use_container_width=True)  
        with col3:
            deny = st.button("❌ Deny", use_container_width=True)
        with col4:
            rerun = st.button("🔄 Regenerate", use_container_width=True )
        with col5:
            more = st.button("⏬ More", use_container_width=True)
    if confirm:
        execute_response = requests.post(
            "http://127.0.0.1:5000/execute", json={"generated_query": st.session_state.generated_query, "confirm": True}
        )
        
        # Remove only the last assistant response (generated query)
        #for i in range(len(st.session_state.messages) - 1, -1, -1):
            #if st.session_state.messages[i]["role"] == "assistant":
                #del st.session_state.messages[i]
                #break     
            
        st.session_state.messages.append({"role": "assistant", "content": "Query executed successfully." if execute_response.status_code == 200 else "Error executing query."})
        st.session_state.show_buttons = False  # Display buttons
        st.session_state.confirmation_needed = False
        st.session_state.generated_query = None
    
        st.rerun()
        
    elif deny:
        
        # Remove only the last assistant response (generated query)
        #for i in range(len(st.session_state.messages) - 1, -1, -1):
            #if st.session_state.messages[i]["role"] == "assistant":
                #del st.session_state.messages[i]
                #break     
                
        st.session_state.messages.append({"role": "assistant", "content": "Query execution denied."})
        st.session_state.confirmation_needed = False
        st.session_state.generated_query = None
        
        st.rerun()
 
    elif rerun:
                
            # Remove only the last assistant response
            for i in range(len(st.session_state.messages) - 1, -1, -1):
                if st.session_state.messages[i]["role"] == "assistant":
                    del st.session_state.messages[i]
                    break     
            
            with st.chat_message("assistant", avatar = bot_icon_path):
                thinking_placeholder = st.empty()
                thinking_placeholder.markdown("Regenerating...")    
            
                
            # Resend the request
            response = requests.post( "http://127.0.0.1:5000/crud" , json= {"message": st.session_state.user_input , "model": st.session_state.model, "temperature": st.session_state.temperature, "max_tokens": st.session_state.max_tokens, "certainty_threshold": st.session_state.certainty_threshold ,  "api_key": st.session_state.api_key} )
            
            # Remove "Regenerating..." message                          
            thinking_placeholder.empty()

            if response.status_code == 200:
                result = response.json()
                
                ## removed case of fetched data coz it doesnt appear for select queries anyways
                
                #if "fetched_data" in result:
                    #bot_response = str(result["fetched_data"][0]) if isinstance(result["fetched_data"], list) else str(result["fetched_data"])

                    # Use expander instead of button to display the executed query
                    #with st.expander("Display Query"):
                        #st.code(result["generated_query"], language="sql")
                    
                    #with st.expander("Display Response Data"):
                        #st.json(result["response_data"])
                        
                if "generated_query" in result:
                    st.session_state.generated_query = result["generated_query"]
                    st.session_state.response_data = result["response_data"] 
                    st.session_state.confirmation_needed = True  
                    bot_response = f"Regenerated Query: `{result['generated_query']}` \n {result['confirmation_message']}"
                    st.session_state.show_buttons = False
                    
                    with st.expander("Display Query"):
                        st.code(result["generated_query"], language="sql")

                    with st.expander("Response Data"):
                        st.json(result["response_data"])
                        
                st.session_state.total_cost += calculate_cost(result["response_data"])
                st.session_state.api_calls += 1
                

            # Append response to conversation history
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            
            # Refresh UI
            st.rerun()
            

                
    elif more:
        st.json(format_dict(st.session_state.response_data))   
        if more: #clear if i click again !!!!!!!!!!  
          st.session_state.show_more = False 
    
    # Update buttons status in history if user clicks
    st.session_state.chat_sessions[st.session_state.active_session]["confirmation_needed"] = st.session_state.get("confirmation_needed", False)

    save_chat_sessions()       
            
            
