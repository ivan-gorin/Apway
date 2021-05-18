from flask import Flask, send_from_directory, jsonify
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_jwt_extended import JWTManager
import threading
import time
import os
import requests


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
api = Api(app)
# jwt = JWTManager(app)
mutex = threading.Lock()

from app.resources.data import RouteDataformat, RouteDataset, RouteTask,\
     RouteEnvironment, RouteImplementation, RouteExperiment, RouteRun, RouteClient

api.add_resource(RouteDataformat, '/data/formats', '/data/formats/<int:id>')
api.add_resource(RouteDataset, '/data/sets', '/data/sets/<int:id>')
api.add_resource(RouteTask, '/tasks', '/tasks/<int:id>')
api.add_resource(RouteEnvironment, '/experiment/environments', '/experiment/environments/<int:id>')
api.add_resource(RouteImplementation, '/implementations', '/implementations/<int:id>')
api.add_resource(RouteExperiment, '/experiment/experiments', '/experiment/experiments/<int:id>')
api.add_resource(RouteRun, '/experiment/run')
api.add_resource(RouteClient, '/client')

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

from app.common.models import ExperimentResult, Client

@app.before_first_request
def before_first_request():
    """Start a background thread that launches tasks when machines are available."""

    def launch_pending_tasks():
        while True:
            time.sleep(5)
            print('LOOP')
            pending = ExperimentResult.query.filter_by(RunStatus='Pending').all()
            if len(pending) == 0:
                continue
            for i in pending:
                mutex.acquire()
                free_client = Client.query.filter_by(Busy=False).first()
                if free_client is None:
                    break
                free_client.Busy = True
                i.RunStatus = 'Running'
                db.session.commit()
                mutex.release()
                url = 'http://' + free_client.ClientIP + ':' + free_client.ClientPort + '/run/' + str(i.Id)
                requests.post(url)

    if not app.config['TESTING']:
        thread = threading.Thread(target=launch_pending_tasks)
        thread.start()