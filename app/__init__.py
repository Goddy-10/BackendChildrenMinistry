# # app/__init__.py
# from flask import Flask
# from .extensions import db, migrate, jwt, cors
# from config import Config
# from app.routes.upload import gallery_bp

# def create_app(config_class=Config):
#     app = Flask(__name__, static_folder=None)
#     app.config.from_object(config_class)

#     # initialize extensions
#     db.init_app(app)
#     migrate.init_app(app, db)
#     jwt.init_app(app)
#     cors.init_app(app, resources={r"/*": {"origins": ["http://localhost:5173"]}},supports_credentials=True)

#     # import models so they are registered with SQLAlchemy
#     from . import models  # noqa: F401
#     from .routes.auth import auth_bp
#     app.register_blueprint(auth_bp,url_prefix="/api/auth")
#     from.routes.teacher import teachers_bp
#     app.register_blueprint(teachers_bp,url_prefix="/teachers")
#     app.register_blueprint(gallery_bp,url_prefix="/api")
    

    
    
  

#     @app.route("/health")
#     def health():
#         return {"status": "ok"}

#     return app










# app/__init__.py
from flask import Flask
from .extensions import db, migrate, jwt, cors
from config import Config
from app.routes.upload import gallery_bp

from app.routes.hbc import homechurch_bp

from . import models

def create_app(config_class=Config):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)


    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)



    # <-- Updated CORS setup -->
    cors.init_app(
        app,
        resources={r"/*": {"origins": ["http://localhost:5173"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],  # allow Authorization header
        methods=["GET", "POST", "PUT","PATCH", "DELETE", "OPTIONS"]  # allow common methods
    )

    # import models so they are registered with SQLAlchemy
    from app.routes.adults_rest import adults_bp
    app.register_blueprint(adults_bp,url_prefix="/api")
      # noqa: F401
    from app.routes.classes import classes_bp  
    from app.routes.timetable import timetable_bp  
    from app.routes.homepage import media_bp 
    from app.routes.visitors import visitors_bp  
    from app.routes.members import members_bp 
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp,url_prefix="/api/auth")
    from .routes.teacher import teachers_bp
    app.register_blueprint(teachers_bp, url_prefix="/api/teachers")
    app.register_blueprint(gallery_bp, url_prefix="/api")
    app.register_blueprint(members_bp,url_prefix="/api/members")
    app.register_blueprint(homechurch_bp,url_prefix="/api/homechurches")
    app.register_blueprint(visitors_bp,url_prefix="/api/visitors")
    app.register_blueprint(media_bp,url_prefix="/api/media") 
    app.register_blueprint(timetable_bp,url_prefix="/api/timetable")
    app.register_blueprint(classes_bp,url_prefix="/api/classes")
    print("✅ Registered Blueprints:", app.blueprints.keys())
    

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app