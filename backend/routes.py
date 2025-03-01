from flask import Blueprint, request, jsonify
from database.db_utils import fetch_from_db, execute_query
from backend.openai_utils import query_openai, build_team
from frontend.panel_functions import calculate_cost
import streamlit as st
import logging

query_blueprint = Blueprint('query_api', __name__)


# Set up logging configuration
logging.basicConfig( level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])  

logger = logging.getLogger(__name__)


# Route for CRUD operations with confirmation
@query_blueprint.route('/crud', methods=['POST'])
def crud_operations():
    try:
        user_input = request.json.get("message", "")
        if not user_input:
            return jsonify({"response": "Error: No message provided in the request."}), 400
        
        model = request.json.get("model", "gpt-4o-mini")  
        temperature = request.json.get("temperature", 0.5)  
        max_tokens = request.json.get("max_tokens", 100) 
        certainty_threshold  = request.json.get("certainty_threshold", 0.95)
        api_key = request.json.get("api_key", None)
        
        sql_query, response_data = query_openai(user_input, model = model,  temperature = temperature, max_tokens = max_tokens, certainty_threshold = certainty_threshold, api_key = api_key)

        # Check if the query is valid for SELECT, INSERT, UPDATE, DELETE 
        if not sql_query or "SELECT" not in sql_query.upper() and not any(op in sql_query.upper() for op in ["INSERT", "UPDATE", "DELETE"]):
            return jsonify({"response": "Error: Invalid SQL query generated."}), 400

        response = {}

        # Split queries if multiple
        queries = [q.strip() for q in sql_query.split(";") if q.strip()]

        # Determine if all queries meet the valid probability threshold
        approved_accuracy = response_data.get("valid_prob_threshold", False)
        
        # Construct confirmation message based on accuracy
        accuracy_warning = "\n❗The generated response might be biased. Consider checking or regenerating with another model." if not approved_accuracy else "\n ✨ Generated Query is qualified as accurate"
    
        if len(queries) > 1:
                    confirmation_message = f"Multiple queries detected ({len(queries)}). Do you want to proceed with all operations? Please confirm. \n"
                    response = {
                        "generated_query": sql_query,
                        "approved_accuracy": approved_accuracy,
                        "confirmation_message": confirmation_message + accuracy_warning,
                        "response_data": response_data
                    }

        # Handle a single SELECT query
        elif "SELECT" in queries[0].upper():
            confirmation_message = ""
            try:
                data = fetch_from_db(queries[0])
            except Exception as e:
                return jsonify({"response": f"Error fetching data from database: {str(e)}"}), 500

            response = {
                "confirmation_message" : accuracy_warning,
                "generated_query": sql_query,
                "approved_accuracy": approved_accuracy,
                "fetched_data": data if data else "No results found.",
                "response_data": response_data
            }

        # Handle a single non-SELECT query (INSERT, UPDATE, DELETE)
        else:
            confirmation_message = "Do you want to proceed with this operation? Please confirm."
            response = {
                "generated_query": sql_query,
                "approved_accuracy": approved_accuracy,
                "confirmation_message": confirmation_message + "\n" + accuracy_warning,
                "response_data": response_data
            }
            
        return jsonify(response)
    except Exception as e:
            return jsonify({"response": f"An unexpected error occurred: {str(e)}"}), 500  




@query_blueprint.route('/execute', methods=['POST'])
def execute_crud():
    try:
        sql_query = request.json.get("generated_query", "")
        confirm = request.json.get("confirm", False)
        
        # Validate the query
        if not sql_query or "SELECT" not in sql_query.upper() and not any(op in sql_query.upper() for op in ["INSERT", "UPDATE", "DELETE"]):
            return jsonify({"response": "Error: Invalid SQL query generated."}), 400

        response = {"queries": []}

        # Split queries if multiple
        queries = [q.strip() for q in sql_query.split(";") if q.strip()]

        for query in queries:
            try:
                if "SELECT" in query.upper():
                    # Fetch data for SELECT queries immediately
                    data = fetch_from_db(query)
                    response["queries"].append({
                        "generated_query": query,
                        "fetched_data": data if data else "No results found."
                    })
                else:
                    # Confirm before modifying data
                    if not confirm:
                        return jsonify({"response": "Operation cancelled by user."}), 200

                    # Execute the query using the updated execute_query
                    query_result = execute_query(query)
                    response["queries"].append({
                        "generated_query": query,
                        **query_result,  # This will include success or error message, 
                        
                    })     

            except Exception as e:
                response["queries"].append({
                    "generated_query": query,
                    "error": f"Error processing query: {str(e)}"
                })
       
        return jsonify(response)

    except Exception as e:
        return jsonify({"response": f"An unexpected error occurred: {str(e)}"}), 500




@query_blueprint.route('/build_team', methods=['POST'])
def build_project_team():
    try:
        project_description = request.json.get("description", "")
        model = request.json.get("model", "gpt-4o-mini")  
        temperature = request.json.get("temperature", 0.5)  
        certainty_threshold  = request.json.get("certainty_threshold", 0.95)
        api_key = request.json.get("api_key", None)
        
        
        if not project_description or not isinstance(project_description, str):
            return jsonify({"error": "Please provide a valid project description."}), 400

        recommendation , team_builder_response_data = build_team(description=project_description, model = model,  temperature = temperature, certainty_threshold = certainty_threshold, api_key = api_key)
        logger.debug(f" \n \n !! Rcommendation from team builder: {recommendation} \n")

        #st.session_state.team_builder_response_data = team_builder_response_data        
        #st.session_state.total_cost += calculate_cost(team_builder_response_data)
        logger.debug(f" \n \n \n !! Cost from team builder : {calculate_cost(team_builder_response_data)} \n")
        #st.session_state.api_calls += 1
        
        logger.debug(f" \n \n !! RECOMMENDATION FROM ROUTES for team builder: {recommendation} \n")
        logger.debug(f" \n \n !! Response data  FROM ROUTESfor team builder: {team_builder_response_data} \n")
        if 'error' in recommendation:
            return jsonify(recommendation, team_builder_response_data), 500

        return jsonify({
            "Ideal Team Composition": recommendation,
            "team_builder_response_data" : team_builder_response_data,
            
        }), 200
        
    

    except Exception as e:
        logger.error(f"Error occurred in build_project_team function: {str(e)}")
        return jsonify({"response": "An unexpected error occurred."}), 500
