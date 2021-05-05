from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
api = Api(app)

from app.resources.data import dataformats, datasets, tasks, environments, implementations, experiments

api.add_resource(dataformats, '/data/formats', '/data/formats/<int:id>')
api.add_resource(datasets, '/data/sets', '/data/sets/<int:id>')
api.add_resource(tasks, '/tasks', '/tasks/<int:id>')
api.add_resource(environments, '/experiment/environments', '/experiment/environments/<int:id>')
api.add_resource(implementations, '/implementations', '/implementations/<int:id>')
api.add_resource(experiments, '/experiment/experiments', '/experiment/experiments/<int:id>')





# from app.common.models import BaseEntity

# @app.route('/delete_be', methods=['GET'])
# def delete_all_free_be():
#     c = 0
#     for i in range(100):
#         try:
#             to_delete = BaseEntity.query.filter_by(Id=i).first()
#             if to_delete is not None:
#                 db.session.delete(to_delete)
#                 db.session.commit()
#                 c += 1
#         except:
#             pass
#     print(c)
#     return 'test'