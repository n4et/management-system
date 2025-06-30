from app import db, User, app
from werkzeug.security import generate_password_hash

with app.app_context():
    db.drop_all()
    db.create_all()

    admin1 = User(name='Admin', email='admin1@gmail.com', role='admin', password=generate_password_hash('admin123'), approved=True)
    staff1 = User(name='Ali', email='ali@gmail.com', role='staff', password=generate_password_hash('ali123'), approved=True)

    db.session.add_all([admin1, staff1])
    db.session.commit()
    print("✅ Database initialized with sample users.")
