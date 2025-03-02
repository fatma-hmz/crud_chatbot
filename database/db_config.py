import os
from dotenv import load_dotenv

#load_dotenv()

#DB_CONFIG = {
#    "dbname": os.getenv("POSTGRES_DB"),
#    "user": os.getenv("DB_USER"),
#    "password": os.getenv("DB_PASSWORD"),
#    "host": os.getenv("DB_HOST"),
#    "port": os.getenv("DB_PORT")
#}

import streamlit as st

# Access database credentials from Streamlit secrets
DB_CONFIG = {
    "dbname": st.secrets["postgres"]["dbname"],
    "user": st.secrets["postgres"]["user"],
    "password": st.secrets["postgres"]["password"],
    "host": st.secrets["postgres"]["host"],
    "port": st.secrets["postgres"]["port"]
}
