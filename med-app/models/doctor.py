from extensions import db
from sqlalchemy import TIMESTAMP
from datetime import datetime

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consultation_fee = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False, )
    specialisation_id = db.Column(db.Integer, db.ForeignKey('specialisation.id'), nullable=False)
    prescriptions = db.relationship('Prescription', backref='doctor')
    appointments = db.relationship('Appointment', backref='doctor')
    active = db.Column(db.Boolean())
    def __init__(self, fee, user_id, spec_id, active=1):
        self.consultation_fee = fee
        self.user_id = user_id
        self.specialisation_id = spec_id
        self.active = active
