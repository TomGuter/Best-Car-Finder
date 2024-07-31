from operator import length_hint
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate
from jinja2 import FileSystemLoader
import os
import secrets

db = SQLAlchemy()
migrate = Migrate()
DB_NAME = "database8.db"

def create_app():
    app = Flask(__name__)
    secret_key = secrets.token_hex(16)
    app.config['SECRET_KEY'] = 'dgtesdfgjhtyrert'
    # app.config['SECRET_KEY'] = secret_key # for now let it stay like this so the server will remember me as logged in
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    migrate.init_app(app, db)

    app.jinja_loader = FileSystemLoader([os.path.join(app.root_path, 'templates'),
                                         os.path.join(app.root_path, 'cars')])

    from .views import views
    from .auth import auth
    from .admin import admin
    from .car_pages import car_pages

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/')
    app.register_blueprint(car_pages, url_prefix='/')

    from .models import User

    if not path.exists('instance/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')
    else:
        print('Database exist!')    
    #create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))


    return app

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all()
        print('Created Database!')