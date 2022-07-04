import os

SECRET_KEY = os.urandom(32)

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

WTF_CSRF_SECRET_KEY = os.getenv('357774788')

WTF_CSRF_ENABLED = False

# Connect to the database
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:@localhost:5432/fyyur'