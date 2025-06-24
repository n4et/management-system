from app import db, User, app

with app.app_context():
    db.create_all()
    admin = User(name='Admin', email='admin_email@gmail.com', role='admin', password='admin123')
    staff = User(name='Ali', email='ali@gmail.com', role='staff', password='ali123')
    db.session.add_all([admin, staff])
    db.session.commit()
    print("✅ Sample admin and staff added.")
