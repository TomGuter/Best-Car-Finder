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

                            
    
    return score*10    




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
                if label not in all_labels:
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

                if label.lower() in ['acceleration 0 - 100 km/h', 'weight unladen (eu)', 'gross vehicle weight (gvwr)']:
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
#         if not first_car_id and not second_car_id:
#             flash('You must choose the cars to compare before getting this page', category='error')
#             return redirect(url_for('views.car1_toCompare'))

#         if first_car_id and second_car_id:
#             car1 = Car.query.filter_by(id=first_car_id).first()
#             car2 = Car.query.filter_by(id=second_car_id).first()

#             real_time_car_data1, final_real_range_data_car1 = car_pages.createData(car1)
#             real_time_car_data2, final_real_range_data_car2 = car_pages.createData(car2)

#             real_time_car_data1_dict = OrderedDict(real_time_car_data1)
#             real_time_car_data2_dict = OrderedDict(real_time_car_data2)

#             # for key, value in real_time_car_data1:
#             #     real_time_car_data1_dict[key].append(value)

#             # for key, value in real_time_car_data2:
#             #     real_time_car_data2_dict[key].append(value)

#             # real_time_car_data1_dict = {k: v for k, v in real_time_car_data1}
#             # real_time_car_data2_dict = {k: v for k, v in real_time_car_data2}

#             for key, value in real_time_car_data1_dict.items():
#                 print(f'{key}, {value}')

#             print('----------------')
#             for label, value in real_time_car_data1:
#                 print(f'{label}: {value}')

#             comparison_data = []
#             car1_pros_score = 0
#             car2_pros_score = 0
#             all_labels = set(real_time_car_data1_dict.keys()).union(real_time_car_data2_dict.keys())
#             for label in all_labels:
#                 value1 = real_time_car_data1_dict.get(label, 'N/A')
#                 value2 = real_time_car_data2_dict.get(label, 'N/A')
#                 highlight1 = ''
#                 highlight2 = ''

#                 if label.lower() == 'acceleration 0 - 100 km/h' or label.lower() == 'weight unladen (eu)' or label.lower() == 'gross vehicle weight (gvwr)':
#                     try:
#                         num1 = float(re.sub(r'[^\d.]+', '', value1))
#                         num2 = float(re.sub(r'[^\d.]+', '', value2))
#                         if num1 < num2:  # smaller value is better for acceleration
#                             highlight1 = 'highlight-better'
#                             highlight2 = 'highlight-difference'
#                             car1_pros_score += 1
#                         elif num1 > num2:
#                             highlight1 = 'highlight-difference'
#                             highlight2 = 'highlight-better'
#                             car2_pros_score += 1
#                     except ValueError:
#                         pass
#                 else:
#                     try:
#                         num1 = float(re.sub(r'[^\d.]+', '', value1))
#                         num2 = float(re.sub(r'[^\d.]+', '', value2))
#                         if num1 > num2:  # larger value is better for other categories
#                             highlight1 = 'highlight-better'
#                             highlight2 = 'highlight-difference'
#                             car1_pros_score += 1
#                         elif num1 < num2:
#                             highlight1 = 'highlight-difference'
#                             highlight2 = 'highlight-better'
#                             car2_pros_score += 1
#                     except ValueError:
#                         pass

#                 comparison_data.append({
#                     'label': label,
#                     'value1': value1,
#                     'value2': value2,
#                     'highlight1': highlight1,
#                     'highlight2': highlight2
#                 })


#             return render_template(
#                 'comperations.html',
#                 real_time_car_data1=real_time_car_data1_dict,
#                 final_real_range_data_car1=final_real_range_data_car1,
#                 real_time_car_data2=real_time_car_data2_dict,
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




