


# app/__init__.py
from flask import Flask ,send_from_directory ,current_app
from .extensions import db, migrate, jwt, cors
from config import Config,BASE_UPLOAD_FOLDER
from app.routes.upload import gallery_bp

from app.routes.hbc import homechurch_bp

from . import models

def create_app(config_class=Config):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)
    

    @app.route("/uploads/<path:filename>")
    def serve_file(filename):
        return send_from_directory(current_app.config["BASE_UPLOAD_FOLDER"], filename)
    
    

   
    



    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)



    



    # <-- Updated CORS setup -->
    cors.init_app(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",              # dev
                "https://children-ministry.vercel.app/"    # production
            ]
        }
    },
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
)

    
    from flask_jwt_extended import JWTManager
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]           # only look in Authorization header
    # optional but recommended
    app.config["JWT_HEADER_NAME"] = "Authorization"
    app.config["JWT_HEADER_TYPE"] = "Bearer"


    # import models so they are registered with SQLAlchemy
    from app.routes.adults_rest import adults_bp
    app.register_blueprint(adults_bp,url_prefix="/api")
      # noqa: F401
    from app.routes.departments import department_members_bp
    from app.routes.classes import classes_bp  
    from app.routes.timetable import timetable_bp  
    from app.routes.reports import reports_bp
    from app.routes.homepage import media_bp 
    from app.routes.visitors import visitors_bp  
    from app.routes.members import members_bp 
    from app.routes.children import children_bp
    from app.routes.programs import programs_bp
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp,url_prefix="/api/auth")
    from .routes.teacher import teachers_bp
    app.register_blueprint(teachers_bp, url_prefix="/api/teachers")
    app.register_blueprint(gallery_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(homechurch_bp,url_prefix="/api/homechurches")
    app.register_blueprint(visitors_bp,url_prefix="/api/visitors")
    app.register_blueprint(media_bp) 
    app.register_blueprint(timetable_bp,url_prefix="/api/timetable")
    app.register_blueprint(classes_bp,url_prefix="/api/classes")
    app.register_blueprint(children_bp,url_prefix="/api/children")
    app.register_blueprint(reports_bp,url_prefix="/api/reports")
    app.register_blueprint(programs_bp,url_prefix="/api/programs")
    app.register_blueprint(department_members_bp)


    print("✅ Registered Blueprints:", app.blueprints.keys())
    

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app