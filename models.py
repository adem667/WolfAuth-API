from database import db
from datetime import datetime

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=False)
    max_users = db.Column(db.Integer, default=1)
    devices = db.relationship("Device", backref="account", lazy=True)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(100))
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    account_id = db.Column(db.Integer, db.ForeignKey("account.id"), nullable=False)

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(255), unique=True, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    max_users = db.Column(db.Integer, default=1)
