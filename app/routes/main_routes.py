from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, socketio
from app.models.user_model import User
from app.models.message_model import Message
from app.models.contact_model import Contact
from flask_socketio import emit, join_room, leave_room
import logging

logging.basicConfig(level=logging.DEBUG)

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']  
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('main.signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('main.signup'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully')
        return redirect(url_for('main.login'))

    return render_template('signup.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return jsonify(message='Invalid username or password'), 401

        login_user(user)
        return jsonify(message='Login successful')
    return render_template('login.html')

@main.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify(message='Logout successful')

@main.route('/api/contacts', methods=['GET'])
@login_required
def get_contacts():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    contacts_list = [{"id": contact.contact_id, "username": contact.contact.username, "email": contact.contact.email} for contact in contacts]
    return jsonify(contacts=contacts_list)

@main.route('/api/contacts/add', methods=['POST'])
@login_required
def add_contact():
    data = request.json
    contact_id = data.get('contactId')

    if not contact_id:
        return jsonify(success=False, error='Contact ID is required'), 400

    if Contact.query.filter_by(user_id=current_user.id, contact_id=contact_id).first():
        return jsonify(success=False, error='Contact already exists'), 409

    new_contact = Contact(user_id=current_user.id, contact_id=contact_id)
    db.session.add(new_contact)
    db.session.commit()

    return jsonify(success=True, contact={"id": new_contact.contact_id, "username": new_contact.contact.username, "email": new_contact.contact.email})

@main.route('/api/messages/<int:contact_id>', methods=['GET'])
@login_required
def get_messages(contact_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == contact_id)) |
        ((Message.sender_id == contact_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    messages_list = [{"id": msg.id, "content": msg.content, "sender_id": msg.sender_id, "recipient_id": msg.recipient_id, "timestamp": msg.timestamp} for msg in messages]
    return jsonify(messages=messages_list)

# Updated send_message route using Socket.IO
@socketio.on('send_message')
@login_required
def handle_send_message(data):
    recipient_id = data.get('recipient_id')
    content = data.get('content')

    if not recipient_id or not content:
        emit('error', {'success': False, 'error': 'Recipient and content are required'})
        return

    new_message = Message(content=content, sender_id=current_user.id, recipient_id=recipient_id)
    db.session.add(new_message)
    db.session.commit()

    # Emit the message to the recipient's room
    recipient_room = f'user_{recipient_id}'
    emit('receive_message', {
        'id': new_message.id,
        'content': new_message.content,
        'sender_id': current_user.id,
        'recipient_id': recipient_id,
        'timestamp': new_message.timestamp.isoformat()
    }, room=recipient_room)

    # Emit the message to the sender's room as well
    sender_room = f'user_{current_user.id}'
    emit('receive_message', {
        'id': new_message.id,
        'content': new_message.content,
        'sender_id': current_user.id,
        'recipient_id': recipient_id,
        'timestamp': new_message.timestamp.isoformat()
    }, room=sender_room)

@socketio.on('join')
@login_required
def on_join(data):
    username = current_user.username
    room = f'user_{username}'
    join_room(room)
    emit('status', {'msg': f'{username} has entered the chat'}, room=room)

@socketio.on('leave')
@login_required
def on_leave(data):
    username = current_user.username
    room = f'user_{username}'
    leave_room(room)
    emit('status', {'msg': f'{username} has left the chat'}, room=room)

@main.route('/profile/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)

@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        db.session.commit()
        flash('Profile updated successfully')
        return redirect(url_for('main.profile', username=current_user.username))
    return render_template('edit_profile.html')

@main.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Password reset link sent to your email')
            return redirect(url_for('main.login'))
        else:
            flash('Username not found')
            return redirect(url_for('main.reset_password'))
    return render_template('reset_password.html')

@main.route('/message_history/<recipient_username>')
@login_required
def message_history(recipient_username):
    recipient = User.query.filter_by(username=recipient_username).first_or_404()
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) & (Message.recipient_id == recipient.id) |
        (Message.sender_id == recipient.id) & (Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all()
    return render_template('message_history.html', messages=messages, recipient=recipient)

@main.route('/search_users', methods=['GET', 'POST'])
@login_required
def search_users():
    if request.method == 'POST':
        search_term = request.form['search_term']
        users = User.query.filter(User.username.contains(search_term)).all()
        return render_template('search_results.html', users=users, search_term=search_term)
    return render_template('search_users.html')

