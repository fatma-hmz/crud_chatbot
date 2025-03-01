import os
from dotenv import load_dotenv
from openai import OpenAI
from database.db_utils import get_database_schema, get_build_team_data
import math
import re
import logging
import streamlit as st

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG,  
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])  

logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_openai_client(api_key_from_request=None):
    api_key = api_key_from_request or OPENAI_API_KEY  # Prefer request key if provided in ui
    if not api_key:
        return None  # No key available
    return OpenAI(api_key=api_key, timeout=180)  # Initialize OpenAI client


SCHEMA_TEXT = get_database_schema()


 
def query_openai(prompt, model, temperature, max_tokens, certainty_threshold, api_key):
        
    agent = get_openai_client(api_key)  # Use the best available API key
    if not agent:
        return None, {"error": "Missing OpenAI API Key"}
    
    system_prompt = (
        "You are an AI assistant that generates SQL queries for CRUD operations (Create, Read, Update, Delete) "
        "on an employee management system. The database schema is as follows:\n\n"
        f"{SCHEMA_TEXT}\n\n"
        "Generate relevant SQL queries in plain text based on the user's input. Do not include any extra text, explanations, or instructions."
        "Ensure the queries are properly formatted, valid, syntactically correct, properly quoted, and correspond to one of the following operations: "
        "SELECT (Read), INSERT (Create), UPDATE, DELETE."
    )
    

    response = agent.chat.completions.create(
        model= model,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        max_tokens= max_tokens,
        temperature= temperature,
        logprobs= True
    )
        
    sql_query = response.choices[0].message.content

    sql_query = format_sql_query(sql_query)
        
    # The log probabilities of each output token reflecting certainty    
    token_log_prob = response.choices[0].logprobs   
    
    # Convert logprobs to probabilities
    if token_log_prob and hasattr(token_log_prob, "content"):
        token_probabilities = [
            {"token": token_data.token, "probability": round(math.exp(token_data.logprob), 3)}
            for token_data in token_log_prob.content
        ]
        
        min_prob = min(tp['probability'] for tp in token_probabilities)
        avg_prob = round(sum(tp['probability'] for tp in token_probabilities) / len(token_probabilities),3)
        
        # Check if min_prov and avg_prob are above threshold to confirm accuracy
        valid_prob_threshold = min_prob > 0.2 and avg_prob > certainty_threshold
        
    else:
        token_probabilities = []
        valid_prob_threshold = False
        
    # Extract additional response data
    response_data = {
        'query':sql_query, 
        'response_id': response.id,
        'finish_reason': finish_reason_dict.get(response.choices[0].finish_reason, "Unknown reason"), 
        'total_tokens': response.usage.total_tokens,
        'prompt_tokens': response.usage.prompt_tokens,
        'completion_tokens': response.usage.completion_tokens,
        'cached_tokens': max(0, response.usage.prompt_tokens - response.usage.completion_tokens),
        'token_prob':token_probabilities,
        'min_prob': min_prob,
        'avg_prob': avg_prob,
        'certainty_threshold': certainty_threshold,
        'valid_prob_threshold': valid_prob_threshold,
        'model': response.model,
        'temparature': temperature
    }
 

    return sql_query, response_data


finish_reason_dict = {
    "stop": "stop -> Response completed naturally ✅",
    "length": "length -> Response was cut off due to the token limit ⚠️",
    "content_filter": "content filter -> Response stopped due to content filters ⚠️",
    "function_call": "function call -> Model decided to call a function instead of returning a normal response 🔧",
    "tool_calls": "tool calls -> Model invoked one or more tools (e.g., API calls, functions)."
}


# Format the query to make sure it doesnt generate an error in execution
def format_sql_query(sql_query):
    """Formats and validates the generated SQL query to avoid syntax errors."""
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    # Ensure the query ends with a semicolon (only if it doesn't already have a valid one)
    sql_query = sql_query.rstrip(";") + ";"

    # Fix improperly escaped single quotes (replace duplicate '' with ')
    sql_query = re.sub(r"''([^'])", r"'\1", sql_query)  # Replace ''Bob'' → 'Bob'

    # Ensure quotes are correctly closed before semicolons
    sql_query = re.sub(r"= '([^']+);", r"= '\1';", sql_query)  # Fix `lastname = 'Williams;` → `lastname = 'Williams';`

    # Ensure proper SQL formatting (convert newlines to spaces, remove extra spaces)
    sql_query = sql_query.replace("\n", " ").strip()
    sql_query = re.sub(r"\s+", " ", sql_query)  # Normalize whitespace

    return sql_query







import os
from openai import OpenAI

DATA = get_build_team_data()    # Includes information about employees (profile, experience...)

def build_team(description, model, temperature, certainty_threshold, api_key):
    try:
        api_key = os.getenv("OPENAI_API_KEY")    
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is missing.")
        
        agent = OpenAI(api_key=api_key, timeout=60)  # Adjust timeout
        if not agent:
            raise ValueError("Invalid OpenAI API Key")

        system_prompt = (
            "You are an AI HR assistant helping managers build project teams by selecting employees based on their roles, skills, availability, and past validated tasks. "
            "Your goal is to first generate an **Ideal Team Composition** based on the project requirements, then match the best employees from the provided dataset (`DATA`)."

            "\n\n### Project Description & Requirements:\n"
            f"{description}\n\n"

            "### Part 1: Ideal Team Composition (General Roles & Skills)\n"
            "- Identify key roles needed for this project.\n"
            "- List essential skills and experience levels required for each role, considering that **junior employees are also suitable** for some positions.\n"
            "- Estimate the number of team members required per role, aiming for a **small, efficient team**\n\n"
            "- This section should **not** consider the provided employee data (`DATA`).\n\n"

            "### Part 2: Matching Employees from Provided Data\n"
            "From the available employees in the dataset (`DATA`), match the best candidates based on:\n"
            "- **Role**: Must align with the required project roles.\n"
            "- **Skills & Proficiency Level**: Match required skills as closely as possible.\n"
            "- **Years of Experience**: Consider experience relevant to the role.\n"
            "- **Validated Tasks**: Prior successful tasks should be prioritized.\n"
            
            "Here are some example employees from the dataset (ensure you are matching roles correctly):\n"
            f"{DATA}\n\n" 

            "### Output Format:\n"
            " **Required Profiles: **\n"
            "- Role 1: [Required Skills, Experience Level]"
            "- Role 2: [Required Skills, Experience Level]"
            "- (Continue listing all required roles)"

            "**Matching Employees**:\n"
            "- Role 1: [employee_1, employee_2, ...]\n"
            "- Role 2: [employee3, employee_4 ...]\n"
            "- (Continue listing all roles with matched Employee firstname and lastname only)\n\n"

            "Important Notes:\n"
            "- **Only use employees from `DATA`**, as it already contains only available profiles.\n"
            "- Ensure optimal team composition based on the best possible matches.\n"
            "- If no exact match is found, suggest the closest alternative."
        )
        
        response = agent.chat.completions.create(
            model = model,  
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": description}],
            max_tokens = 800,
            temperature = temperature,
            logprobs = True
        )
        
        if response.choices:
            recommendation = response.choices[0].message.content
        else:
            raise ValueError("No valid choices in the response.")

                # The log probabilities of each output token reflecting certainty    
        token_log_prob = response.choices[0].logprobs   
        
        # Convert logprobs to probabilities
        if token_log_prob and hasattr(token_log_prob, "content"):
            token_probabilities = [
                {"token": token_data.token, "probability": round(math.exp(token_data.logprob), 3)}
                for token_data in token_log_prob.content
            ]
            
            min_prob = min(tp['probability'] for tp in token_probabilities)
            avg_prob = round(sum(tp['probability'] for tp in token_probabilities) / len(token_probabilities),2)
            
            # Check if min_prov and avg_prob are above threshold to confirm accuracy
            valid_prob_threshold = min_prob > 0.2 and avg_prob > certainty_threshold
            
        else:
            token_probabilities = []
            valid_prob_threshold = False
            
        # Extract additional response data
        team_builder_response_data = {
            'response_id': response.id,
            'finish_reason': finish_reason_dict.get(response.choices[0].finish_reason, "Unknown reason"), 
            'total_tokens': response.usage.total_tokens,
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'cached_tokens': max(0, response.usage.prompt_tokens - response.usage.completion_tokens),
            #'token_prob':token_probabilities,
            'min_prob': min_prob,
            'avg_prob': avg_prob,
            'certainty_threshold': certainty_threshold,
            'valid_prob_threshold': valid_prob_threshold,
            'model': response.model,
            'temparature': temperature
        }
        
        return recommendation , team_builder_response_data

    except Exception as e:
        logger.error(f"Error occurred in build_team function: {str(e)}")
        return {"error": "An error occurred while generating team composition."}
