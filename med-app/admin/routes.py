import os

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, logout_user
from flask_security import roles_accepted, SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from werkzeug.utils import secure_filename

import config
from extensions import db, SQLAlchemyError, OperationalError, bcrypt
from models.appointments import Appointment
from models.doctor import Doctor
from models.location import Location
from models.patient import Patient
from models.role import Role
from models.specialisation import Specialisation
from models.user import User

admin = Blueprint('admin', __name__, static_folder='../static', template_folder='../templates')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


@admin.route('/')
@roles_accepted('admin')
def admin_dash():
    user = current_user.username
    return render_template('admin/admin_home.html', username=user)


@admin.route('/add-specialisation')
@roles_accepted('admin')
def add_specialisation():
    return render_template('admin/add_specialisation.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin.route('/save-specialisation', methods=['GET', 'POST'])
@roles_accepted('admin')
def save_specialisation():
    if request.method == "POST":
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            name = request.form.get('name')
            spec = Specialisation(name=name, img=filename)
            db.session.add(spec)
            file.save(os.path.join('static/uploads', filename))
            db.session.commit()
            return redirect(url_for("admin.get_spec"))

@admin.route('/appointments/<id>', methods=['GET', 'POST'])
@roles_accepted('admin')
def delete_appointment(id):
    app = Appointment.query.filter_by(id=id).update({"active":0})
    db.session.commit()
    flash("Appointment successfully deleted", "success text-center")
    return redirect(url_for("admin.get_appointments"))

@admin.route('/patient/<id>', methods=['GET', 'POST'])
@roles_accepted('admin')
def del_patient(id):
    usr = User.query.get(id)
    user = User.query.filter_by(id=id).update({"active":0})
    db.session.commit()
    flash(f"{usr} successfully deleted", "success text-center")
    return redirect(url_for("admin.get_patients"))

@admin.route('/doctor/<id>', methods=['GET', 'POST'])
@roles_accepted('admin')
def del_doctor(id):
    usr = User.query.get(id)
    user = User.query.filter_by(id=id).update({"active":0})
    db.session.commit()
    flash(f"{usr} successfully deleted", "success text-center")
    return redirect(url_for("admin.get_doctors"))


@admin.route('/add-doctor')
@roles_accepted('admin')
def add_doctor():
    specs = Specialisation.query.all()
    return render_template("admin/add_doctors.html", specs=specs)


@admin.route('/specialisations')
@roles_accepted('admin')
def get_spec():
    specs = Specialisation.query.all()
    return render_template("admin/specialisation.html", specs=specs)


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


@admin.route('/save-doctor', methods=['GET', 'POST'])
@roles_accepted('admin')
def save_doctor():
    message = ""
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        if password.__ne__(password_confirm):
            flash("Password does not match Password confirmation. Please match the passwords.", "alert")
            return render_template("admin/add_doctors.html")
        phone = consultation_fee = request.form.get('phone')
        # DOCTOR
        spec = request.form.get('spec_id')
        consultation_fee = request.form.get('fee')

        # LOCATION
        street = request.form.get('street')
        city = request.form.get('city')
        country = request.form.get('country')

        doctor_role = Role(name='doctor')

        try:
            user = user_datastore.create_user(username=username, email=email, password=bcrypt.generate_password_hash(password)
                                              , phone=phone, roles=[doctor_role])
            db.session.add(user)
            db.session.commit()
            location = Location(street=street, city=city, country=country, user_id=user.id)
            doctor = Doctor(user_id=user.id, spec_id=spec, fee=consultation_fee)
            db.session.add(location)
            db.session.add(doctor)
        except SQLAlchemyError as e:
            flash(f"{str(e.__dict__['orig'])}", "danger text-center")
            db.session.rollback()
            return render_template("admin/add_doctors.html")
        except OperationalError as o:
            flash(f"{str(o.__dict__['orig'])}", "danger text-center")
            db.session.rollback()
            return render_template("admin/add_doctors.html")
        else:
            db.session.commit()

        flash("Successfully added new doctor", "success text-center m-2")
        return render_template('admin/manage_doctors.html')
    flash("Error encountered while adding new doctor! Please try again with valid information", "alert")
    return redirect("admin/manage_doctors.html")


@admin.route('/get-doctors', methods=['GET'])
@roles_accepted('admin')
def get_doctors():
    docs = Doctor.query.all()
    docs2 = []
    for doc in docs:
        user = User.query.get(doc.user_id)
        spec = Specialisation.query.get(doc.specialisation_id)
        doc = {"user": user, "spec": spec, "doc": doc}
        docs2.append(doc)
    return render_template("admin/manage_doctors.html", doctors=docs2)


@admin.route('/appointments', methods=['GET'])
@roles_accepted('admin')
def get_appointments():
    appointments = Appointment.query.all()
    appoints = []
    for app in appointments:
        pat = User.query.get(Patient.query.get(app.patient_id).user_id)
        doc = User.query.get(Doctor.query.get(app.doctor_id).user_id)
        spec = Specialisation.query.get(Doctor.query.get(app.doctor_id).specialisation_id)
        appointment = {"pat": pat, "spec": spec, "doc": doc, "status": app.status,
                       "date": app.date, "time": app.time, "id":app.id, "active":app.active}
        appoints.append(appointment)
    return render_template("admin/appointments.html", appointments=appoints)


@admin.route('/manage-patients', methods=['GET'])
@roles_accepted('admin')
def get_patients():
    patients = Patient.query.all()
    pats = []
    for pat in patients:
        user = User.query.get(pat.user_id)
        pat2 = {"user": user, "pat": pat}
        pats.append(pat2)
    return render_template("admin/manage_patients.html", patients=pats)


@admin.route('/logout', methods=['GET', 'POST'])
@login_required
def logout_():
    logout_user()
    return redirect(url_for("main.index"))



@admin.route('/profile', methods=['GET'])
@roles_accepted('admin')
def edit_profile():
    user_info = current_user
    return render_template('admin/profile.html', info=user_info)


@admin.route('/save-profile', methods=['POST', 'GET'])
@roles_accepted('admin')
def save_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    try:
        user = User.query.filter_by(id=current_user.id).update({"username": username, "email": email})
    except SQLAlchemyError as e:
        flash(f"{str(e.__dict__['orig'])}", "alert text-center")
        db.session.rollback()
        redirect(url_for("patient.edit_profile"))
    except OperationalError as o:
        flash(f"{str(o.__dict__['orig'])}", "alert text-center")
        db.session.rollback()
        return redirect(url_for("admin.edit_profile"))
    else:
        db.session.commit()
    flash("Successfully edit user profile.", "success text-center")
    return redirect(url_for("admin.edit_profile"))


@admin.route('/change-password', methods=['POST', 'GET'])
@roles_accepted('admin')
def change_password():
    old_pwd = request.form.get('old_password')
    new_pwd = request.form.get('new_password')
    confirm_pwd = request.form.get('password_confirm')
    user = User.query.filter_by(id=current_user.id).first()
    if user and user.verify_password(old_pwd):
        if new_pwd.__ne__(confirm_pwd):
            flash("Password does not match Password confirmation. Please match the passwords.", "alert")
            return redirect(url_for("admin.edit_profile"))
        user = User.query.filter_by(id=current_user.id).update({"password": bcrypt.generate_password_hash(new_pwd)})
        db.session.commit()
        flash("Successfully change password!", "success text-center")
        return redirect(url_for("admin.edit_profile"))