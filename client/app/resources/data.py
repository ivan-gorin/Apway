from flask_restful import Resource, reqparse
from app.common.models import DataFormat, BaseEntity, DataSet, Task,\
 ExperimentEnvironment, ProgramImplementation, Experiment, DataSetList, ExperimentResult
from datetime import datetime
from app import db
from sqlalchemy.exc import IntegrityError
from copy import deepcopy

def check_database(model, id):
    query = model.query.filter_by(Id=id).first()
    if query is None:
        return False
    else:
        return True

run_parser = reqparse.RequestParser()
run_parser.add_argument('ExperimentResultId', type=int, required=True)

class run_experiment(Resource):
    def post(self):
        args = run_parser.parse_args(strict=True)
        if not check_database(ExperimentResult, args['ExperimentResultId']):
            return f'ExperimentResult not found.', 404

        experimentresult = ExperimentResult.query.filter_by(Id=args['ExperimentResultId']).first()
        implementation = ProgramImplementation.query.filter_by(Id=experimentresult.ProgramImplementationId).first()
        task = Task.query.filter_by(Id=experimentresult.TaskId).first()
        file_uri = implementation.Blob

        

        start_time = datetime.now()

        # RUN EXPERIMENT

        return 200

