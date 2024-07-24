from flask import Blueprint, redirect, render_template, request, flash, jsonify, url_for
from flask_login import login_required, current_user
from .models import Note, Car, CarBrand
from . import db
from datetime import datetime
import json

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) <= 1:
            flash('Note is too shory!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added', category='success')    

    return render_template("home.html", user=current_user)




@views.route('delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            flash('Note deleted', category='success')

    return jsonify({})       

# @views.route('/add-transaction', methods=['GET', 'POST'])
# @login_required 
# def add_transaction():
#     if request.method == 'POST':
#         amount = request.form.get('amount')
#         category = request.form.get('category')
#         date_str = request.form.get('date')
#         description = request.form.get('description')

#         date = datetime.strptime(date_str, '%Y-%m-%d').date()

        
#         new_transaction = Transaction(
#             user_id=current_user.id,
#             amount=float(amount),
#             category=category,
#             date=date,
#             description=description)
#         db.session.add(new_transaction)
#         db.session.commit()
#         flash('Transaction added', category='success')
#     else:
#         flash('Problim with adding the transaction', category='error')

#     return render_template('add_transaction.html', user=current_user)        


@views.route('/view_ransactions', methods=['GET', 'POST'])      
@login_required  
def view_transactions():
    return render_template('view_transactions.html', user=current_user)





@views.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    if request.method == 'POST':
        min_range = float(request.form.get('minRange', 0))  # Convert to float, default to 0
        min_price = float(request.form.get('minPrice', 0))  # Convert to float, default to 0
        max_price = float(request.form.get('maxPrice', float('inf')))  # Convert to float, default to infinity
        preferred_brand = request.form.get('preferredBrands')
        usage = request.form.get('usage')
        fast_charging_max_time = float(request.form.get('fastChargingMaxTime', 0))

        print(min_range)
        preferences = {
            'min_range': min_range,
            'min_price': min_price,
            'max_price': max_price,
            'preferred_brand': preferred_brand,
            'usage': usage,
            'fast_charging_max_time': fast_charging_max_time
        }
        cars = Car.query.all()
        cars_score = [(car.model, analyze_results(car, preferences)) for car in cars]
        print('cars score:')
        for car_model, score in cars_score:
            print(f"{car_model}: {score}")

    car_brands = CarBrand.query.all()
    return render_template("preferences.html", car_brands=car_brands,  user=current_user)



def analyze_results(car, preferences):
    score = 0
    if car.range >= preferences['min_range']:
        score += 1
    if car.model == preferences['preferred_brand']:
        score += 1
    if car.fast_chargingTime <= preferences['fast_charging_max_time']:
        score += 1    

    return score    





