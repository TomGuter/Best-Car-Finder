from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')


class CarBrand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    cars = db.relationship('Car', backref='brand', lazy=True)


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100))
    range = db.Column(db.Integer)
    fast_chargingTime = db.Column(db.Integer)
    price = db.Column(db.Integer, default=0)
    usage = db.Column(db.String)
    daily_commute = db.Column(db.Integer, default=0)
    manufacturing_country = db.Column(db.String)
    brand_id = db.Column(db.Integer, db.ForeignKey('car_brand.id'))






  



# class Transaction(db.Model):
#     __tablename__ = 'transactions'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     amount = db.Column(db.Float, nullable=False)
#     category = db.Column(db.String(50))
#     date = db.Column(db.Date, nullable=False) 
#     description = db.Column(db.String(200))


