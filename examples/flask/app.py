from datetime import datetime
from flask import Flask, abort, jsonify, request
from flask.ext.babel import Babel, gettext
from bson import ObjectId
from pymongo import MongoClient

from umongo import Document, fields, ValidationError, set_gettext


app = Flask(__name__)
db = MongoClient().demo_umongo
babel = Babel(app)
set_gettext(gettext)


# available languages
LANGUAGES = {
    'en': 'English',
    'fr': 'Français'
}


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


class User(Document):
    nick = fields.StrField(required=True, unique=True)
    firstname = fields.StrField()
    lastname = fields.StrField()
    birthday = fields.DateTimeField()
    password = fields.StrField()  # Don't store it in clear in real life !

    class Meta:
        collection = db.user


def populate_db():
    User.collection.drop()
    User.ensure_indexes()
    for data in [
        {
            'nick': 'mze', 'lastname': 'Mao', 'firstname': 'Zedong',
            'birthday': datetime(1893, 12, 26), 'password': 'Serve the people'
        },
        {
            'nick': 'lsh', 'lastname': 'Liu', 'firstname': 'Shaoqi',
            'birthday': datetime(1898, 11, 24), 'password': 'Dare to think, dare to act'
        },
        {
            'nick': 'lxia', 'lastname': 'Li', 'firstname': 'Xiannian',
            'birthday': datetime(1909, 6, 23), 'password': 'To rebel is justified'
        },
        {
            'nick': 'ysh', 'lastname': 'Yang', 'firstname': 'Shangkun',
            'birthday': datetime(1907, 7, 5), 'password': 'Smash the gang of four'
        },
        {
            'nick': 'jze', 'lastname': 'Jiang', 'firstname': 'Zemin',
            'birthday': datetime(1926, 8, 17), 'password': 'Seek truth from facts'
        },
        {
            'nick': 'huji', 'lastname': 'Hu', 'firstname': 'Jintao',
            'birthday': datetime(1942, 12, 21), 'password': 'It is good to have just 1 child'
        },
        {
            'nick': 'xiji', 'lastname': 'Xi', 'firstname': 'Jinping',
            'birthday': datetime(1953, 6, 15), 'password': 'Achieve the 4 modernisations'
        }
    ]:
        User(**data).commit()


# dump/update can be passed a custom schema instance to avoid some fields
no_pass_schema = User.Schema(load_only=('password',), dump_only=('password',))


def dump_user_no_pass(u):
    return u.dump(schema=no_pass_schema)


@app.route('/', methods=['GET'])
def root():
    return """<h1>Umongo flask example</h1>
<br>
<h3>routes:</h3><br>
<ul>
  <li><a href="/users">GET /users</a></li>
  <li>POST /users</li>
  <li>GET /users/&lt;nick_or_id&gt;</li>
  <li>PATCH /users/&lt;nick_or_id&gt;</li>
  <li>PUT /users/&lt;nick_or_id&gt;/password</li>
</ul>
"""


def _to_objid(data):
    try:
        return ObjectId(data)
    except ValueError:
        return None


@app.route('/users/<nick_or_id>', methods=['GET'])
def get_user(nick_or_id):
    user = User.find_one({'$or': [{'nick': nick_or_id}, {'_id': _to_objid(nick_or_id)}]})
    if not user:
        abort(404)
    return jsonify(dump_user_no_pass(user))


@app.route('/users/<nick_or_id>', methods=['PATCH'])
def update_user(nick_or_id):
    payload = request.get_json()
    if payload is None:
        abort(400, 'Request body must be json with Content-type: application/json')
    user = User.find_one({'$or': [{'nick': nick_or_id}, {'_id': _to_objid(nick_or_id)}]})
    if not user:
        abort(404)
    # Define a custom schema from the default one to ignore read-only fields
    schema = User.Schema(dump_only=('password', 'nick'))
    try:
        user.update(payload, schema=schema)
        user.commit()
    except ValidationError as ve:
        resp = jsonify(message=ve.args[0])
        resp.status_code = 400
        return resp
    return jsonify(dump_user_no_pass(user))


@app.route('/users/<nick_or_id>/password', methods=['PUT'])
def change_password_user(nick_or_id):
    payload = request.get_json()
    if payload is None:
        abort(400, 'Request body must be json with Content-type: application/json')
    user = User.find_one({'$or': [{'nick': nick_or_id}, {'_id': _to_objid(nick_or_id)}]})
    if not user:
        abort(404)

    # Custom schema with only a required password field
    class PasswordSchema(User.Schema):
        class Meta:
            fields = ('password',)

    schema = PasswordSchema(strict=True)
    schema.fields['password'].required = True
    try:
        # Validate the incoming payload outside of the document to process
        # the `required` options
        data, _ = schema.load(payload)
        user.password = data['password']
        user.commit()
    except ValidationError as ve:
        resp = jsonify(message=ve.args[0])
        resp.status_code = 400
        return resp
    return jsonify(dump_user_no_pass(user))


@app.route('/users', methods=['GET'])
def list_users():
    page = int(request.args.get('page', 1))
    users = User.find().limit(10).skip((page - 1) * 10)
    return jsonify({
        '_total': users.count(),
        '_page': page,
        '_per_page': 10,
        '_items': [dump_user_no_pass(u) for u in users]
    })


@app.route('/users', methods=['POST'])
def create_user():
    payload = request.get_json()
    if payload is None:
        abort(400, 'Request body must be json with Content-type: application/json')
    try:
        user = User(**payload)
        user.commit()
    except ValidationError as ve:
        resp = jsonify(message=ve.args[0])
        resp.status_code = 400
        return resp
    return jsonify(dump_user_no_pass(user))


if __name__ == '__main__':
    populate_db()
    app.run(debug=True)
