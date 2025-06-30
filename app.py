import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

# Email config from environment
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# === MODELS ===
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    role = db.Column(db.String(10))  # 'admin', 'staff', 'felo'
    password = db.Column(db.String(200))  # Hashed
    approved = db.Column(db.Boolean, default=False)

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

# Initial DB setup
with app.app_context():
    db.create_all()
    if not User.query.first():
        admin1 = User(name='Admin', email='ssupdope88@gmail.com', role='admin', password=generate_password_hash('admin123'), approved=True)
        admin2 = User(name='Admin Two', email='norazhar@ums.edu.my', role='admin', password=generate_password_hash('adminpass2'), approved=True)
        staff1 = User(name='Ali', email='ali@gmail.com', role='staff', password=generate_password_hash('ali123'), approved=True)
        staff2 = User(name='Sara', email='sara@gmail.com', role='staff', password=generate_password_hash('sara123'), approved=True)
        db.session.add_all([admin1, admin2, staff1, staff2])
        db.session.commit()

# === ROUTES ===
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Email not found.")
        elif not user.approved:
            flash("Your account is not approved yet. Please wait for admin approval.")
        elif user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect('/dashboard')
        else:
            flash("Incorrect password.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    user = User.query.get(session['user_id'])
    if user.role in ['staff', 'felo']:
        leaves = LeaveRequest.query.filter_by(staff_id=user.id).all()
        shifts = ShiftSwap.query.filter_by(requester_id=user.id).all()
        staff_names = {u.id: u.name for u in User.query.filter(User.role.in_(['staff', 'felo']))}
        return render_template('dashboard.html', user=user, leaves=leaves, shifts=shifts, staff_names=staff_names)
    else:
        requests = LeaveRequest.query.all()
        users = {u.id: u.name for u in User.query.all()}
        pending_users = User.query.filter_by(approved=False).all()
        return render_template('admin_view.html', requests=requests, users=users, pending_users=pending_users)

@app.route('/approve-user/<int:user_id>')
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.approved = True
    db.session.commit()
    flash(f"Approved {user.name} successfully.")
    return redirect('/dashboard')

@app.route('/users')
def user_list():
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')
    admins = User.query.filter_by(role='admin').all()
    staff = User.query.filter_by(role='staff').all()
    felos = User.query.filter_by(role='felo').all()
    return render_template('user_list.html', admins=admins, staff=staff, felos=felos)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_profile.html', user=user)

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
        msg.body = f"""
        Staff: {staff.name}
        Email: {staff.email}
        From: {leave.start_date}
        To: {leave.end_date}
        Reason: {leave.reason}
        """
        try:
            mail.send(msg)
        except Exception as e:
            print("Failed to send email:", e)

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
    staff_list = User.query.filter_by(role='felo').filter(User.id != session['user_id']).all()
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect('/register')

        new_user = User(
            name=name,
            email=email,
            role=role,
            password=generate_password_hash(password),
            approved=False
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration submitted! Please wait for admin approval.')
        return redirect('/')
    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        print("USER:", user)
        if user:
            print("Approved:", user.approved)
            print("Password Correct:", check_password_hash(user.password, password))

        if not user:
            flash("Email not found.")
        elif not user.approved:
            flash("Your account is not approved yet. Please wait for admin approval.")
        elif check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect('/dashboard')
        else:
            flash("Incorrect password.")
    return render_template('login.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
