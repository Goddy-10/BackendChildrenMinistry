from app import create_app
from app.extensions import db
from app.models import SundayClass

app = create_app()

AGE_RANGES = {
    "Gifted Brains": (0, 3),
    "Beginners": (3, 6),
    "Shinners": (6, 9),
    "Conquerors": (9, 13),
    "Teens": (13, 18),
}

with app.app_context():
    classes = SundayClass.query.all()

    for c in classes:
        if c.name in AGE_RANGES:
            c.min_age, c.max_age = AGE_RANGES[c.name]
            print(f"Updated {c.name} → {c.min_age}-{c.max_age}")

    db.session.commit()
    print("DONE.")