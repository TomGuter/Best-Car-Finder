from flask import Blueprint, redirect, render_template, request, flash, jsonify, url_for, session
from flask_login import login_required, current_user
from .models import Note, Car, CarBrand, CurrentUserPreferences
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






@views.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    if request.method == 'POST':
        min_range = float(request.form.get('minRange', 0))  
        min_price = float(request.form.get('minPrice', 0))  
        max_price = float(request.form.get('maxPrice', float('inf')))  
        preferred_brands = json.dumps(request.form.getlist('preferredBrands'))
        usage = request.form.get('usage')
        daily_commute = float(request.form.get('daily_commute'))
        fast_charging_max_time = float(request.form.get('fastChargingMaxTime', 0))
        manufacturing_country = json.dumps(request.form.getlist('manufacturing_country'))

        if min_price < 0:
            flash('Minimum price cannot be negative.', category='error')
        elif max_price < min_price:
            flash('Maximum price cannot be less than minimum price.', category='error')
        elif fast_charging_max_time < 0:
            flash('Fast charging time cannot be negative.', category='error')
        elif len(manufacturing_country) < 0:
            flash('Must choose at least 1 country production', category='error')
        else:
                      
            current_user_preferences  = CurrentUserPreferences.query.filter_by(user_id=current_user.id).first()
            if current_user_preferences:
                # update the data in the database for the current user
                current_user_preferences.min_range = min_range
                current_user_preferences.min_price = min_price
                current_user_preferences.max_price = max_price
                current_user_preferences.preferred_brands = preferred_brands
                current_user_preferences.usage = usage
                current_user_preferences.daily_commute = daily_commute
                current_user_preferences.fast_charging_max_time = fast_charging_max_time
                current_user_preferences.manufacturing_country = manufacturing_country
            else:
                #create new preferations for the user
                current_user_preferences = CurrentUserPreferences(
                user_id=current_user.id,
                min_range=min_range,
                min_price=min_price,
                max_price=max_price,
                preferred_brands=preferred_brands,
                usage=usage,
                daily_commute=daily_commute,
                fast_charging_max_time=fast_charging_max_time,
                manufacturing_country=manufacturing_country
                )
                db.session.add(current_user_preferences)

            db.session.commit()
            session['from_preferences'] = True
            return redirect(url_for('views.results'))    

    car_brands = CarBrand.query.all()
    return render_template("preferences.html", car_brands=car_brands,  user=current_user)





def analyze_results(car, preferences):
    score = 0
    if car.range >= preferences['min_range']:
        score += 1
    if  'nothing' in preferences['preferred_brands'] or car.model in preferences['preferred_brands']:
        score += 1
    if car.fast_chargingTime <= preferences['fast_charging_max_time']:
        score += 1
    if car.daily_commute <= preferences['max_price']:
        score += 1
    if car.daily_commute <= preferences['min_price']:
        score += 1;    
    if 'Any Country' in preferences['manufacturing_country'] or car.manufacturing_country in preferences['manufacturing_country']:
        score += 1
    if car.usage == preferences['usage']:
        score += 1

    return score    




@views.route('/results', methods=['GET', 'POST'])      
@login_required  
def results():
    
    preferences_status = CurrentUserPreferences.query.filter_by(user_id=current_user.id).first()
    if 'from_preferences' not in session and not preferences_status:
        flash('Please complete the preferences form before accessing results.', category='error')
        return redirect(url_for('views.preferences'))

    current_user_preferences = CurrentUserPreferences.query.filter_by(user_id=current_user.id).first()
    if current_user_preferences:
        preferences_dictionary = {
        'min_range': current_user_preferences.min_range,
        'min_price': current_user_preferences.min_price,
        'max_price': current_user_preferences.max_price,
        'preferred_brands': current_user_preferences.preferred_brands,
        'usage': current_user_preferences.usage,
        'daily_commute': current_user_preferences.daily_commute,
        'fast_charging_max_time': current_user_preferences.fast_charging_max_time,
        'manufacturing_country': current_user_preferences.manufacturing_country
    }
    else:
        preferences_dictionary = {}    
     
    cars = Car.query.all()
    cars_score = [(car.brand.name, car.model, car.range, car.fast_chargingTime, car.price, car.manufacturing_country, car.range, analyze_results(car, preferences_dictionary)) for car in cars]
    sorted_cars_score = sorted(cars_score, key=lambda x: x[2], reverse=True)
    options_num = len(sorted_cars_score)            

    result_limit = 3
    if request.method == 'POST':
        result_limit = int(request.form.get('result_limit')) 
        if result_limit > options_num:
            flash('Number of results to display cannot be greater than maximum possible options', category='error')

    session.pop('from_preferences', None)
    return render_template('results.html',sorted_cars_score=sorted_cars_score, result_limit=result_limit, options_num=options_num, index=0, user=current_user)





