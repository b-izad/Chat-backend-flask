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
    return render_template('index.html')

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
    users = User.query.all()
    return render_template('chat.html', users=users)

@main.route('/send_message', methods=['POST'])
@login_required
def send_message():
    recipient_username = request.form['recipient']
    message_content = request.form['message']
    recipient = User.query.filter_by(username=recipient_username).first()
    
    if recipient:
        new_message = Message(content=message_content, sender=current_user, recipient=recipient)
        db.session.add(new_message)
        db.session.commit()
        message_data = {
            'sender': current_user.username,
            'recipient': recipient.username,
            'message': message_content
        }
        logging.debug(f"Message stored: {message_data}")
        socketio.emit('message', message_data, broadcast=True)
        logging.debug(f"Message emitted to clients: {message_data}")
        return redirect(url_for('main.chat'))
    else:
        flash('Recipient not found')
        return redirect(url_for('main.chat'))

@socketio.on('message')
def handle_message(data):
    logging.debug(f"Received message from client: {data}")
    socketio.send(data)

@main.route('/profile/<username>')
@login_required
def profile(username):
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
            # Implement the actual password reset logic here (e.g., sending a reset email)
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
