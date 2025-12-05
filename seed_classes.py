from app import create_app
from app.extensions import db
from app.models import Child, SundayClass

app = create_app()

AGE_RANGES = {
    "Gifted Brains": (0, 3),
    "Beginners": (3, 6),
    "Shinners": (6, 9),
    "Conquerors": (9, 13),
    "Teens": (13, 18),
}

with app.app_context():
    # Map SundayClass names to their IDs
    classes = {c.name: c.id for c in SundayClass.query.all()}

    children = Child.query.all()
    for ch in children:
        if ch.age is None:
            continue
        for cname, (min_age, max_age) in AGE_RANGES.items():
            if min_age <= ch.age < max_age:
                ch.class_id = classes[cname]
                break

    db.session.commit()
    print("All children reassigned to correct classes ✔️")