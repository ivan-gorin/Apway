from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    Id = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(64), index=True, unique=True)
    PasswordHash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.Username)

    def set_password(self, password):
        self.PasswordHash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.PasswordHash, password)
    
    def get_id(self):
        return (self.Id)

class BaseEntity(db.Model):
    __tablename__ = 'BaseEntity'
    Id = db.Column(db.Integer, primary_key=True)
    Author = db.Column(db.String(128))
    TimeCreated = db.Column(db.DateTime)
    TimeLastEdited = db.Column(db.DateTime)
    PreviousVersion = db.Column(db.Integer)

class Tag(db.Model):
    __tablename__ = 'Tag'
    Id = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.String(128))
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

class DataFormat(db.Model):
    __tablename__ = 'DataFormat'
    Id = db.Column(db.Integer, primary_key=True)
    FormatType = db.Column(db.String(128))
    FormatSchema = db.Column(db.String(4000))
    FormatExample = db.Column(db.String(4000))
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class DataSet(db.Model):
    __tablename__ = 'DataSet'
    Id = db.Column(db.Integer, primary_key=True)
    DataFormatId = db.Column(db.Integer, db.ForeignKey(DataFormat.Id))
    Content = db.Column(db.String(128))
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Task(db.Model):
    __tablename__ = 'Task'
    Id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(128), unique=True)
    Input = db.Column(db.String(128))
    DefaultInputFormat = db.Column(db.Integer, db.ForeignKey(DataFormat.Id))
    Output = db.Column(db.String(128))
    DefaultOutputFormat = db.Column(db.Integer, db.ForeignKey(DataFormat.Id))
    ResultQuality = db.Column(db.String(128))
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class SubTaskList(db.Model):
    __tablename__ = 'SubTaskList'
    Id = db.Column(db.Integer, primary_key=True)
    TaskId = db.Column(db.Integer, db.ForeignKey(Task.Id))
    BaseTaskId = db.Column(db.Integer, db.ForeignKey(Task.Id))

class DataConverter(db.Model):
    __tablename__ = 'DataConverter'
    Id = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.String(128))
    InputFormatId = db.Column(db.Integer, db.ForeignKey(DataFormat.Id))
    OutputFormatId = db.Column(db.Integer, db.ForeignKey(DataFormat.Id))
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

class ExperimentEnvironment(db.Model):
    __tablename__ = 'ExperimentEnvironment'
    Id = db.Column(db.Integer, primary_key=True)
    OS = db.Column(db.String(128))
    Processor = db.Column(db.String(128))
    Memory = db.Column(db.Integer)
    HDD = db.Column(db.Integer)
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Experiment(db.Model):
    __tablename__ = 'Experiment'
    Id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(128))
    TitleShort = db.Column(db.String(128))
    Comment = db.Column(db.String(128))
    BaseLine = db.Column(db.String(128))
    RefRes = db.Column(db.String(128))
    EnvironmentId = db.Column(db.Integer, db.ForeignKey(ExperimentEnvironment.Id))
    TaskId = db.Column(db.Integer, db.ForeignKey(Task.Id))
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class DataSetList(db.Model):
    __tablename__ = 'DataSetList'
    Id = db.Column(db.Integer, primary_key=True)
    DataSetId = db.Column(db.Integer, db.ForeignKey(DataSet.Id))
    ExperimentId = db.Column(db.Integer, db.ForeignKey(Experiment.Id))

class ProgramImplementation(db.Model):
    __tablename__ = 'ProgramImplementation'
    Id = db.Column(db.Integer, primary_key=True)
    Status = db.Column(db.String(128))
    OS = db.Column(db.String(128))
    EnvironmentId = db.Column(db.Integer, db.ForeignKey(ExperimentEnvironment.Id))
    TaskId = db.Column(db.Integer, db.ForeignKey(Task.Id))
    InputFormat = db.Column(db.Integer, db.ForeignKey(DataFormat.Id))
    OutputFormat = db.Column(db.Integer, db.ForeignKey(DataFormat.Id))
    CommandLineArgs = db.Column(db.String(4000))
    Blob = db.Column(db.String(128))
    DataProcessing = db.Column(db.Integer)
    ProgramType = db.Column(db.String(128))
    PythonRequirements = db.Column(db.String(128))
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class ExperimentResult(db.Model):
    __tablename__ = 'ExperimentResult'
    Id = db.Column(db.Integer, primary_key=True)
    ExperimentId = db.Column(db.Integer, db.ForeignKey(Experiment.Id))
    ProgramImplementationId = db.Column(db.Integer, db.ForeignKey(ProgramImplementation.Id))
    StartTime = db.Column(db.DateTime)
    StopTime = db.Column(db.DateTime)
    LogReference = db.Column(db.String(128))
    BaseEntityId = db.Column(db.Integer, db.ForeignKey(BaseEntity.Id))

class ValueList(db.Model):
    __tablename__ = 'ValueList'
    Id = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.Integer, db.ForeignKey(DataSet.Id))
    ExperimentResultId = db.Column(db.Integer, db.ForeignKey(ExperimentResult.Id))

class CommentList(db.Model):
    __tablename__ = 'CommentList'
    Id = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.String(4000))
    ExperimentResultId = db.Column(db.Integer, db.ForeignKey(ExperimentResult.Id))