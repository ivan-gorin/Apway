import os
from sqlalchemy.engine import URL
import sqlalchemy as sa

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my_secret_string_key'
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=ApwayDB;UID=python_login;PWD=1234"
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or connection_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENV_FILE_LOCATION = os.environ.get('ENV_FILE_LOCATION')
    IMPLEMENTATION_DIR = os.environ.get('IMPLEMENTATION_DIR') or r'C:\Users\ivang\Documents\PythonCode\implementations'
    # SECRET_KEY = os.getenv('SECRET_KEY', 'my_precious')