from cmath import sqrt
from flask import Blueprint, redirect, render_template, request, flash, jsonify, url_for, session
from flask_login import login_required, current_user
from .models import Note, Car, CarBrand, CurrentUserPreferences, UserWishList
from . import db
from datetime import datetime
import json
import ast

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    wish_list_car = UserWishList.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) <= 1:
            flash('Note is too shory!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added', category='success')    

    cars = Car.query.all()
    return render_template("home.html", cars=cars, wish_list_car=wish_list_car, user=current_user)




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




@views.route('/removeFromWishList', methods=['POST'])
@login_required
def remove_from_wish_list():
    data = json.loads(request.data)
    car_id = data.get('carId')
     
    if car_id:
        wish_list_entry = UserWishList.query.filter_by(user_id=current_user.id, id=car_id).first()
        
        if wish_list_entry:
            db.session.delete(wish_list_entry)
            db.session.commit()
            flash('Car removed from wish list', category='success')
            return jsonify({'success': True}), 200
        
    flash('Failed to remove car from wish list', category='error')
    return jsonify({'success': False}), 400





@views.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    if request.method == 'POST':
        min_range = float(request.form.get('minRange', 0))  
        min_price = float(request.form.get('minPrice', 0))  
        max_price = float(request.form.get('maxPrice', float('inf')))  
        preferred_brands = json.dumps(request.form.getlist('preferredBrands'))
        no_way_brands = json.dumps(request.form.getlist('no_way_brands'))
        usage = 'Null'
        #usage = request.form.get('usage')
        daily_commute = float(request.form.get('daily_commute'))
        fast_charging_max_time = float(request.form.get('fastChargingMaxTime', 0))
        manufacturing_country = json.dumps(request.form.getlist('manufacturing_country'))
        segment = json.dumps(request.form.getlist('car_segment'))
        isSafety_rating = int(request.form.get('ncap_rating'))
        isBig_screen = int(request.form.get('screen_size'))
        horse_power_rating = int(request.form.get('horse_power_rating'))


        #print(segment)
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
                current_user_preferences.no_way_brands = no_way_brands
                current_user_preferences.usage = usage
                current_user_preferences.daily_commute = daily_commute
                current_user_preferences.fast_charging_max_time = fast_charging_max_time
                current_user_preferences.manufacturing_country = manufacturing_country
                current_user_preferences.segment = segment
                current_user_preferences.isSafety_rating = isSafety_rating
                current_user_preferences.isBig_screen = isBig_screen
                current_user_preferences.horse_power_rating = horse_power_rating
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
                manufacturing_country=manufacturing_country,
                segment=segment,
                isSafety_rating=isSafety_rating,
                isBig_screen=isBig_screen,
                no_way_brands=no_way_brands,
                horse_power_rating=horse_power_rating
                )
                db.session.add(current_user_preferences)

            db.session.commit()
            session['from_preferences'] = True
            return redirect(url_for('views.results'))    

    car_brands = CarBrand.query.all()
    return render_template("preferences.html", car_brands=car_brands,  user=current_user)





def analyze_results(car, preferences):
    score = 0

    if car.brand.name in preferences['no_way_brands']:
        return 0

    if car.range >= preferences['min_range']:
        if car.range - preferences['min_range'] <= 20:
            score += 1
        elif car.range - preferences['min_range'] <= 40:
            score += 2
        elif car.range - preferences['min_range'] <= 60:
            score += 3
        elif car.range - preferences['min_range'] <= 80:
             score += 4
        elif car.range - preferences['min_range'] <= 100:
            score += 5     
        else:
            score += 6               
    if  'nothing' in preferences['preferred_brands'] or car.model in preferences['preferred_brands']:
        score += 1
    if car.fast_chargingTime <= preferences['fast_charging_max_time']:
        if abs(car.fast_chargingTime - preferences['fast_charging_max_time']) <= 5:
            score += 1
        elif abs(car.fast_chargingTime - preferences['fast_charging_max_time']) <= 10:
            score += 2
        elif abs(car.fast_chargingTime - preferences['fast_charging_max_time']) <= 15:
            score += 3
        elif abs(car.fast_chargingTime - preferences['fast_charging_max_time']) <= 15:
            score += 4
        elif abs(car.fast_chargingTime - preferences['fast_charging_max_time']) <= 20:
            score += 5
        elif abs(car.fast_chargingTime - preferences['fast_charging_max_time']) <= 25:
            score += 6
        elif abs(car.fast_chargingTime - preferences['fast_charging_max_time']) <= 30:
            score += 7        
        else:
            score += 8                 

    if car.price <= preferences['max_price']:
        if preferences['max_price'] - car.price <= 5000:
            score += 8
        elif preferences['max_price'] - car.price <= 10000:
            score += 7
        elif preferences['max_price'] - car.price <= 20000:
            score += 6
        elif preferences['max_price'] - car.price <= 30000:
            score += 5
        elif preferences['max_price'] - car.price <= 40000:
            score += 4
        elif preferences['max_price'] - car.price <= 60000:
            score += 3 
        elif preferences['max_price'] - car.price <= 90000:
            score += 2
        else:
            score += 1  
              
    if 100-((preferences['max_price']/car.price)*100) > 20:
        return 0 # in a case that the car price is higher than the maimum price the client is considering to pay in more than 20%
        
 
    if abs(car.price <= preferences['min_price']) <= 15000:
        score += 1   
    elif abs(car.price <= preferences['min_price']) <= 10000:
        score += 2
    elif abs(car.price <= preferences['min_price']) <= 5000:
        score += 2;     
    
    if 'Any_Country' in preferences['manufacturing_country']:
        score += 1
    
    if car.manufacturing_country in preferences['manufacturing_country']:
        score += 3    

    if car.usage == preferences['usage']:
        score += 3

    if car.daily_commute >= preferences['daily_commute']:
        if car.daily_commute - preferences['daily_commute'] <= 10:
            score += 1
        elif car.daily_commute - preferences['daily_commute'] <= 20:
            score += 2    
        elif car.daily_commute - preferences['daily_commute'] <= 30:
            score += 3
        elif car.daily_commute - preferences['daily_commute'] <= 50:
            score += 4
        elif car.daily_commute - preferences['daily_commute'] <= 100:
            score += 5 
        elif car.daily_commute - preferences['daily_commute'] <= 150:
            score += 6
        elif car.daily_commute - preferences['daily_commute'] <= 200:
            score += 7
        elif car.daily_commute - preferences['daily_commute'] <= 250:
            score += 8
        elif car.daily_commute - preferences['daily_commute'] <= 300:
            score += 9
        elif car.daily_commute - preferences['daily_commute'] <= 350:
            score += 10
        else:
            score += 11   



    # Convert string representation of list to actual list
    categories = ast.literal_eval(car.segment)  # This should convert the string into a list

    for category in categories:
        category = category.strip()  # Clean up any extra spaces
        if category == 'SUV' or category == 'Sedan':
            score += 30
        elif category in preferences['segment']:
            score += 10


    

    if car.isSafety_rating >= preferences['isSafety_rating']:
        if car.isSafety_rating == preferences['isSafety_rating']:   
            score += 10
        else:
            score += 3
    elif car.isSafety_rating == 1 and preferences['isSafety_rating'] == 5:
        return 0
    
    
    
    if car.screen_size == 5 and preferences['isBig_screen'] > 13:
        score += 10
    elif car.screen_size >= 3 and preferences['isBig_screen'] >= 11:   
        score += 10
    else:
        score += 1
    if car.screen_size <= 10 and preferences['isBig_screen'] == 5:
        return 0

    if preferences['horse_power_rating'] >= 4:
        if preferences['horse_power_rating'] == 5 and (car.horse_power/car.weight)*100 >= 20:
            score += 20
        elif preferences['horse_power_rating'] == 5 and (car.horse_power/car.weight)*100 <= 10:
            score -= 15    
        elif preferences['horse_power_rating'] == 4 and (car.horse_power/car.weight)*100 >= 14:
            score += 15

    elif preferences['horse_power_rating'] == 3:
        if (car.horse_power/car.weight)*100 >= 9:
            score += 13



    if preferences['horse_power_rating'] >= 4 and car.acceleration <= 6:
        if preferences['horse_power_rating'] == 5 and car.acceleration <= 4:
            score += 20
        elif preferences['horse_power_rating'] == 5 and car.acceleration <= 3.5:
            score += 30
        elif car.acceleration <= 5:
            score += 10
        elif car.acceleration <= 6:
            score += 5
    elif preferences['horse_power_rating'] >= 4 and car.acceleration >= 7:
        if car.acceleration >= 7 and car.acceleration <= 8:
            score -= 10
        elif car.acceleration >= 8 and car.acceleration <= 9:
            score -= 15
        else:
            score -= 20             

                            
    
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
        'no_way_brands': current_user_preferences.no_way_brands,
        'isSafety_rating': current_user_preferences.isSafety_rating,
        'isBig_screen': current_user_preferences.isBig_screen,
        'segment': current_user_preferences.segment,
        'usage': current_user_preferences.usage,
        'daily_commute': current_user_preferences.daily_commute,
        'fast_charging_max_time': current_user_preferences.fast_charging_max_time,
        'manufacturing_country': current_user_preferences.manufacturing_country,
        'horse_power_rating': current_user_preferences.horse_power_rating
    }
    else:
        preferences_dictionary = {}    
     
    cars = Car.query.all()
    cars_score = [(car.brand.name, car.model, car.range, car.fast_chargingTime, car.price, car.manufacturing_country, car.range, car.img, car.horse_power, car.acceleration, analyze_results(car, preferences_dictionary)) for car in cars]
    sorted_cars_score = sorted(cars_score, key=lambda x: x[10], reverse=True)
    index_of_first_zero = next((index for index, car in enumerate(sorted_cars_score) if car[10] == 0), len(sorted_cars_score))
    print(index_of_first_zero)
    options_num = len(sorted_cars_score)            

    result_limit = min(index_of_first_zero, 3)
    if request.method == 'POST':
        result_limit = int(request.form.get('result_limit')) 
        if result_limit > options_num:
            flash('Number of results to display cannot be greater than maximum possible options', category='error')

    session.pop('from_preferences', None)
    return render_template('results.html',sorted_cars_score=sorted_cars_score, result_limit=result_limit, options_num=index_of_first_zero, index=0, user=current_user)




@views.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    brand = request.form.get('brand')
    model = request.form.get('model')
    range_ = request.form.get('range')
    fast_charging_time = request.form.get('fast_charging_time')
    price = request.form.get('price')
    manufacturing_country = request.form.get('manufacturing_country')
    score_result = request.form.get('score_result')

    existing_query = UserWishList.query.filter_by(
        user_id=current_user.id,
        brand=brand,
        model=model
    ).first()

    if existing_query:
        flash('Car is already in your wishlist.', category='error')
        return redirect(url_for('views.results'))
    
    new_car_wish = UserWishList(
        user_id=current_user.id,
        brand=brand,
        model=model,
        range=range_,
        fast_charging_time=fast_charging_time,
        price=price,
        manufacturing_country=manufacturing_country,
        score_result=score_result
    )
    db.session.add(new_car_wish)
    db.session.commit()

    flash('Car added to your wishlist!', category='success')
    return redirect(url_for('views.results'))




@views.route('/wish-list', methods=['GET', 'POST'])
def wish_list():
    wish_list_car = UserWishList.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) <= 1:
            flash('Note is too shory!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added', category='success')    

    return render_template('wish-list.html', user=current_user)
