import json
import datetime
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from klein import Klein
from bson import ObjectId
from txmongo import MongoConnection

from umongo import Instance, Document, fields, ValidationError


app = Klein()
db = MongoConnection().demo_umongo
instance = Instance(db)

# Babel is no supported for the moment...
# babel = Babel(app)
# set_gettext(gettext)


# available languages
LANGUAGES = {
    'en': 'English',
    'fr': 'Français'
}


# @babel.localeselector
# def get_locale():
#     return request.accept_languages.best_match(LANGUAGES.keys())


class MongoJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def jsonify(request, *args, **kwargs):
    """
    jsonify with support for MongoDB ObjectId
    """
    request.setHeader('Content-Type', 'application/json')
    return json.dumps(dict(*args, **kwargs), cls=MongoJsonEncoder, indent=True)


def get_json(request):
    return json.loads(request.content.read().decode())


@instance.register
class User(Document):
    nick = fields.StrField(required=True, unique=True)
    firstname = fields.StrField()
    lastname = fields.StrField()
    birthday = fields.DateTimeField()
    password = fields.StrField()  # Don't store it in clear in real life !


@inlineCallbacks
def populate_db():
    yield User.collection.drop()
    yield User.ensure_indexes()
    for data in [
        {
            'nick': 'mze', 'lastname': 'Mao', 'firstname': 'Zedong',
            'birthday': datetime.datetime(1893, 12, 26),
            'password': 'Serve the people'
        },
        {
            'nick': 'lsh', 'lastname': 'Liu', 'firstname': 'Shaoqi',
            'birthday': datetime.datetime(1898, 11, 24),
            'password': 'Dare to think, dare to act'
        },
        {
            'nick': 'lxia', 'lastname': 'Li', 'firstname': 'Xiannian',
            'birthday': datetime.datetime(1909, 6, 23),
            'password': 'To rebel is justified'
        },
        {
            'nick': 'ysh', 'lastname': 'Yang', 'firstname': 'Shangkun',
            'birthday': datetime.datetime(1907, 7, 5),
            'password': 'Smash the gang of four'
        },
        {
            'nick': 'jze', 'lastname': 'Jiang', 'firstname': 'Zemin',
            'birthday': datetime.datetime(1926, 8, 17),
            'password': 'Seek truth from facts'
        },
        {
            'nick': 'huji', 'lastname': 'Hu', 'firstname': 'Jintao',
            'birthday': datetime.datetime(1942, 12, 21),
            'password': 'It is good to have just 1 child'
        },
        {
            'nick': 'xiji', 'lastname': 'Xi', 'firstname': 'Jinping',
            'birthday': datetime.datetime(1953, 6, 15),
            'password': 'Achieve the 4 modernisations'
        }
    ]:
        yield User(**data).commit()


# dump/update can be passed a custom schema instance to avoid some fields
no_pass_schema = User.Schema(load_only=('password',), dump_only=('password',))


def dump_user_no_pass(u):
    return u.dump(schema=no_pass_schema)


@app.route('/', methods=['GET'])
def root(request):
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
    except Exception:
        return None


class Error(Exception):
    pass


@app.handle_errors(Error)
def error(self, request, failure):
    request.setResponseCode(failure.args[0])
    return failure.args[1]


@app.route('/users/<nick_or_id>', methods=['GET'])
@inlineCallbacks
def get_user(request, nick_or_id):
    user = yield User.find_one({'$or': [{'nick': nick_or_id}, {'_id': _to_objid(nick_or_id)}]})
    if not user:
        raise Error(404, 'Not found')
    returnValue(jsonify(request, dump_user_no_pass(user)))


@app.route('/users/<nick_or_id>', methods=['PATCH'])
@inlineCallbacks
def update_user(request, nick_or_id):
    payload = get_json(request)
    if payload is None:
        raise Error(400, 'Request body must be json with Content-type: application/json')
    user = yield User.find_one({'$or': [{'nick': nick_or_id}, {'_id': _to_objid(nick_or_id)}]})
    if not user:
        raise Error(404, 'Not found')
    # Define a custom schema from the default one to ignore read-only fields
    schema = User.Schema(dump_only=('password', 'nick'))
    try:
        user.update(payload, schema=schema)
        yield user.commit()
    except ValidationError as ve:
        resp = jsonify(request, message=ve.args[0])
        resp.status_code = 400
        returnValue(resp)
    returnValue(jsonify(request, dump_user_no_pass(user)))


@app.route('/users/<nick_or_id>', methods=['DELETE'])
@inlineCallbacks
def delete_user(request, nick_or_id):
    user = yield User.find_one({'$or': [{'nick': nick_or_id}, {'_id': _to_objid(nick_or_id)}]})
    if not user:
        Error(404)
    try:
        user.delete()
    except ValidationError as ve:
        resp = jsonify(message=ve.args[0])
        resp.status_code = 400
        returnValue(resp)
    returnValue('Ok')


@app.route('/users/<nick_or_id>/password', methods=['PUT'])
@inlineCallbacks
def change_password_user(request, nick_or_id):
    payload = get_json(request)
    if payload is None:
        raise Error(400, 'Request body must be json with Content-type: application/json')
    user = yield User.find_one({'$or': [{'nick': nick_or_id}, {'_id': _to_objid(nick_or_id)}]})
    if not user:
        raise Error(404, 'Not found')

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
        yield user.commit()
    except ValidationError as ve:
        resp = jsonify(request, message=ve.args[0])
        resp.status_code = 400
        returnValue(resp)
    returnValue(jsonify(request, dump_user_no_pass(user)))


@app.route('/users', methods=['GET'])
@inlineCallbacks
def list_users(request):
    page = int(request.args.get('page', 1))
    users = yield User.find(limit=10, skip=(page - 1) * 10)
    returnValue(jsonify(request, {
        '_total': (yield User.count()),
        '_page': page,
        '_per_page': 10,
        '_items': [dump_user_no_pass(u) for u in users]
    }))


@app.route('/users', methods=['POST'])
@inlineCallbacks
def create_user(request):
    payload = get_json(request)
    if payload is None:
        raise Error(400, 'Request body must be json with Content-type: application/json')
    try:
        user = User(**payload)
        yield user.commit()
    except ValidationError as ve:
        resp = jsonify(request, message=ve.args[0])
        resp.status_code = 400
        returnValue(resp)
    returnValue(jsonify(request, dump_user_no_pass(user)))


if __name__ == '__main__':
    reactor.callWhenRunning(populate_db)
    app.run('localhost', 5000)
