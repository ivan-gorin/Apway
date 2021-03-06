from flask_restful import Resource, reqparse
from app.common.models import DataFormat, BaseEntity, DataSet, Task,\
 ExperimentEnvironment, ProgramImplementation, Experiment, DataSetList, ExperimentResult, Client
from datetime import datetime
from app import db
from sqlalchemy.exc import IntegrityError
from app import app
from urllib import parse
import os, sys, threading, requests, subprocess, shlex, re, zipfile

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

    impl_dir = os.path.join(app.config['IMPLEMENTATION_DIR'], str(implementation.Id))
    os.makedirs(impl_dir, exist_ok=True)
    filepath = os.path.join(impl_dir, filename)

    impl_addr = parse.urljoin(app.config['SERVER_ADDR'], 'implementation_download/' + filename)

    try:
        with requests.get(impl_addr, stream=True) as r:
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
    
    if implementation.ProgramType == 'PythonZip':
        try:
            with zipfile.ZipFile(filepath, 'r') as zipf:
                zipf.extractall(impl_dir)
        except:
            print(sys.exc_info())
            experimentresult.RunStatus = 'Failed Implementation Unzip'
            this_client.Busy = False
            db.session.commit()
            return

        filepath = os.path.join(app.config['IMPLEMENTATION_DIR'], str(implementation.Id), 'main.py')


    output_dir = os.path.join(app.config['OUTPUT_DIR'], str(id))

    os.makedirs(output_dir, exist_ok=True)

    inputformat = DataFormat.query.filter_by(Id=implementation.InputFormat).first()
    outputformat = DataFormat.query.filter_by(Id=implementation.OutputFormat).first()

    datasets = DataSetList.query.filter_by(ExperimentId=experiment.Id).all()
    log = open(os.path.join(output_dir, 'log.txt'), 'wb')

    idx = 0
    success = True
    for i in datasets:
        log.write((f'Running on DataSet number {idx}\n').encode('utf-8'))

        dataset = DataSet.query.filter_by(Id=i.DataSetId).first()

        if inputformat.FormatType == 'File':
            try:
                with requests.get(dataset.Content, stream=True) as r:
                    r.raise_for_status()
                    cd = r.headers.get('content-disposition')
                    dataset_name = re.findall('filename="(.+)"', cd)[0]
                    dataset_path = os.path.join(args.config['IMPLEMENTATION_DIR'], dataset_name)
                    with open(dataset_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            except:
                print(sys.exc_info())
                experimentresult.RunStatus = f'Failed DataSet Id={i.DataSetId} Download'
                this_client.Busy = False
                db.session.commit()
                log.close()
                return
            input_file = dataset_path
        else:
            input_file = dataset.Content

        if outputformat.FormatType == 'File':
            output = os.path.join(output_dir, str(idx))
            os.makedirs(output, exist_ok=True)
        else:
            output = experimentresult.OutputString

        if implementation.ProgramType == 'Exec':
            args = [filepath, '--input', input_file, '--output', output]
        else:
            args = ['python', filepath, '--input', input_file, '--output', output]

        if implementation.CommandLineArgs is not None:
            args += shlex.split(implementation.CommandLineArgs)

        try:
            with subprocess.Popen(args, stdout=subprocess.PIPE, cwd=impl_dir) as proc:
                log.write(proc.stdout.read())
        except:
            log.write(str(sys.exc_info()))
            success = False
            break

        idx += 1
        
    log.close()
    stop_time = datetime.now()
    if success:
        experimentresult.RunStatus = 'Success'
    else:
        experimentresult.RunStatus = 'Failed to run'

    this_client.Busy = False
    experimentresult.StartTime = start_time
    experimentresult.StopTime = stop_time
    db.session.commit()
    
class run_experiment(Resource):
    def post(self, id):
        if not check_database(ExperimentResult, id):
            return f'ExperimentResult not found.', 404

        threading.Thread(group=None, target=run_impl, args=(id,)).start()

        return 200

