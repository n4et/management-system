from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'ssupdope88@gmail.com'  # update
app.config['MAIL_PASSWORD'] = 'xcfcgfqjysnwymue'     # update
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)

# === MODELS ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    role = db.Column(db.String(10))  # 'admin' or 'staff'
    password = db.Column(db.String(100))

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')

class ShiftSwap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer)
    target_id = db.Column(db.Integer)
    date = db.Column(db.String(20))
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pending')

# Run once
with app.app_context():
    db.create_all()
    if not User.query.first():
        admin = User(name='Admin', email='ssupdope88@gmail.com', role='admin', password='admin123')
        staff1 = User(name='Ali', email='ali@gmail.com', role='staff', password='ali123')
        staff2 = User(name='Sara', email='sara@gmail.com', role='staff', password='sara123')
        db.session.add_all([admin, staff1, staff2])
        db.session.commit()

# === ROUTES ===

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    user = User.query.get(session['user_id'])
    if session['role'] == 'staff':
        leaves = LeaveRequest.query.filter_by(staff_id=user.id).all()
        shifts = ShiftSwap.query.filter_by(requester_id=user.id).all()
        staff_names = {u.id: u.name for u in User.query.filter_by(role='staff')}
        return render_template('dashboard.html', user=user, leaves=leaves, shifts=shifts, staff_names=staff_names)
    else:
        requests = LeaveRequest.query.all()
        users = {u.id: u.name for u in User.query.all()}
        return render_template('admin_view.html', requests=requests, users=users)


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

        # Notify admin
        admin = User.query.filter_by(role='admin').first()
        staff = User.query.get(session['user_id'])
        msg = Message("New Leave Request", sender=app.config['MAIL_USERNAME'], recipients=[admin.email])
        msg.body = f"""
        Staff: {staff.name}
        Email: {staff.email}
        From: {leave.start_date}
        To: {leave.end_date}
        Reason: {leave.reason}
        """
        mail.send(msg)
        return redirect('/dashboard')
    return render_template('leave_form.html')

@app.route('/request-shift', methods=['GET', 'POST'])
def request_shift():
    if request.method == 'POST':
        swap = ShiftSwap(
            requester_id=session['user_id'],
            target_id=request.form['target_id'],
            date=request.form['date'],
            reason=request.form['reason']
        )
        db.session.add(swap)
        db.session.commit()
        return redirect('/dashboard')
    staff_list = User.query.filter_by(role='staff').filter(User.id != session['user_id']).all()
    return render_template('shift_form.html', staff_list=staff_list)

@app.route('/cancel-leave/<int:id>')
def cancel_leave(id):
    leave = LeaveRequest.query.get_or_404(id)
    if leave.status == 'Pending':
        db.session.delete(leave)
        db.session.commit()
    return redirect('/dashboard')

@app.route('/cancel-shift/<int:id>')
def cancel_shift(id):
    shift = ShiftSwap.query.get_or_404(id)
    if shift.status == 'Pending':
        db.session.delete(shift)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/update-status/<int:id>/<action>')
def update_status(id, action):
    leave = LeaveRequest.query.get(id)
    leave.status = 'Approved' if action == 'approve' else 'Declined'
    db.session.commit()
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(debug=True)
