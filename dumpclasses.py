# dump_classes.py
from app import create_app
from app.extensions import db
from app.models import SundayClass

app = create_app()
with app.app_context():
    for c in SundayClass.query.all():
        print(c.id, c.name, c.min_age, c.max_age)