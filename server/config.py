import os
from sqlalchemy.engine import URL
import sqlalchemy as sa

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my_secret_string_key'
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=ApwayDB;UID=python_login;PWD=1234"
    connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or connection_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
