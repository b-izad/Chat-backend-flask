import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://bahareh:Barf%407811204@localhost:5432/chat_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = '6b95a292bba641298e75b3f31dc5276d4c788d3d2d52972e5c9e0b9e12f2c6a9'  # Randomly generated secret key
    WTF_CSRF_ENABLED = True
