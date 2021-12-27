from extensions import db
from sqlalchemy import TIMESTAMP
from datetime import datetime


class Appointment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.Date(), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(100), nullable=False, default='pending')
    comment = db.Column(db.String(255), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False, )
    active = db.Column(db.Boolean())

    def __str__(self):
        return f"{self.date} {self.time}"

    def __init__(self, date, time, doctor_id, patient_id, status, comment, active=1):
        self.date = date
        self.time = time
        self.doctor_id = doctor_id
        self.patient_id = patient_id
        self.status = status
        self.comment = comment
        self.active = active
