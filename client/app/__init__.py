from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask import request
import os


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
api = Api(app)
jwt = JWTManager(app)

os.makedirs(app.config['IMPLEMENTATION_DIR'], exist_ok=True)

from app.resources.data import run_experiment

api.add_resource(run_experiment, '/run/<int:id>')

from app.common.models import Client

@app.route('/set_client/<int:id>', methods=['POST'])
def set_client(id):
    query = Client.query.filter_by(Id=id).first()
    if query is None:
        return 'Client not found.', 404
    app.config['CLIENT_ID'] = id
    return 'Success.', 200

@app.route('/test')
def test():
    print(app.config['CLIENT_ID'])

# @app.before_first_request
# def before_first_request():