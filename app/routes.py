from flask import Blueprint, render_template, redirect, url_for, flash, request
from . import socketio, db
from .models import User, Message
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logging.basicConfig(level=logging.DEBUG)

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return "Hello, World!"

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('main.signup'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully')
        return redirect(url_for('main.login'))
    return render_template('signup.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))
        login_user(user)
        return redirect(url_for('main.chat'))
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    message = request.form['message']
    username = current_user.username
    new_message = Message(content=message, user=current_user)
    db.session.add(new_message)
    db.session.commit()
    message_data = {'username': username, 'message': message}
    logging.debug(f"Message stored: {message_data}")
    socketio.emit('message', message_data, broadcast=True)
    logging.debug(f"Message emitted to clients: {message_data}")
    return redirect(url_for('main.chat'))

@socketio.on('message')
def handle_message(data):
    logging.debug(f"Received message from client: {data}")
    socketio.send(data)
