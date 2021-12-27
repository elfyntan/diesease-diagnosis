from datetime import date, datetime

from flask import  Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from flask_security import roles_accepted
from models.prescription import Prescription
from models.doctor import Doctor
from models.patient import Patient
from models.specialisation import Specialisation
from models.appointments import  Appointment
from models.location import Location
from models.user import User
from extensions import db, bcrypt, SQLAlchemyError, OperationalError

doc = Blueprint('doctor', __name__)


@doc.route('/')
@roles_accepted('doctor')
def doc_dash():
    user = current_user.username
    return render_template('doctor/dash_history.html', username=user)

@doc.route('/create-prescription/<patient_id>/<app_id>', methods=['GET'])
@roles_accepted('doctor')
def create_prescription(patient_id, app_id):
    todays_date = date.today()
    patient = Patient.query.get(patient_id)
    patient_info = User.query.get(patient.user_id)
    doc_info = current_user
    doc = Doctor.query.filter_by(user_id=current_user.id).first()
    doc_spec = Specialisation.query.get(doc.specialisation_id)
    age =todays_date.today() - patient.dob

    data = {"doc_info": current_user, "doc":doc, "patient": patient, "patient_info":patient_info,
            "spec": doc_spec, "patient_age":age, "app_id":app_id}
    return render_template('doctor/create_prescription.html', data=data)

@doc.route('/save-prescription', methods=['POST', 'GET'])
@roles_accepted('doctor')
def save_prescription():
    if request.method=="POST":
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        patient_id = request.form.get("patient_id")
        appointment_id = request.form.get("appointment_id")
        prescription = request.form.get('prescription')
        prescription = Prescription(patient_id=patient_id, doctor_id=doctor.id, prescription=prescription)
        db.session.add(prescription)
        app_updated = Appointment.query.filter_by(id=appointment_id).update({"status": "approved"})
        db.session.commit()
        return redirect(url_for('doctor.prescriptions'))

@doc.route('/prescriptions', methods=['GET'])
@roles_accepted('doctor')
def prescriptions():
    prescriptions = Doctor.query.filter_by(user_id=current_user.id).first().prescriptions
    prescrips=[]
    for p in prescriptions:
        p_user = User.query.get(Patient.query.get(p.patient_id).user_id)
        presc = {"id":str(p.id), "patient":p_user, "created_at": p.created_at, "prescription": p.prescription}
        prescrips.append(presc)
    return render_template("doctor/prescriptions.html", prescriptions=prescrips)

@doc.route('/prescription/<id>', methods=['GET'])
@roles_accepted('doctor')
def prescription(id):
    prescription = Prescription.query.get(id)
    return render_template("doctor/prescription.html", presc=prescription)

@doc.route('/appointments-history', methods=['GET'])
@roles_accepted('doctor')
def appointments_history():
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    # appointments = Appointment.query.filter(Appointment.patient_id==patient.id).all()
    appointments = []
    for appointment in doctor.appointments:
        patient = Patient.query.get(appointment.patient_id)
        user = User.query.get(patient.user_id)
        new_app = { "patient": patient, "user":user, "app":appointment}
        appointments.append(new_app)
    return render_template('doctor/appointments.html', appointments=appointments)

@doc.route('/profile', methods=['GET'])
@roles_accepted('doctor')
def edit_profile():
    user_info = current_user
    doc = Doctor.query.filter_by(user_id=current_user.id).first()
    spec = Specialisation.query.get(doc.specialisation_id)
    specs = Specialisation.query.all()
    data = {"user":user_info, "doc":doc, "spec":spec}
    return render_template('doctor/profile.html', info=data, specs=specs)


@doc.route('/change-password', methods=['POST', 'GET'])
@roles_accepted('doctor')
def change_password():
    old_pwd = request.form.get('old_password')
    new_pwd = request.form.get('new_password')
    confirm_pwd = request.form.get('password_confirm')
    user = User.query.filter_by(id=current_user.id).first()
    if user and user.verify_password(old_pwd):
        if new_pwd.__ne__(confirm_pwd):
            flash("Password does not match Password confirmation. Please match the passwords.", "alert")
            return redirect(url_for("doctor.edit_profile"))
        user = User.query.filter_by(id=current_user.id).update({"password": bcrypt.generate_password_hash(new_pwd)})
        db.session.commit()
        flash("Successfully change password!", "success text-center")
        return redirect(url_for("doctor.edit_profile"))


@doc.route('/save-profile', methods=['POST', 'GET'])
@roles_accepted('doctor')
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
        redirect(url_for("doctor.edit_profile"))
    except OperationalError as o:
        flash(f"{str(o.__dict__['orig'])}", "alert text-center")
        db.session.rollback()
        return redirect(url_for("doctor.edit_profile"))
    else:
        db.session.commit()
    flash("Successfully edit user profile.", "success text-center")
    return redirect(url_for("doctor.edit_profile"))