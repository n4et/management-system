from app import db, User, app
from werkzeug.security import generate_password_hash

with app.app_context():
    admin1 = User(name='Admin', email='ssupdope88@gmail.com', role='admin', password=generate_password_hash('admin123'), approved=True)
    admin2 = User(name='Admin Two', email='norazhar@ums.edu.my', role='admin', password=generate_password_hash('adminpass2'), approved=True)
    staff1 = User(name='Ali', email='ali@gmail.com', role='staff', password=generate_password_hash('ali123'), approved=True)
    staff2 = User(name='Sara', email='sara@gmail.com', role='staff', password=generate_password_hash('sara123'), approved=True)

    db.session.add_all([admin1, admin2, staff1, staff2])
    db.session.commit()
    print("✅ Sample users inserted.")
