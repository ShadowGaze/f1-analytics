from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)

    from app.controllers.main import main_bp
    from app.controllers.drivers import drivers_bp
    from app.controllers.circuits import circuits_bp
    from app.controllers.constructors import constructors_bp
    from app.controllers.races import races_bp
    from app.controllers.analysis import analysis_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(drivers_bp,      url_prefix="/drivers")
    app.register_blueprint(circuits_bp,     url_prefix="/circuits")
    app.register_blueprint(constructors_bp, url_prefix="/constructors")
    app.register_blueprint(races_bp,        url_prefix="/races")
    app.register_blueprint(analysis_bp,     url_prefix="/analysis")

    from app.controllers.errors import register_error_handlers
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app
