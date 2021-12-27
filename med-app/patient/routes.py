from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from flask_security import roles_accepted, SQLAlchemyUserDatastore
from flask_security.utils import hash_password

from extensions import db, bcrypt, SQLAlchemyError, OperationalError
from models.appointments import Appointment
from models.doctor import Doctor
from models.location import Location
from models.patient import Patient
from models.role import Role
from models.specialisation import Specialisation
from models.user import User
from models.prescription import Prescription

pat = Blueprint('patient', __name__, static_folder='../static', template_folder='../templates')


@pat.route('/')
@roles_accepted('patient')
def pat_dash():
    user = current_user.username
    return render_template('patient/dashboard_history.html', username=user)


@pat.route('/book_appointment')
@roles_accepted('patient')
def choose_doctor():
    serv = Specialisation.query.all()
    services = []
    for service in serv:
        doctors = []
        for d in service.doctors:
            doc = User.query.get(d.user_id)
            doc = {"doc": d, "user": doc}
            doctors.append(doc)
        service = {"service": service, "doctors": doctors}
        services.append(service)
    return render_template('patient/book_appointment.html', services=services)


@pat.route('/book_now/<id>', methods=['POST', 'GET'])
@roles_accepted('patient')
def book_appointment(id=None):
    if id is None:
        return "NONE"
    else:
        user = User.query.get(id)
        doctor = Doctor.query.filter_by(user_id=id).first()
        spec = Specialisation.query.get(doctor.specialisation_id)
        data = {"user": user, "doctor": doctor, "spec": spec}
        return render_template('patient/book_app_form.html', data=data)


@pat.route('/save_appointment', methods=['POST'])
def save_appointment():
    if request.method == "POST":
        patient_id = current_user.id
        patient = Patient.query.filter_by(user_id=patient_id).first()
        doctor_id = request.form.get("doctor_id")
        status = "pending"
        time = request.form.get('time')
        date = request.form.get('date')
        comment = request.form.get('comment')
        appointment = Appointment(patient_id=patient.id, doctor_id=doctor_id, status=status, time=time, date=date,
                                  comment=comment)
        db.session.add(appointment)
        db.session.commit()
        flash(f"You have successful scheduled an appointment on with a doctor on {date} {time}", "success text-center")
        return redirect(url_for("patient.appointments_history"))


@pat.route('/appointment-cancel/<id>', methods=['POST', 'GET'])
@roles_accepted('patient')
def cancel_appointment(id=None):
    if id is None:
        return "NONE"
    else:
        app_cancelled = Appointment.query.filter_by(id=id).update({"status": "cancel"})
        db.session.commit()
        flash(f"Appointment successfully cancelled", "success text-center")
        return redirect(url_for("patient.appointments_history"))


@pat.route('/appointments-history')
@roles_accepted('patient')
def appointments_history():
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    # appointments = Appointment.query.filter(Appointment.patient_id==patient.id).all()
    appointments = []
    for appointment in patient.appointments:
        doc = Doctor.query.get(appointment.doctor_id)
        user = User.query.get(doc.user_id)
        service = Specialisation.query.get(doc.specialisation_id)
        new_app = {"consultation_fee": doc.consultation_fee, "doctor": user, "service": service,
                   "date": appointment.date, "time": appointment.time, "status": appointment.status,
                   "id": appointment.id, "created_at": appointment.created_at}
        appointments.append(new_app)
    return render_template('patient/appointments_history.html', appointments=appointments)


user_datastore = SQLAlchemyUserDatastore(db, User, Role)


@pat.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        if password.__ne__(password_confirm):
            flash("Password does not match Password confirmation. Please match the passwords.", "alert")
            return render_template("security/register_user.html")
        # LOCATION
        street = request.form.get('street')
        city = request.form.get('city')
        country = request.form.get('country')

        # PATIENT
        dob = request.form.get('dob')
        sex = request.form.get('sex')
        patient_role = Role(name='patient')

        try:
            user = user_datastore.create_user(username=username, email=email,
                                              password=bcrypt.generate_password_hash(password), roles=[patient_role])
            db.session.add(user)
            db.session.commit()
            location = Location(street=street, city=city, country=country, user_id=user.id)
            patient1 = Patient(dob=dob, gender=sex, user_id=user.id)
            db.session.add(location)
            db.session.add(patient1)
        except SQLAlchemyError as e:
            flash(f"{str(e.__dict__['orig'])}", "danger text-center")
            db.session.rollback()
            return render_template("security/register_user.html")
        except OperationalError as o:
            flash(f"{str(o.__dict__['orig'])}", "danger text-center")
            db.session.rollback()
            return render_template("security/register_user.html")
        else:
            db.session.commit()
        return redirect(url_for("main.login"))


@pat.route('/profile', methods=['GET'])
@roles_accepted('patient')
def edit_profile():
    user_info = current_user
    pat = Patient.query.filter_by(user_id=current_user.id).first()
    specs = Specialisation.query.all()
    data = {"user": user_info, "pat": pat}
    return render_template('patient/profile.html', info=data)


@pat.route('/save-profile', methods=['POST', 'GET'])
@roles_accepted('patient')
def save_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    phone = request.form.get('phone')
    dob = request.form.get('dob')
    sex = request.form.get('gender')
    street = request.form.get('street')
    city = request.form.get('city')
    country = request.form.get('country')
    try:
        user = User.query.filter_by(id=current_user.id).update({"username": username, "email": email, "phone": phone})
        location = Location.query.filter_by(user_id=current_user.id).update({"street": street, "city": city, "country": country})
    except SQLAlchemyError as e:
        flash(f"{str(e.__dict__['orig'])}", "alert text-center")
        db.session.rollback()
        redirect(url_for("patient.edit_profile"))
    except OperationalError as o:
        flash(f"{str(o.__dict__['orig'])}", "alert text-center")
        db.session.rollback()
        return redirect(url_for("patient.edit_profile"))
    else:
        db.session.commit()
    flash("Successfully edit user profile.", "success text-center")
    return redirect(url_for("patient.edit_profile"))


@pat.route('/change-password', methods=['POST', 'GET'])
@roles_accepted('patient')
def change_password():
    old_pwd = request.form.get('old_password')
    new_pwd = request.form.get('new_password')
    confirm_pwd = request.form.get('password_confirm')
    user = User.query.filter_by(id=current_user.id).first()
    if user and user.verify_password(old_pwd):
        if new_pwd.__ne__(confirm_pwd):
            flash("Password does not match Password confirmation. Please match the passwords.", "alert")
            return redirect(url_for("patient.edit_profile"))
        user = User.query.filter_by(id=current_user.id).update({"password": bcrypt.generate_password_hash(new_pwd)})
        db.session.commit()
        flash("Successfully change password!", "success text-center")
        return redirect(url_for("patient.edit_profile"))


@pat.route('/prescriptions', methods=['GET'])
@roles_accepted('patient')
def prescriptions():
    prescriptions = Patient.query.filter_by(user_id=current_user.id).first().prescriptions
    prescrips = []
    for p in prescriptions:
        p_user = User.query.get(Doctor.query.get(p.doctor_id).user_id)
        presc = {"id": str(p.id), "doctor": p_user, "created_at": p.created_at, "prescription": p.prescription}
        prescrips.append(presc)
    return render_template("patient/prescriptions.html", prescriptions=prescrips)

@pat.route('/prescription/<id>', methods=['GET'])
@roles_accepted('patient')
def prescription(id):
    prescription = Prescription.query.get(id)
    return render_template("patient/prescription.html", presc=prescription)
"""

def change_password():
    return "password changed"



def delete_appointment_record():
    return "deleting record"

def diagnosis_history():
    return "appointment history"

def clear_diagnosis_history():
    return "appointment history"

def remove_diagnosis_record():
    return "appointment history"


"""
