# models/user_model.py

from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Relationships
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy=True)
    contacts = db.relationship('Contact', foreign_keys='Contact.user_id', backref='user', lazy=True)
    contact_of = db.relationship('Contact', foreign_keys='Contact.contact_id', backref='contact', lazy=True)

    def set_password(self, password):
      
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
  
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
