from extensions import db
from sqlalchemy import TIMESTAMP
from datetime import datetime
# Define models
patient_diseases = db.Table(
    'patient_diseases',
    db.Column('patient_id', db.Integer(), db.ForeignKey('patient.id')),
    db.Column('disease_id', db.Integer(), db.ForeignKey('disease.id')),
    db.Column('result', db.String(50), nullable=False),
    db.Column('create_at', TIMESTAMP, default=datetime.utcnow, nullable=False, )
)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gender = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.Date(), nullable=False)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False, )
    active = db.Column(db.Boolean())
    # user = db.relationship("User", back_populates="patient")
    prescriptions = db.relationship('Prescription', backref='patient')
    appointments = db.relationship('Appointment', backref='patient')

    def __init__(self, gender, dob, user_id, active=1):
        self.gender = gender
        self.dob = dob
        self.user_id = user_id
        self.active = active
