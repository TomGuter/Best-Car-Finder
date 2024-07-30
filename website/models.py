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
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    notes = db.relationship('Note')


class CarBrand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    cars = db.relationship('Car', backref='brand', lazy=True)


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100))
    range = db.Column(db.Integer)
    horse_power = db.Column(db.Integer)
    acceleration = db.Column(db.Integer)
    fast_chargingTime = db.Column(db.Integer)
    price = db.Column(db.Integer, default=0)
    usage = db.Column(db.String)
    daily_commute = db.Column(db.Integer, default=0)
    manufacturing_country = db.Column(db.String)
    segment = db.Column(db.Text, default=[])
    isSafety_rating = db.Column(db.Integer)
    screen_size = db.Column(db.Integer)
    weight = db.Column(db.Integer) 
    img = db.Column(db.String)
    year = db.Column(db.Integer) 
    car_data_url = db.Column(db.String)
    car_data_list_info = db.Column(db.Text, default=[])
    car_data_final_range = db.Column(db.Text, default=[])
    brand_id = db.Column(db.Integer, db.ForeignKey('car_brand.id'))
    userWishList = db.relationship('UserWishList', backref='car')


class CurrentUserPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    min_range = db.Column(db.Float, default=0.0)
    min_price = db.Column(db.Float, default=0.0)
    max_price = db.Column(db.Float, default=float('inf'))
    preferred_brands = db.Column(db.Text, default=[])
    no_way_brands = db.Column(db.Text, default=[])
    usage = db.Column(db.String(50), nullable=True)
    daily_commute = db.Column(db.Float, default=0.0)
    fast_charging_max_time = db.Column(db.Float, default=0.0)
    manufacturing_country = db.Column(db.Text, default=[])
    segment = db.Column(db.Text, default=[])
    isSafety_rating = db.Column(db.Integer)
    isBig_screen = db.Column(db.Integer)
    horse_power_rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    counter = db.Column(db.Integer, default=1) # counts the times the user submit its preferences in the file
    user = db.relationship('User', backref='preferences', lazy=True)




class UserWishList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    model = db.Column(db.String)
    brand = db.Column(db.String)
    score_result = db.Column(db.Integer)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'))

