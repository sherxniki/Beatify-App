from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_principal import Principal
from flask_migrate import Migrate


login_manager=LoginManager()
login_manager.blueprint_login_views = {
    'admin': '/admin_login',
    'users': '/login', 
    'main' : '/login',
    'creators' : '/login'
}
login_manager.login_message_category='info'
db=SQLAlchemy()
migrate=Migrate()
principal = Principal()

def application():
    app=Flask(__name__)
    app.config['SECRET_KEY']='cceac037c0983bc4089a0e1d243efa39'
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///beatify.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
    app.config['ADMIN_USERNAME']='admin'
    app.config['ADMIN_PASS']='adminp@$$'

    login_manager.init_app(app)
    db.init_app(app)
    principal.init_app(app)
    migrate.init_app(app, db) 

    with app.app_context():
        from .routes.main import main
        from .routes.users import users
        from .routes.admin import admin
        from .routes.creators import creators
        
        app.register_blueprint(main)
        app.register_blueprint(users)
        app.register_blueprint(admin)
        app.register_blueprint(creators)

        db.create_all()
        return app
    
