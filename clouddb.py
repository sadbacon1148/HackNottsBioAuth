# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


builtin_list = list


db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile(r'C:\Users\sadbacon\Desktop\getting-started-python\2-structured-data/config.py')
    init_app(app)
    return app

def init_app(app):
    # Disable track modifications, as it unnecessarily uses memory.
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    db.init_app(app)


def from_sql(row):
    """Translates a SQLAlchemy model instance into a dictionary"""
    data = row.__dict__.copy()
    data['accountNum'] = row.accountNum
    data.pop('_sa_instance_state')
    return data


# [START model]
class Biodata(db.Model):
    __tablename__ = 'Biodata'

    accountNum = db.Column(db.Integer, primary_key=True)
    fingerID = db.Column(db.Integer)
    phoneNum = db.Column(db.String(20))

    def __repr__(self):
        return "<Biodata>"
# [END model]

# [START list]
def list(limit=10, cursor=None):
    cursor = int(cursor) if cursor else 0
    query = (Biodata.query
             .order_by(Biodata.accountNum)
             .limit(limit)
             .offset(cursor))
    bdatas = builtin_list(map(from_sql, query.all()))
    next_page = cursor + limit if len(bdatas) == limit else None
    return (bdatas, next_page)
# [END list]


# [START read]
def read(id):
    result = Biodata.query.get(id)
    if not result:
        return None
    return from_sql(result)
# [END read]


# [START create]
def create(data):
    bdata = Biodata(**data)
    db.session.add(bdata)
    db.session.commit()
    return from_sql(bdata)
# [END create]


# [START update]
def update(data, id):
    bdata = Biodata.query.get(id)
    for k, v in data.items():
        setattr(bdata, k, v)
    db.session.commit()
    return from_sql(bdata)
# [END update]


def delete(id):
    Biodata.query.filter_by(accountNum=id).delete()
    db.session.commit()


def _create_database():
    """
    If this script is run directly, create all the tables necessary to run the
    application.
    """
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')
    init_app(app)
    with app.app_context():
        db.create_all()
    print("All tables created")


if __name__ == '__main__':
    _create_database()
