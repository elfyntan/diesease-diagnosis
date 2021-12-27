from extensions import db
from sqlalchemy import TIMESTAMP
from datetime import datetime

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prescription = db.Column(db.String(255), nullable=False)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False, )
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    active = db.Column(db.Boolean())

    def __str__(self):
        return self.prescription