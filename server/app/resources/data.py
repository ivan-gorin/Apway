from flask_restful import Resource, reqparse
from app.common.models import DataFormat, BaseEntity, DataSet, Task,\
 ExperimentEnvironment, ProgramImplementation, Experiment, DataSetList, ExperimentResult
from datetime import datetime
from app import db
from sqlalchemy.exc import IntegrityError
from copy import deepcopy

dataformat_parser = reqparse.RequestParser()
dataformat_parser.add_argument('FormatType', type=str, required=True)
dataformat_parser.add_argument('FormatSchema', type=str)
dataformat_parser.add_argument('FormatExample', type=str)

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

class dataformats(Resource):
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

        baseentity = create_BaseEntity()

        try:
            new_dataformat = DataFormat(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_dataformat)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity error', 400

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
            return 'Integrity error', 400

dataset_parser = reqparse.RequestParser()
dataset_parser.add_argument('DataFormatId', type=int, required=True)
dataset_parser.add_argument('Content', type=str, required=True)

class datasets(Resource):
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
            return 'Integrity error', 400

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
            return 'Integrity error', 400


task_parser = reqparse.RequestParser()
task_parser.add_argument('Title', type=str, required=True)
task_parser.add_argument('Input', type=str, required=True)
task_parser.add_argument('Output', type=str, required=True)
task_parser.add_argument('DefaultInputFormat', type=int, required=True)
task_parser.add_argument('DefaultOutputFormat', type=int, required=True)
task_parser.add_argument('ResultQuality', type=str, required=True)

class tasks(Resource):
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

        baseentity = create_BaseEntity()

        try:
            new_task = Task(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_task)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity error', 400

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
            return 'Integrity error', 400


environment_parser = reqparse.RequestParser()
environment_parser.add_argument('OS', type=str, required=True)
environment_parser.add_argument('Processor', type=str, required=True)
environment_parser.add_argument('Memory', type=str, required=True)
environment_parser.add_argument('HDD', type=int, required=True)

class environments(Resource):
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

        baseentity = create_BaseEntity()

        try:
            new_obj = ExperimentEnvironment(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_obj)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity error', 400

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
            return 'Integrity error', 400

implementation_parser = reqparse.RequestParser()
implementation_parser.add_argument('OS', type=str, required=True)
implementation_parser.add_argument('EnvironmentId', type=int, required=True)
implementation_parser.add_argument('TaskId', type=int, required=True)
implementation_parser.add_argument('InputFormat', type=int, required=True)
implementation_parser.add_argument('OutputFormat', type=int, required=True)
implementation_parser.add_argument('CommandLineArgs', type=str)
implementation_parser.add_argument('Blob', type=str, required=True)
implementation_parser.add_argument('DataProcessing', type=int, required=True)

class implementations(Resource):
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
        
        task = Task.query.filter_by(Id=args['TaskId']).first()
        if task.DefaultInputFormat != args['InputFormat']:
            return f"Input formats do not match.", 404
        if task.DefaultOutputFormat != args['OutputFormat']:
            return f"Output formats do not match.", 404

        baseentity = create_BaseEntity()

        try:
            new_obj = ProgramImplementation(**args, BaseEntityId=baseentity.Id, Status='Working')
            db.session.add(new_obj)
            db.session.commit()
        except IntegrityError as e:
            print(e)
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity error', 400

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
            return 'Integrity error', 400

experiment_parser = reqparse.RequestParser()
experiment_parser.add_argument('Title', type=str, required=True)
experiment_parser.add_argument('TitleShort', type=str, required=True)
experiment_parser.add_argument('Comment', type=str)
experiment_parser.add_argument('DataSets', type= lambda x: list(x.split(',')), required=True)
experiment_parser.add_argument('BaseLine', type=str)
experiment_parser.add_argument('RefRes', type=str)
experiment_parser.add_argument('EnvironmentId', type=int, required=True)
experiment_parser.add_argument('TaskId', type=int, required=True)


class experiments(Resource):
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
            return 'Integrity error', 400
        
        for id in datasets:
            node = DataSetList(DataSetId=id, ExperimentId=new_obj.Id)
            db.session.add(node)

        db.session.commit()

        return new_obj.as_dict(), 201

run_parser = reqparse.RequestParser()
run_parser.add_argument('ExperimentId', type=int, required=True)
run_parser.add_argument('ProgramImplementationId', type=int, required=True)

class run(Resource):
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

        baseentity = create_BaseEntity()

        try:
            new_obj = ExperimentResult(**args, BaseEntityId=baseentity.Id)
            db.session.add(new_obj)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            delete_BaseEntity(baseentity.Id)
            return 'Integrity error', 400

        return new_obj.as_dict(), 201

