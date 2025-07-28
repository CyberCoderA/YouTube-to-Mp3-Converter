class Config:
    DEBUG = False
    TESTING = False
    SECRET_KEY = 'default_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site_database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True