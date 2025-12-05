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
    classes = {c.name: c for c in SundayClass.query.all()}
    children = Child.query.all()

    for child in children:
        age = child.age
        assigned = False
        for class_name, (min_age, max_age) in AGE_RANGES.items():
            if min_age <= age < max_age:
                child.class_id = classes[class_name].id
                assigned = True
                break
        if not assigned:
            child.class_id = None  # optional: unassigned
    db.session.commit()
    print("✅ Children assigned to classes based on age ranges.")