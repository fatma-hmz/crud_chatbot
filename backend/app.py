from flask import Flask
from flask_cors import CORS  
from backend.routes import query_blueprint

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

app.register_blueprint(query_blueprint)  

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
