from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user_model import User
from .message_model import Message
from .contact_model import Contact
