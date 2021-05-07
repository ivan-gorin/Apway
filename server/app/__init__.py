from flask import Flask, send_from_directory, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_jwt_extended import JWTManager
import threading
import time
import os


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
api = Api(app)
# jwt = JWTManager(app)

from app.resources.data import dataformats, datasets, tasks, environments, implementations, experiments

api.add_resource(dataformats, '/data/formats', '/data/formats/<int:id>')
api.add_resource(datasets, '/data/sets', '/data/sets/<int:id>')
api.add_resource(tasks, '/tasks', '/tasks/<int:id>')
api.add_resource(environments, '/experiment/environments', '/experiment/environments/<int:id>')
api.add_resource(implementations, '/implementations', '/implementations/<int:id>')
api.add_resource(experiments, '/experiment/experiments', '/experiment/experiments/<int:id>')


@app.route('/implementation_download/<path:filename>')
def impl_download(filename):
    try:
        if not os.path.exists(os.path.join(app.config['IMPLEMENTATION_DIR'], filename)):
            raise FileNotFoundError
        return send_from_directory(
            os.path.join(app.config['IMPLEMENTATION_DIR'], ''),
            filename
        )
    except FileNotFoundError:
        return 'File not found.', 404
    except:
        return 'Error downloading the file.', 500

# @app.before_first_request
# def before_first_request():
#     """Start a background thread that launches tasks when machines are available."""

#     def launch_pending_tasks():
#         while True:
#             print('LOOP')
#             time.sleep(1)

#     if not app.config['TESTING']:
#         thread = threading.Thread(target=launch_pending_tasks)
#         thread.start()