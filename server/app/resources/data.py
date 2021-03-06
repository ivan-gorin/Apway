from flask_restful import Resource, reqparse
from app.common.models import DataFormat, BaseEntity, DataSet, Task,\
 ExperimentEnvironment, ProgramImplementation, Experiment, DataSetList, ExperimentResult, Client
from datetime import datetime
from app import db
from sqlalchemy.exc import IntegrityError
from copy import deepcopy
import re
import threading
import requests
import sys
import os

from app import app

regex = re.compile(
    r'^(?:http|ftp)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
    r'localhost|' #localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def check_uri(uri):
    return re.match(regex, uri)

def delete_BaseEntity(id):
    to_delete = BaseEntity.query.filter_by(Id=id).first()
    if to_delete is None:
        return False
    db.session.delete(to_delete)
    db.session.commit()
    return True

def create_BaseEntity():
    current_time = datetime.now()
    baseentity = BaseEntity(Author='user', TimeCreated=current_time, TimeLastEdited=current_time)
    db.session.add(baseentity)
    db.session.commit()
    return baseentity

def check_database(model, id):
    query = model.query.filter_by(Id=id).first()
    if query is None:
        return False
    else:
        return True

def try_download_impl(id):
    implementation = ProgramImplementation.query.filter_by(Id=id).first()
    url = implementation.FileURL
    if implementation.ProgramType == 'Exec':
        filename = f'{id}_impl.exe'
    elif implementation.ProgramType == 'Python':
        filename = f'{id}_impl.py'
    elif implementation.ProgramType == 'PythonZip':
        filename = f'{id}_impl.zip'
    filepath = os.path.join(app.config['IMPLEMENTATION_DIR'], filename)
    try:
        with requests.get(url, allow_redirects=True, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except:
        print(sys.exc_info())
        implementation.Status = 'Incorrect'
        db.session.commit()
        return
    implementation.Status = 'Active'
    implementation.DownloadSuccess = 'True'
    implementation.FilePath = filename
    db.session.commit()
    
dataformat_parser = reqparse.RequestParser()
dataformat_parser.add_argument('FormatName', type=str, required=True)
dataformat_parser.add_argument('FormatType', type=str, required=True)
dataformat_parser.add_argument('FormatSchema', type=str)
dataformat_parser.add_argument('FormatExample', type=str)

class RouteDataformat(Resource):
    def get(self, id=None):
        if id is None:
            query = DataFormat.query.order_by(DataFormat.Id)
            return [i.as_dict() for i in query]
        else:
            query = DataFormat.query.filter_by(Id=id).first()
            if query is None:
                return f'DataFormat with id={id} not found.', 404
            return query.as_dict(), 200

    def post(self):
        args = dataformat_parser.parse_args(strict=True)

        if args['FormatType'] not in {'File', 'Table'}:
            return f"Unknown FormatType.", 400

        baseentity = create_BaseEntity()

        try:
            new_dataformat = DataFormat(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_dataformat)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity Error.', 400

        return new_dataformat.as_dict(), 201

    def delete(self, id):
        to_delete = DataFormat.query.filter_by(Id=id).first()
        if to_delete is None:
            return f'DataFormat with id={id} not found.', 404
        be_id = to_delete.BaseEntityId
        try:
            db.session.delete(to_delete)
            db.session.commit()
            delete_BaseEntity(be_id)
            return 200
        except IntegrityError:
            db.session.rollback()
            return 'Integrity Error.', 400

dataset_parser = reqparse.RequestParser()
dataset_parser.add_argument('DataFormatId', type=int, required=True)
dataset_parser.add_argument('Content', type=str, required=True)

class RouteDataset(Resource):
    def get(self, id=None):
        if id is None:
            query = DataSet.query.order_by(DataSet.Id)
            return [i.as_dict() for i in query]
        else:
            query = DataSet.query.filter_by(Id=id).first()
            if query is None:
                return f'DataSet with id={id} not found.', 404
            return query.as_dict(), 200
    
    def post(self):
        args = dataset_parser.parse_args(strict=True)

        if not check_database(DataFormat, args['DataFormatId']):
            return f"DataFormat with id={args['DataFormatId']} not found.", 404

        baseentity = create_BaseEntity()

        try:
            new_dataset = DataSet(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_dataset)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity Error.', 400

        return new_dataset.as_dict(), 201
    
    def delete(self, id):
        to_delete = DataSet.query.filter_by(Id=id).first()
        if to_delete is None:
            return f'DataSet with id={id} not found.', 404
        be_id = to_delete.BaseEntityId
        try:
            db.session.delete(to_delete)
            db.session.commit()
            delete_BaseEntity(be_id)
            return 'Success', 200
        except IntegrityError:
            db.session.rollback()
            return 'Integrity Error.', 400


task_parser = reqparse.RequestParser()
task_parser.add_argument('Title', type=str, required=True)
task_parser.add_argument('Input', type=str, required=True)
task_parser.add_argument('Output', type=str, required=True)
task_parser.add_argument('DefaultInputFormat', type=int, required=True)
task_parser.add_argument('DefaultOutputFormat', type=int, required=True)
task_parser.add_argument('ResultQuality', type=str, required=True)

class RouteTask(Resource):
    def get(self, id=None):
        if id is None:
            query = Task.query.order_by(Task.Id)
            return [i.as_dict() for i in query]
        else:
            query = Task.query.filter_by(Id=id).first()
            if query is None:
                return f'Task with id={id} not found.', 404
            return query.as_dict(), 200
    
    def post(self):
        args = task_parser.parse_args(strict=True)

        if not check_database(DataFormat, args['DefaultInputFormat']):
            return f"DataFormat with id={args['DefaultInputFormat']} not found.", 404
        if not check_database(DataFormat, args['DefaultOutputFormat']):
            return f"DataFormat with id={args['DefaultOutputFormat']} not found.", 404
        if args['Input'] not in {'File', 'Table'}:
            return f"Unknown Input Type.", 400
        if args['Output'] not in {'File', 'Table'}:
            return f"Unknown Output Type.", 400

        baseentity = create_BaseEntity()

        try:
            new_task = Task(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_task)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity Error.', 400

        return new_task.as_dict(), 201
    
    def delete(self, id):
        to_delete = Task.query.filter_by(Id=id).first()
        if to_delete is None:
            return f'Task with id={id} not found.', 404
        be_id = to_delete.BaseEntityId
        try:
            db.session.delete(to_delete)
            db.session.commit()
            delete_BaseEntity(be_id)
            return 'Success', 200
        except IntegrityError:
            db.session.rollback()
            return 'Integrity Error.', 400


environment_parser = reqparse.RequestParser()
environment_parser.add_argument('OS', type=str, required=True)
environment_parser.add_argument('Processor', type=str, required=True)
environment_parser.add_argument('Memory', type=str, required=True)
environment_parser.add_argument('HDD', type=int, required=True)

class RouteEnvironment(Resource):
    def get(self, id=None):
        if id is None:
            query = ExperimentEnvironment.query.order_by(ExperimentEnvironment.Id)
            return [i.as_dict() for i in query]
        else:
            query = ExperimentEnvironment.query.filter_by(Id=id).first()
            if query is None:
                return f'ExperimentEnvironment with id={id} not found.', 404
            return query.as_dict(), 200
    
    def post(self):
        args = environment_parser.parse_args(strict=True)

        if args['OS'] not in {'Win', 'Linux', 'MacOS'}:
            return f"Unknown OS={args['OS']}.", 400

        baseentity = create_BaseEntity()

        try:
            new_obj = ExperimentEnvironment(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_obj)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity Error.', 400

        return new_obj.as_dict(), 201
    
    def delete(self, id):
        to_delete = ExperimentEnvironment.query.filter_by(Id=id).first()
        if to_delete is None:
            return f'ExperimentEnvironment with id={id} not found.', 404
        be_id = to_delete.BaseEntityId
        try:
            db.session.delete(to_delete)
            db.session.commit()
            delete_BaseEntity(be_id)
            return 'Success', 200
        except IntegrityError:
            db.session.rollback()
            return 'Integrity Error.', 400

implementation_parser = reqparse.RequestParser()
implementation_parser.add_argument('OS', type=str, required=True)
implementation_parser.add_argument('EnvironmentId', type=int, required=True)
implementation_parser.add_argument('TaskId', type=int, required=True)
implementation_parser.add_argument('InputFormat', type=int, required=True)
implementation_parser.add_argument('OutputFormat', type=int, required=True)
implementation_parser.add_argument('CommandLineArgs', type=str)
implementation_parser.add_argument('FileURL', type=str, required=True)
implementation_parser.add_argument('DataProcessing', type=int, required=True)
implementation_parser.add_argument('ProgramType', type=str, required=True)
implementation_parser.add_argument('PythonRequirements', type=str)

class RouteImplementation(Resource):
    def get(self, id=None):
        if id is None:
            query = ProgramImplementation.query.order_by(ProgramImplementation.Id)
            return [i.as_dict() for i in query]
        else:
            query = ProgramImplementation.query.filter_by(Id=id).first()
            if query is None:
                return f'ProgramImplementation with id={id} not found.', 404
            return query.as_dict(), 200
    
    def post(self):
        args = implementation_parser.parse_args(strict=True)

        if not check_database(DataFormat, args['InputFormat']):
            return f"DataFormat with id={args['InputFormat']} not found.", 404
        if not check_database(DataFormat, args['OutputFormat']):
            return f"DataFormat with id={args['OutputFormat']} not found.", 404
        if not check_database(ExperimentEnvironment, args['EnvironmentId']):
            return f"ExperimentEnvironment with id={args['EnvironmentId']} not found.", 404
        if not check_database(Task, args['TaskId']):
            return f"Task with id={args['TaskId']} not found.", 404
        if args['OS'] not in {'Win', 'Linux', 'MacOS'}:
            return f"Unknown OS={args['OS']}.", 400
        if args['ProgramType'] not in {'Python', 'PythonZip', 'Exec'}:
            return f"Unknown ProgramType={args['ProgramType']}.", 400
        
        if not check_uri(args['FileURL']):
            return f"Malformed File URL.", 400
        if (args['PythonRequirements'] is not None) and (not check_uri(args['PythonRequirements'])):
            return f"Malformed PythonRequirements URI.", 400
        
        task = Task.query.filter_by(Id=args['TaskId']).first()
        if task.DefaultInputFormat != args['InputFormat']:
            return f"Input formats do not match.", 400
        if task.DefaultOutputFormat != args['OutputFormat']:
            return f"Output formats do not match.", 400

        baseentity = create_BaseEntity()

        try:
            new_obj = ProgramImplementation(**args, BaseEntityId=baseentity.Id, Status='Downloading', DownloadSuccess='False')
            db.session.add(new_obj)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity Error.', 400
        
        threading.Thread(group=None, target=try_download_impl, args=(new_obj.Id,)).start()

        return new_obj.as_dict(), 201
    
    def delete(self, id):
        to_delete = ProgramImplementation.query.filter_by(Id=id).first()
        if to_delete is None:
            return f'ProgramImplementation with id={id} not found.', 404
        be_id = to_delete.BaseEntityId
        try:
            db.session.delete(to_delete)
            db.session.commit()
            delete_BaseEntity(be_id)
            return 'Success', 200
        except IntegrityError:
            db.session.rollback()
            return 'Integrity Error.', 400

experiment_parser = reqparse.RequestParser()
experiment_parser.add_argument('Title', type=str, required=True)
experiment_parser.add_argument('TitleShort', type=str, required=True)
experiment_parser.add_argument('Comment', type=str)
experiment_parser.add_argument('DataSets', type= lambda x: list(x.split(',')), required=True)
experiment_parser.add_argument('BaseLine', type=str)
experiment_parser.add_argument('RefRes', type=str)
experiment_parser.add_argument('EnvironmentId', type=int, required=True)
experiment_parser.add_argument('TaskId', type=int, required=True)


class RouteExperiment(Resource):
    def get(self, id=None):
        if id is None:
            query = Experiment.query.order_by(Experiment.Id)
            return [i.as_dict() for i in query]
        else:
            query = Experiment.query.filter_by(Id=id).first()
            if query is None:
                return f'Experiment with id={id} not found.', 404
            datasets_query = DataSetList.query.filter_by(ExperimentId=id).all()
            result = query.as_dict()
            result['DataSets'] = [i.DataSetId for i in datasets_query]
            return result, 200
    
    def post(self):
        args = experiment_parser.parse_args(strict=True)
        datasets = deepcopy(args['DataSets'])
        args.pop('DataSets')

        if not check_database(ExperimentEnvironment, args['EnvironmentId']):
            return f"ExperimentEnvironment with id={args['EnvironmentId']} not found.", 404
        if not check_database(Task, args['TaskId']):
            return f"Task with id={args['TaskId']} not found.", 404

        task = Task.query.filter_by(Id=args['TaskId']).first()
        for id in datasets:
            if not check_database(DataSet, id):
                return f"DataSet with id={id} not found.", 404
            dataset = DataSet.query.filter_by(Id=id).first()
            if dataset.DataFormatId != task.DefaultInputFormat:
                return f"DataSet Format does not match Task DefaultInputFormat.", 400

        baseentity = create_BaseEntity()

        try:
            new_obj = Experiment(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_obj)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity Error.', 400
        
        for id in datasets:
            node = DataSetList(DataSetId=id, ExperimentId=new_obj.Id)
            db.session.add(node)

        db.session.commit()

        return new_obj.as_dict(), 201

run_parser = reqparse.RequestParser()
run_parser.add_argument('ExperimentId', type=int, required=True)
run_parser.add_argument('ProgramImplementationId', type=int, required=True)
run_parser.add_argument('OutputString', type=str)

class RouteRun(Resource):
    def get(self, id=None):
        if id is None:
            query = ExperimentResult.query.order_by(ExperimentResult.Id)
            return [i.as_dict() for i in query]
        else:
            query = ExperimentResult.query.filter_by(Id=id).first()
            if query is None:
                return f'ExperimentResult with id={id} not found.', 404
            return query.as_dict(), 200

    def post(self):
        args = run_parser.parse_args(strict=True)

        if not check_database(Experiment, args['ExperimentId']):
            return f"ExperimentId with id={args['ExperimentId']} not found.", 404
        if not check_database(ProgramImplementation, args['ProgramImplementationId']):
            return f"ProgramImplementationId with id={args['ProgramImplementationId']} not found.", 404

        experiment = Experiment.query.filter_by(Id=args['ExperimentId']).first()
        implementation = ProgramImplementation.query.filter_by(Id=args['ProgramImplementationId']).first()
        if experiment.TaskId != implementation.TaskId:
            return f"TaskIds do not match.", 400
        if experiment.EnvironmentId != implementation.EnvironmentId:
            return f"EnvironmentIds do not match.", 400
        
        output_format = DataFormat.query.filter_by(Id=implementation.OutputFormat).first()
        if output_format.FormatType == 'Table' and args['OutputString'] is None:
            return f"OutputString required but not specified.", 400

        baseentity = create_BaseEntity()

        try:
            new_obj = ExperimentResult(**args, BaseEntityId=baseentity.Id, RunStatus='Pending')
            db.session.add(new_obj)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity Error.', 400

        return new_obj.as_dict(), 201

client_parser = reqparse.RequestParser()
client_parser.add_argument('ClientIP', type=str, required=True)
client_parser.add_argument('ClientPort', type=str, required=True)

class RouteClient(Resource):
    def get(self, id=None):
        if id is None:
            query = Client.query.order_by(Client.Id)
            return [i.as_dict() for i in query]
        else:
            query = Client.query.filter_by(Id=id).first()
            if query is None:
                return f'Client with id={id} not found.', 404
            return query.as_dict(), 200

    def post(self):
        args = client_parser.parse_args(strict=True)

        try:
            new_obj = Client(**args, Busy=False)
            db.session.add(new_obj)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            db.session.rollback()
            return 'Integrity Error.', 400
        
        url = 'http://' + new_obj.ClientIP + ':' + new_obj.ClientPort + '/set_client/' + str(new_obj.Id)
        requests.post(url)

        return new_obj.as_dict(), 201

    def delete(self, id):
        app.mutex.acquire()
        to_delete = Client.query.filter_by(Id=id).first()
        if to_delete is None:
            return f'Client with id={id} not found.', 404
        if to_delete.Busy:
            return f'Client Busy.', 400
        
        be_id = to_delete.BaseEntityId
        try:
            db.session.delete(to_delete)
            db.session.commit()
            delete_BaseEntity(be_id)
            app.mutex.release()
            return 'Success', 200
        except IntegrityError:
            db.session.rollback()
            app.mutex.release()
            return 'Integrity Error.', 400