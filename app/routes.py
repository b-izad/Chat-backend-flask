from flask import Blueprint, jsonify, request, redirect, url_for
from sqlalchemy.exc import IntegrityError
from . import socketio, db
from .models.user import User
from .models.message import Message
from flask_login import login_user, logout_user, login_required, current_user
from flask_cors import cross_origin
import logging

logging.basicConfig(level=logging.DEBUG)

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('main.chat'))

@main.route('/signup', methods=['POST'])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
def signup():
    data = request.get_json()
    logging.debug(f"Received signup data: {data}")
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    username = data.get('username')
    email = data.get('email')  # Remove this if email is not needed
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    # Email check if email is part of the user model
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    try:
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        logging.debug("User created successfully")
        return jsonify({"message": "User created successfully"}), 201
    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"IntegrityError: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500

@main.route('/login', methods=['POST'])
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
def login():
    data = request.get_json()
    logging.debug(f"Received login data: {data}")
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user is None:
        logging.error('User not found')
        return jsonify({"error": "Invalid username or password"}), 401
    if not user.check_password(password):
        logging.error('Incorrect password')
        return jsonify({"error": "Invalid username or password"}), 401
    login_user(user)
    logging.info('Login successful')
    return jsonify({"message": "Login successful"}), 200

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/api/contacts', methods=['GET'])
@login_required
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
def get_contacts():
    users = User.query.filter(User.id != current_user.id).all()
    contacts = [{'id': user.id, 'name': user.username, 'status': 'online'} for user in users]
    return jsonify({'contacts': contacts})

@main.route('/api/messages/<int:contact_id>', methods=['GET'])
@login_required
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
def get_messages(contact_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == contact_id)) |
        ((Message.sender_id == contact_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    return jsonify({'messages': [{'id': msg.id, 'content': msg.content, 'sender_id': msg.sender_id, 'timestamp': msg.timestamp} for msg in messages]})

@main.route('/api/messages', methods=['POST'])
@login_required
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
def send_message():
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    if recipient_id is None:
        return jsonify({'error': 'Recipient ID is required'}), 400
    message = Message(content=data['content'], sender_id=current_user.id, recipient_id=recipient_id)
    db.session.add(message)
    db.session.commit()
    socketio.emit('message', {'id': message.id, 'content': message.content, 'sender_id': message.sender_id, 'recipient_id': recipient_id, 'timestamp': message.timestamp}, broadcast=True)
    return jsonify({'id': message.id, 'content': message.content, 'sender_id': message.sender_id, 'recipient_id': recipient_id, 'timestamp': message.timestamp})

@main.route('/api/messages/<int:message_id>/like', methods=['POST'])
@login_required
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
def like_message(message_id):
    message = Message.query.get(message_id)
    if message:
        message.likes = message.likes + 1 if hasattr(message, 'likes') else 1
        db.session.commit()
        return jsonify({'id': message.id, 'content': message.content, 'sender_id': message.sender_id, 'likes': message.likes})
    return jsonify({'error': 'Message not found'}), 404

@main.route('/api/profile', methods=['GET', 'PUT'])
@login_required
@cross_origin(origins=["http://localhost:3000"], supports_credentials=True)
def profile():
    if request.method == 'GET':
        user = User.query.get(current_user.id)
        return jsonify({'profile': {'username': user.username, 'email': user.email}})
    if request.method == 'PUT':
        data = request.get_json()
        user = User.query.get(current_user.id)
        user.username = data['username']
        user.email = data['email']
        db.session.commit()
        return jsonify({'success': True})

@socketio.on('message')
def handle_message(data):
    logging.debug(f"Received message from client: {data}")
    socketio.send(data)
