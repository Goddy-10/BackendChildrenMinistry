# # app/seed_admin.py
# from app import create_app
# from app.extensions import db
# from app.models import User
# from werkzeug.security import generate_password_hash

# app = create_app()

# with app.app_context():
#     # Check if an admin already exists
#     existing_admin = User.query.filter_by(role="admin").first()
    
#     if existing_admin:
#         print(f"✅ Admin already exists: {existing_admin.username}")
#     else:
#         admin = User(
#             name="Administrator",
#             phone="0716454160",
#             email="gdthuranira@gmail.com"
#             password="admin123",
#             role="admin"
#         )
#         db.session.add(admin)
#         db.session.commit()
#         print("🎉 Admin account created successfully!")
#         print("📧 Phone: 0716454160")
#         print("🔑 Password: admin123")








from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    # Check if an admin already exists
    existing_admin = User.query.filter_by(role="admin").first()
    
    if existing_admin:
        print(f"✅ Admin already exists: {existing_admin.name}")
    else:
        admin = User(
            username="admin",
            name="Administrator",
            phone="0716454160",
            email="gdthuranira@gmail.com",
            password="admin123", # auto-hashed (see model below)
            role="admin",
            must_change_password=False
        )
        
        db.session.add(admin)
        db.session.commit()
        print("🎉 Admin account created successfully!")
        print("📧 Email: gdthuranira@gmail.com")
        print("📞 Phone: 0716454160")
        print("🔑 Password: admin123")