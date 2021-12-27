from extensions import  db
from sqlalchemy import TIMESTAMP
from datetime import datetime
class Specialisation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(255), nullable=False)
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False, )
    doctors = db.relationship('Doctor', backref='specialisation')
    active = db.Column(db.Boolean())

    def __str__(self):
        return self.name

    def __init__(self, name, img, active=1):
        self.name = name
        self.image = img
        self.active = active