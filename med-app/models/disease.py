from extensions import db
from sqlalchemy import TIMESTAMP
from datetime import datetime

class Disease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    created_at = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False, )
    def __str__(self):
        return self.name

    def __init__(self, name, desc):
        self.name = name
        self.description = desc