from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import functools
import jwt
import datetime


app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = "mongodb+srv://bhung7001:Hung28072002@cluster0.s0le1.mongodb.net/greentech?retryWrites=true&w=majority&appName=Cluster0"
app.config["SECRET_KEY"] = 'your_secret_key'

socketio = SocketIO(app, cors_allowed_origins="*")

mongo = PyMongo(app)
bcrypt = Bcrypt(app)

users_collection = mongo.db.users
devices_collection = mongo.db.devices
sensor_data_collection = mongo.db.sensor_data


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'Email already exists!'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_id = users_collection.insert_one({'email': email, 'password': hashed_password}).inserted_id
    return jsonify({'message': 'User registered!', 'user_id': str(user_id)}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = users_collection.find_one({'email': email})

    if user and bcrypt.check_password_hash(user['password'], password):
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid credentials!'}), 401


def token_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token is missing!'}), 403
        if token.startswith('Bearer'):
            token = token[7:]
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = users_collection.find_one({'_id': ObjectId(data['user_id'])})
        except:
            return jsonify({'error': 'Token is invalid!'}), 403

        return f(current_user, *args, **kwargs)
    return wrapper

@app.route('/devices', methods=['POST'])
@token_required
def add_device(current_user):
    data = request.json
    device_name = data.get('name')
    device_mac_address = data.get('mac_address')
    device_type = data.get('type')

    if not device_mac_address:
        return jsonify({'error': 'Device MAC address are required!'}), 400
    if not device_type:
        return jsonify({'error': 'Device type are required!'}), 400

    new_device = {
        'name': device_name,
        'mac_address': device_mac_address,
        'type': device_type,
        'status': 'off',
        'user_id': current_user['_id']
    }
    device_id = devices_collection.insert_one(new_device).inserted_id

    return jsonify({'message': 'Device added!', 'device_id': str(device_id)}), 201


@app.route('/devices', methods=['GET'])
@token_required
def get_devices(current_user):
    devices = devices_collection.find({'user_id': current_user['_id']})
    result = []
    for device in devices:
        result.append({
            'id': str(device['_id']),
            'name': device.get('name', 'unknowm'),
            'mac_address': device.get('mac_address', 'unknowm'),
            'type': device.get('type', 'unknowm'),
            'status': device.get('status', 'unknown')
        })
    return jsonify(result), 200


@app.route('/devices/<device_id>', methods=['PUT'])
@token_required
def update_device(current_user, device_id):
    data = request.json
    new_status = data.get('status')

    if not new_status:
        return jsonify({'error': 'Status is required!'}), 400

    result = devices_collection.update_one(
        {'_id': ObjectId(device_id), 'user_id': current_user['_id']},
        {'$set': {'status': new_status}}
    )

    if result.matched_count == 0:
        return jsonify({'error': 'Device not found or not authorized!'}), 404

    socketio.emit('device_status_updated', {'device_id': device_id, 'status': new_status})
    
    return jsonify({'message': 'Device updated!'}), 200


@app.route('/sensor-data', methods=['GET'])
def get_sensor_data():
    sensor_data_cursor = sensor_data_collection.find()
    
    result = []
    for data in sensor_data_cursor:
        data['_id'] = str(data['_id'])
        result.append(data)
    
    return jsonify(result), 200


@socketio.on('sensor_data')
def handle_sensor_data(data):
    try:
        if 'name' not in data or 'status' not in data or 'temp' not in data or 'humi' not in data:
            emit('error', {'message': 'Missing required fields.'})
            return
        
        sensor_data = {
            'name': data['name'],
            'status': data['status'],
            'temp': data['temp'],
            'humi': data['humi'],
            'soil': data.get('soil', None),
            'lux': data.get('lux', None),
            'timestamp': datetime.datetime.utcnow()
        }

        sensor_data_id = sensor_data_collection.insert_one(sensor_data).inserted_id

        emit('sensor_data_received', {'message': 'Sensor data added', 'id': str(sensor_data_id)})

    except Exception as e:
        emit('error', {'message': str(e)})


if __name__ == '__main__':
    socketio.run(app, debug=True)
