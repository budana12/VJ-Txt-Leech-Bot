import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# Create Flask app
app = Flask(__name__)

# Configure app
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///engineersbabu.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy", "message": "Engineers Babu API is running"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)