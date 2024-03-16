import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://yourusername:yourpassword@localhost/yourdbname'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Add any other configuration parameters here as needed
