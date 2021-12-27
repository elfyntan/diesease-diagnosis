import os
from flask import Flask
from flask_security.utils import hash_password
from wtforms import StringField, DateField, RadioField
from wtforms.validators import DataRequired as Required
from models.role import Role
from models.user import User
from models.location import Location
from models.appointments import Appointment
from models.disease import Disease
from models.doctor import Doctor
from models.patient import Patient
from models.prescription import Prescription
from models.specialisation import Specialisation
from main.routes import main
from patient.routes import pat
from doctor.routes import doc
from admin.routes import admin
from flask_security import Security, SQLAlchemyUserDatastore, RegisterForm, user_registered
from extensions import db, login_manager, bcrypt


class ExtendRegisterForm(RegisterForm):
    username = StringField('Username', validators=[Required()])
    sex = RadioField('Gender', choices=[('F', 'Female'), ('M', 'Male')], validators=[Required()])
    dob = start_date = DateField('DOB', validators=[Required()])

    # LOCATION
    street = StringField('Street', validators=[Required()])
    city = StringField('City', validators=[Required()])
    country = StringField('Country', validators=[Required()])


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True, static_url_path='',
                static_folder='../static', template_folder='../templates')

    if test_config is None:
        app.config.from_pyfile("../config.py")
        print('------configuration----------')
    else:
        app.config.from_mapping(test_config)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    login_manager.login_view = 'login'
    login_manager.init_app(app)
    bcrypt.init_app(app)

    app.register_blueprint(main, url_prefix='/')
    app.register_blueprint(pat, url_prefix='/patient')
    app.register_blueprint(doc, url_prefix='/doctor')
    app.register_blueprint(admin, url_prefix='/admin')

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore, register_form=ExtendRegisterForm)

    @user_registered.connect_via(app)
    def user_registered_sighandler(app, user, confirm_token):
        user_role = user_datastore.find_role("patient")
        user_datastore.add_role_to_user(user, user_role)
        db.session.commit()

    def build_sample_db():
        """
            Populate a small db with some example entries.
        """
        with app.app_context():
            db.drop_all()
            db.create_all()
            patient_role = Role(name='patient')
            doctor_role = Role(name='doctor')
            admin_role = Role(name='admin')

            db.session.add(patient_role)
            db.session.add(doctor_role)
            db.session.add(admin_role)

            admin = user_datastore.create_user(
                username='admin',
                email='admin@med.com',
                phone='0777547547',
                password=bcrypt.generate_password_hash('pass@admin'),
                roles=[admin_role]
            )
            """
            print(' --- ADMIN ROLE ---')
            doctor1 = user_datastore.create_user(
                username='samuel',
                email='samuel@med.com',
                phone='0713222556',
                password=hash_password('pass@doctors'),
                roles=[doctor_role]
            )
            print(' --- DOCTOR ROLE ---')
            patient1 = user_datastore.create_user(
                username='henry',
                email='henry@med.com',
                phone='0714222555',
                password=hash_password('pass@patient'),
                roles=[patient_role]
            )
            print(' --- PATIENT 1 ROLE ---')
            patient2 = user_datastore.create_user(
                username='leon',
                email='leon@med.com',
                phone='0719262557',
                password=hash_password('pass@patient'),
                roles=[patient_role]
            )
            print(' --- PATIENT 2 ROLE ---')
            print(' --- Before commit ---')"""
            db.session.commit()
            print(' --- After commit ---')
        return
    build_sample_db()

    return app
