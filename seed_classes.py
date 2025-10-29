from app import create_app
app = create_app()
with app.app_context():
    from app.models import SundayClass
    from app.extensions import db
    classes = ["Gifted Brains", "Beginners", "Shinners", "Conquerors", "Teens"]
    for name in classes:
        if not SundayClass.query.filter_by(name=name).first():
            db.session.add(SundayClass(name=name))
    db.session.commit()
    print("Seed complete")