from cmath import sqrt
import re
from flask import Blueprint, redirect, render_template, request, flash, jsonify, url_for, session
from flask_login import login_required, current_user

from website import car_pages
from .models import Note, Car, CarBrand, CurrentUserPreferences, UserWishList, Comparisons
from . import db
import json
import ast

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    cars = Car.query.all()
    return render_template("home.html", cars=cars, user=current_user)






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
                current_user_preferences.counter += 1
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








def score_for_category(side1, side2, score, category_value):
    res = abs(side1 - side2)
    res = (res/category_value)*100


    if side1 >= side2:
        if res <= 5:
            score += 5
        elif res <= 10:
            score += 10
        elif res <= 15:
            score += 15
        elif res <= 20:
            score += 20
        elif res <= 25:
            score += 25
        elif res <= 30:
            score += 30
        elif res <= 35:
            score += 35
        elif res <= 40:
            score += 40  
        elif res <= 45:
            score += 45
        else:
            score += 50
    else:
        if res >= 15:
            return 0

    return score
            


def analyze_results(car, preferences):
    score = 0           

    res = score_for_category(car.range, preferences['min_range'], score, car.range)
    if res == 0:
        return 0
    score += res

    res = score_for_category(car.daily_commute, preferences['daily_commute'], score, car.price)
    if res == 0:
        return 0
    score += res



    res = score_for_category(preferences['fast_charging_max_time'], car.fast_chargingTime, score, car.fast_chargingTime)
    if res == 0:
        return 0
    score += res


    if car.price < preferences['min_price']*0.9 or car.price*0.9 > preferences['max_price']:
        return 0
    else:
        res = score_for_category(preferences['min_price'], car.price, score, car.price)
        score += res
        res = score_for_category(preferences['max_price'], car.price, score, preferences['max_price'])
        score += res

    res = score_for_category(car.screen_size, preferences['isBig_screen'], score, car.screen_size)
    if res == 0:
        return 0
    score += res


    pref_brands = ast.literal_eval(preferences['preferred_brands'])
    for brand in pref_brands:
        brand = brand.strip()              
        if car.brand.name == brand:
            score += 40

    no_way_brands = ast.literal_eval(preferences['no_way_brands'])
    for now_way_brand in no_way_brands:
        now_way_brand = now_way_brand.strip()       
        if car.brand.name == now_way_brand:
            return 0
        
    manufacturing_country = ast.literal_eval(preferences['manufacturing_country'])
    for country in manufacturing_country:
        country = country.strip()
        if car.manufacturing_country == country:
            score += 15



    segments = ast.literal_eval(car.segment)  # this should convert the string into a list
    for segment in segments:
        segment = segment.strip()  # clean up any extra spaces
        if segment.lower() == 'suv' or segment.lower() == 'sedan':
            score += 30
        if segment.lower() in ["a (mini cars)", "b (small cars)"]:
            pref_segments = ast.literal_eval(preferences['segment']) 
            for pref_segment in pref_segments:
                if pref_segment.lower() in ["c (medium cars)", "d (large cars)"]:
                    return 0

        elif segment in preferences['segment']:
            score += 15



    if car.isSafety_rating >= preferences['isSafety_rating']:
        if car.isSafety_rating == 5 and preferences['isSafety_rating'] == 5:   
            score += 30
        elif car.isSafety_rating == 4 and preferences['isSafety_rating'] == 5:
            score += 10
        else:
            score += 5
    elif car.isSafety_rating <= 1 and preferences['isSafety_rating'] == 5:
        return 0
    
    
    
    res =  (car.horse_power/car.weight)*100 
    if preferences['horse_power_rating'] >= 4:
        if preferences['horse_power_rating'] == 5 and res >= 20:
            score += 30
        elif preferences['horse_power_rating'] == 4 and res >= 14:
            score += 15
        elif preferences['horse_power_rating'] == 5 and res <= 10:
            score -= 15    
        elif preferences['horse_power_rating'] == 5 and res <= 5:
            return 0
        
    elif preferences['horse_power_rating'] == 3:
        if res >= 10:
            score += 15


    if preferences['horse_power_rating'] >= 4 and car.acceleration <= 6:
        if preferences['horse_power_rating'] == 5 and car.acceleration <= 4:
            score += 30
        elif car.acceleration <= 5:
            score += 40
        elif preferences['horse_power_rating'] == 5 and car.acceleration <= 3.5:
            score += 50
        elif car.acceleration <= 6:
            score += 10

    elif preferences['horse_power_rating'] >= 4 and car.acceleration >= 7:
        if car.acceleration <= 7.5:
            score -= 5
        elif car.acceleration <= 8:
            score -= 10
        elif car.acceleration <= 8.5:
            score -= 15
        elif car.acceleration <= 9.2:
            score -= 20
        else:
            score = 0             

                            
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
    cars_score = [(car.brand.name, car.model, car.range, car.fast_chargingTime, car.price, car.manufacturing_country, car.range, car.img, car.horse_power, car.acceleration, car.year, analyze_results(car, preferences_dictionary)) for car in cars]
    sorted_cars_score = sorted(cars_score, key=lambda x: x[11], reverse=True)
    index_of_first_zero = next((index for index, car in enumerate(sorted_cars_score) if car[11] == 0), len(sorted_cars_score))
    print(index_of_first_zero)
    options_num = len(sorted_cars_score)            


    for car in sorted_cars_score:
        print(car[0], ",", car[1], "score: ", car[11])

    result_limit = min(index_of_first_zero, 3)
    if request.method == 'POST':
        result_limit = int(request.form.get('result_limit')) 
        print("result_limit:", result_limit)
        print("options_num:", options_num)
        if result_limit > options_num or result_limit > index_of_first_zero:
            flash('Number of results to display cannot be greater than maximum possible options', category='error')
            return redirect(url_for('views.results'))

    session.pop('from_preferences', None)
    return render_template('results.html',sorted_cars_score=sorted_cars_score, result_limit=result_limit, options_num=index_of_first_zero, index=0, user=current_user)




@views.route('/add_to_wishlist', methods=['POST'])
@login_required
def add_to_wishlist():
    user_id = current_user.id
    brand = request.form.get('brand')
    model = request.form.get('model')
    score_result = request.form.get('score_result')
    car = Car.query.filter_by(model=model).first()

    if car:
        car_id = car.id
        existing_query = UserWishList.query.filter_by(
            user_id=user_id,
            brand=brand,
            model=model
        ).first()

        if existing_query:
            flash('Car is already in your wishlist.', category='error')
        else:
            new_car_wish = UserWishList(
                user_id=user_id,
                brand=brand,
                model=model,
                score_result=score_result,
                car_id=car_id  
            )
            db.session.add(new_car_wish)
            db.session.commit()
            flash('Car added to your wishlist!', category='success')
    else:
        flash('Car not found.', category='error')

    return redirect(url_for('views.results'))





@views.route('/wish-list', methods=['GET', 'POST'])
def wish_list():
    wish_list_cars= UserWishList.query.filter_by(user_id=current_user.id).all()
    highest_score = 0
    for car in wish_list_cars:
        print(car.car.brand.name)
        print(car.score_result)

    highest_score = max((car.score_result for car in wish_list_cars), default=0)        

    return render_template('wish-list.html', wish_list_cars=wish_list_cars, highest_score=highest_score, user=current_user)








@views.route('/car1', methods=['GET', 'POST'])
@login_required
def car1_toCompare():
    if request.method == 'POST':
        car_id = request.form.get('car_id')

        if car_id:
            user_request = Comparisons.query.filter_by(user_id=current_user.id).first()
            if user_request:
                user_request.first_car_id = int(car_id)
            else:
                user_request = Comparisons(
                    first_car_id=int(car_id),
                    user_id=current_user.id
                )

                db.session.add(user_request)

            db.session.commit()         
            return redirect(url_for('views.car2_toCompare'))  
    
    brands = CarBrand.query.all()
    cars = Car.query.all()
    return render_template("car1_toCompare.html", cars=cars, brands=brands, user=current_user)





@views.route('/car2', methods=['GET', 'POST'])
@login_required
def car2_toCompare():
    user_request = Comparisons.query.filter_by(user_id=current_user.id).first()
    if not user_request.first_car_id:
        flash('You did not choose your first car to compare', category='error')
        return redirect(url_for('views.car1'))
    

    if request.method == 'POST':
        car_id = request.form.get('car_id')
        if int(car_id) == user_request.first_car_id:
            flash('The selected cars must be dirrefent, please choosse again', category='error')
            return redirect(url_for('views.car2_toCompare'))
        
        if car_id:
            print(car_id)
            user_request.second_car_id = int(car_id)
            db.session.commit()         
            return redirect(url_for('views.comperations'))
          
    cars = Car.query.all()
    brands = CarBrand.query.all()
    return render_template("car2_toCompare.html", cars=cars, brands=brands, user=current_user)   







@views.route('/comperations', methods=['GET', 'POST'])
@login_required
def comperations():
    user_request = Comparisons.query.filter_by(user_id=current_user.id).first()

    if user_request:
        first_car_id = user_request.first_car_id
        second_car_id = user_request.second_car_id
        if not first_car_id or not second_car_id:
            flash('You must choose the cars to compare before getting this page', category='error')
            return redirect(url_for('views.car1_toCompare'))

        if first_car_id and second_car_id:
            car1 = Car.query.filter_by(id=first_car_id).first()
            car2 = Car.query.filter_by(id=second_car_id).first()

            real_time_car_data1 = json.loads(car1.car_data_list_info)
            final_real_range_data_car1 = json.loads(car1.car_data_final_range)

            real_time_car_data2 = json.loads(car2.car_data_list_info)
            final_real_range_data_car2 = json.loads(car2.car_data_final_range)
            # real_time_car_data1, final_real_range_data_car1 = car_pages.createData(car1)
            # real_time_car_data2, final_real_range_data_car2 = car_pages.createData(car2)

            # Convert lists of tuples to lists of labels and values
            real_time_car_data1_list = list(real_time_car_data1)
            real_time_car_data2_list = list(real_time_car_data2)

  
            comparison_data = []
            car1_pros_score = 0
            car2_pros_score = 0

            all_labels = []                  
            for label, _ in real_time_car_data1_list:
                    all_labels.append(label)

            for label, _ in real_time_car_data2_list:
                if label not in all_labels:
                    all_labels.append(label)


            for label in all_labels:
                # return using the iterator the next value according to the label
                value1 = next((value for lbl, value in real_time_car_data1_list if lbl == label), 'N/A')
                value2 = next((value for lbl, value in real_time_car_data2_list if lbl == label), 'N/A')
      
                highlight1 = ''
                highlight2 = ''


                def get_numeric_value(value):
                    try:
                        return float(re.sub(r'[^\d.]+', '', value))
                    except ValueError:
                        return None

                num1 = get_numeric_value(value1)
                num2 = get_numeric_value(value2)

                if value1.lower() == 'yes' and value2.lower() == 'no':
                    highlight1 = 'highlight-better'
                    highlight2 = 'highlight-difference'
                    car1_pros_score += 1
                elif value1.lower() == 'no' and value2.lower() == 'yes':  
                    highlight1 = 'highlight-difference'
                    highlight2 = 'highlight-better'
                    car2_pros_score += 1  

                if label.lower() in ['acceleration 0 - 100 km/h', 'weight unladen (eu)', 'gross vehicle weight (gvwr)', 'germany', 'united kingdom', 'the netherlands', 'vehicle consumption *',
                                     'rated consumption', 'vehicle consumption', 'rated fuel equivalent', 'vehicle fuel equivalent', 'weight unladen (eu)', 'gross vehicle weight (gvwr)', 'turning circle']:
                    if num1 is not None and num2 is not None:
                        if num1 < num2:
                            highlight1 = 'highlight-better'
                            highlight2 = 'highlight-difference'
                            car1_pros_score += 1
                        elif num1 > num2:
                            highlight1 = 'highlight-difference'
                            highlight2 = 'highlight-better'
                            car2_pros_score += 1       
                else:
                    if num1 is not None and num2 is not None:
                        if num1 > num2:
                            highlight1 = 'highlight-better'
                            highlight2 = 'highlight-difference'
                            car1_pros_score += 1
                        elif num1 < num2:
                            highlight1 = 'highlight-difference'
                            highlight2 = 'highlight-better'
                            car2_pros_score += 1

                comparison_data.append({
                    'label': label,
                    'value1': value1,
                    'value2': value2,
                    'highlight1': highlight1,
                    'highlight2': highlight2
                })

            return render_template(
                'comperations.html',
                real_time_car_data1=real_time_car_data1_list,
                final_real_range_data_car1=final_real_range_data_car1,
                real_time_car_data2=real_time_car_data2_list,
                final_real_range_data_car2=final_real_range_data_car2,
                car1=car1, 
                car2=car2,
                user=current_user,
                comparison_data=comparison_data,
                car1_pros_score=car1_pros_score,
                car2_pros_score=car2_pros_score
            )
    flash('Problem with your request', category='error')
    return redirect(url_for('views.home'))












# @views.route('/comperations', methods=['GET', 'POST'])
# @login_required
# def comperations():
#     user_request = Comparisons.query.filter_by(user_id=current_user.id).first()

#     if user_request:
#         first_car_id = user_request.first_car_id
#         second_car_id = user_request.second_car_id
#         if not first_car_id or not second_car_id:
#             flash('You must choose the cars to compare before getting this page', category='error')
#             return redirect(url_for('views.car1_toCompare'))

#         if first_car_id and second_car_id:
#             car1 = Car.query.filter_by(id=first_car_id).first()
#             car2 = Car.query.filter_by(id=second_car_id).first()

#             real_time_car_data1 = json.loads(car1.car_data_list_info)
#             final_real_range_data_car1 = json.loads(car1.car_data_final_range)

#             real_time_car_data2 = json.loads(car2.car_data_list_info)
#             final_real_range_data_car2 = json.loads(car2.car_data_final_range)
#             # real_time_car_data1, final_real_range_data_car1 = car_pages.createData(car1)
#             # real_time_car_data2, final_real_range_data_car2 = car_pages.createData(car2)

#             # Convert lists of tuples to lists of labels and values
#             real_time_car_data1_list = list(real_time_car_data1)
#             real_time_car_data2_list = list(real_time_car_data2)

  
#             comparison_data = []
#             car1_pros_score = 0
#             car2_pros_score = 0
#             all_labels = [] 

#             len_car1 = len(real_time_car_data1)
#             len_car2 = len(real_time_car_data2)
            
#             if len_car1 <= len_car2:
#                 for label, _ in real_time_car_data2:
#                     all_labels.append(label)
#             else:
#                 for label, _ in real_time_car_data1:
#                     all_labels.append(label)     
            

#             iterator1 = iter(real_time_car_data1)
#             iterator2 = iter(real_time_car_data2)

#             for label in all_labels:
                               
#                 value1 = next((item[1] for item in iterator1), 'N/A')
#                 value2 = next((item[1] for item in iterator2), 'N/A')

                
#                 highlight1 = ''
#                 highlight2 = ''


#                 def get_numeric_value(value):
#                     try:
#                         return float(re.sub(r'[^\d.]+', '', value))
#                     except ValueError:
#                         return None

#                 num1 = get_numeric_value(value1)
#                 num2 = get_numeric_value(value2)

#                 if value1.lower() == 'yes' and value2.lower() == 'no':
#                     highlight1 = 'highlight-better'
#                     highlight2 = 'highlight-difference'
#                     car1_pros_score += 1
#                 elif value1.lower() == 'no' and value2.lower() == 'yes':  
#                     highlight1 = 'highlight-difference'
#                     highlight2 = 'highlight-better'
#                     car2_pros_score += 1  

#                 if label.lower() in ['acceleration 0 - 100 km/h', 'weight unladen (eu)', 'gross vehicle weight (gvwr)', 'germany', 'united kingdom', 'the netherlands', 'vehicle consumption *',
#                                      'rated consumption', 'vehicle consumption', 'rated fuel equivalent', 'vehicle fuel equivalent', 'weight unladen (eu)', 'gross vehicle weight (gvwr)', 'turning circle']:
#                     if num1 is not None and num2 is not None:
#                         if num1 < num2:
#                             highlight1 = 'highlight-better'
#                             highlight2 = 'highlight-difference'
#                             car1_pros_score += 1
#                         elif num1 > num2:
#                             highlight1 = 'highlight-difference'
#                             highlight2 = 'highlight-better'
#                             car2_pros_score += 1       
#                 else:
#                     if num1 is not None and num2 is not None:
#                         if num1 > num2:
#                             highlight1 = 'highlight-better'
#                             highlight2 = 'highlight-difference'
#                             car1_pros_score += 1
#                         elif num1 < num2:
#                             highlight1 = 'highlight-difference'
#                             highlight2 = 'highlight-better'
#                             car2_pros_score += 1

#                 comparison_data.append({
#                     'label': label,
#                     'value1': value1,
#                     'value2': value2,
#                     'highlight1': highlight1,
#                     'highlight2': highlight2
#                 })

#             return render_template(
#                 'comperations.html',
#                 real_time_car_data1=real_time_car_data1_list,
#                 final_real_range_data_car1=final_real_range_data_car1,
#                 real_time_car_data2=real_time_car_data2_list,
#                 final_real_range_data_car2=final_real_range_data_car2,
#                 car1=car1, 
#                 car2=car2,
#                 user=current_user,
#                 comparison_data=comparison_data,
#                 car1_pros_score=car1_pros_score,
#                 car2_pros_score=car2_pros_score
#             )
#     flash('Problem with your request', category='error')
#     return redirect(url_for('views.home'))






