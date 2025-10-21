# manage.py
from app import create_app
from app.extensions import db
from flask_migrate import Migrate
import os

app = create_app()

migrate=Migrate(app, db)

if __name__ == "__main__":
    # For simple dev run
    app.run(debug=True)