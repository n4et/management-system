from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Gmail SMTP settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ssupdope88@gmail.com'
app.config['MAIL_PASSWORD'] = 'ioqmgpzgogfewiwa'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    role = db.Column(db.String(10))
    password = db.Column(db.String(100))

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email'], password=request.form['password']).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect('/dashboard')
        return "Login Failed"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if session['role'] == 'staff':
        leaves = LeaveRequest.query.filter_by(staff_id=session['user_id']).all()
        return render_template('dashboard.html', leaves=leaves)
    else:
        requests = LeaveRequest.query.all()
        return render_template('admin_view.html', requests=requests)

@app.route('/request-leave', methods=['GET', 'POST'])
def request_leave():
    if request.method == 'POST':
        leave = LeaveRequest(
            staff_id=session['user_id'],
            start_date=request.form['start'],
            end_date=request.form['end'],
            reason=request.form['reason']
        )
        db.session.add(leave)
        db.session.commit()

        admin = User.query.filter_by(role='admin').first()
        staff = User.query.get(session['user_id'])

        msg = Message("New Leave Request", sender=app.config['MAIL_USERNAME'], recipients=[admin.email])
        msg.body = f"""A new leave request has been submitted:

Staff: {staff.name}
Email: {staff.email}
From: {leave.start_date}
To: {leave.end_date}
Reason: {leave.reason}

Please login to your dashboard to review it."""
        mail.send(msg)

        return redirect('/dashboard')
    return render_template('leave_form.html')

@app.route('/update-status/<int:id>/<action>')
def update_status(id, action):
    leave = LeaveRequest.query.get(id)
    leave.status = 'Approved' if action == 'approve' else 'Declined'
    db.session.commit()
    return redirect('/dashboard')

with app.app_context():
    if not User.query.first():  # only insert if table is empty
        admin = User(name='Admin', email='admin_email@gmail.com', role='admin', password='admin123')
        staff = User(name='Ali', email='ali@gmail.com', role='staff', password='ali123')
        db.session.add_all([admin, staff])
        db.session.commit()
        print("✅ Default users added.")


# 🔥 This is the important part!
if __name__ == '__main__':
    print("🔥 Flask app starting...")
    app.run(debug=True)
