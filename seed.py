# scripts/seed.py
from app import create_app
from app.extensions import db
from app.models import SundayClass, User

app = create_app()
app.app_context().push()

# create classes if missing
classes = [
    ("Gifted Brains", 0, 3),
    ("Beginners", 3, 6),
    ("Shinners", 6, 9),
    ("Conquerors", 9, 13),
    ("Teens", 13, 99),
]
for name, min_age, max_age in classes:
    if not SundayClass.query.filter_by(name=name).first():
        c = SundayClass(name=name, min_age=min_age, max_age=max_age)
        db.session.add(c)

# create admin user if missing
if not User.query.filter_by(username="admin").first():
    user = User(username="admin", name="Administrator", role="admin", email=None)
    user.set_password("change-me-please")
    user.must_change_password = True
    db.session.add(user)

db.session.commit()
print("Seeded classes and admin.")