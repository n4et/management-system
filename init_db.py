from app import db, User, app
from werkzeug.security import generate_password_hash

with app.app_context():
    db.drop_all()   # 🔁 Ensure everything is dropped first
    db.create_all()  # ✅ Then recreate tables with updated schema

    admin = User(
        name='Admin',
        email='ssupdope88@gmail.com',
        role='admin',
        password=generate_password_hash('admin123'),
        approved=True
    )
    staff = User(
        name='Ali',
        email='ali@gmail.com',
        role='staff',
        password=generate_password_hash('ali123'),
        approved=True
    )

    db.session.add_all([admin, staff])
    db.session.commit()
    print("✅ Sample admin and staff added.")
