#!/bin/bash

# Exit script on error
set -e

# Setup Python environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
export FLASK_APP=run.py
export FLASK_ENV=development
export SECRET_KEY='your-secret-key'
export SQLALCHEMY_DATABASE_URI='postgresql://username:password@localhost/housescraper_db'

# Initialize the database
flask db init
flask db migrate -m "Initial migration."
flask db upgrade

# Inform the user of the completion
echo "Setup completed. You can now run the Flask app with 'flask run'."