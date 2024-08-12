# app/__init__.py

from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS  


socketio = SocketIO()
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
  
    app = Flask(__name__)
    app.config.from_object('config.Config')  

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    login_manager.init_app(app)


    CORS(app, supports_credentials=True)

 
    login_manager.login_view = 'main.login'

  
    from app.routes.main_routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

@login_manager.user_loader
def load_user(user_id):
   
    from app.models.user_model import User
    return User.query.get(int(user_id))
