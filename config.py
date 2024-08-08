class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://bahareh:Barf%407811204@localhost:5432/chat_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'super_secret_key_1234567890'  # Hardcoded secret key
    WTF_CSRF_ENABLED = False
    DEBUG = True
