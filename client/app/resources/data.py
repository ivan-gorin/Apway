from flask_restful import Resource, reqparse
from app.common.models import DataFormat, BaseEntity, DataSet, Task,\
 ExperimentEnvironment, ProgramImplementation, Experiment, DataSetList, ExperimentResult, Client
from datetime import datetime
from app import db
from sqlalchemy.exc import IntegrityError
from copy import deepcopy
from app import app
from urllib import parse
import os, sys, threading, requests, subprocess, shlex

def check_database(model, id):
    query = model.query.filter_by(Id=id).first()
    if query is None:
        return False
    else:
        return True

def run_impl(id):
    start_time = datetime.now()

    this_client = Client.query.filter_by(Id=app.config['CLIENT_ID']).first()
    experimentresult = ExperimentResult.query.filter_by(Id=id).first()
    implementation = ProgramImplementation.query.filter_by(Id=experimentresult.ProgramImplementationId).first()
    experiment = Experiment.query.filter_by(Id=experimentresult.ExperimentId).first()
    filename = implementation.FilePath
    filepath = os.path.join(app.config['IMPLEMENTATION_DIR'], filename)
    addr = parse.urljoin(app.config['SERVER_ADDR'], 'implementation_download/' + filename)
    print(implementation.as_dict())
    print(addr)
    print(filepath)
    try:
        with requests.get(addr, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except:
        print(sys.exc_info())
        experimentresult.RunStatus = 'Failed Implementation Download'
        this_client.Busy = False
        db.session.commit()
        return

    output_dir = os.path.join(app.config['OUTPUT_DIR'], str(id))

    os.makedirs(output_dir, exist_ok=True)

    inputformat = DataFormat.query.filter_by(Id=implementation.InputFormat).first()
    outputformat = DataFormat.query.filter_by(Id=implementation.OutputFormat).first()

    datasets = DataSetList.query.filter_by(ExperimentId=experiment.Id).all()
    idx = 0
    log = open(os.path.join(output_dir, 'log.txt'), 'wb')

    success = True
    for i in datasets:
        if inputformat.FormatType == 'File':
            # download file TODO

            print('File format not supported.')
            input_file = 'junk'
            # experimentresult.RunStatus = f'Failed DataSet {i.Id} Download'
            # this_client.Busy = False
            # db.session.commit()
            # return
        else:
            input_file = i.Content

        cur_output_dir = os.path.join(output_dir, str(idx))
        os.makedirs(cur_output_dir, exist_ok=True)

        args = [filepath, '--input', input_file, '--output', cur_output_dir]
        if implementation.CommandLineArgs is not None:
            args += shlex.split(implementation.CommandLineArgs)

        try:
            with subprocess.Popen(args, stdout=subprocess.PIPE) as proc:
                log.write(proc.stdout.read())
        except:
            log.write(str(sys.exc_info()))
            success = False
            break

        idx += 1
        
    log.close()
    if success:
        experimentresult.RunStatus = 'Success'
        this_client.Busy = False
        db.session.commit()
    else:
        experimentresult.RunStatus = 'Failed to run'
        this_client.Busy = False
        db.session.commit()
    
class run_experiment(Resource):
    def post(self, id):
        if not check_database(ExperimentResult, id):
            return f'ExperimentResult not found.', 404

        threading.Thread(group=None, target=run_impl, args=(id,)).start()

        return 200

