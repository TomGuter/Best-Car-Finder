import ast
import base64
from datetime import datetime
import io
import re
from turtle import pd
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from sqlalchemy import asc, func

from website import car_pages
from .models import CurrentUserPreferences, User, Car, CarBrand
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import json
from werkzeug.utils import secure_filename
import os
import plotly.graph_objects as go
import pandas as pd
import google.generativeai as genai


admin = Blueprint('admin', __name__)

api_key = "add_your_secret_key"

@admin.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():
    if current_user.first_name != 'Admin' and current_user.email != 'admin@gmail.com':
        flash('You do not have the permission necessary to access this page', category='error')
        return redirect(url_for('views.home'))

    users = User.query.all()
    cars_num = Car.query.count()
    users_num = User.query.count()
    user_preferenes = CurrentUserPreferences.query.all()
    questionnaire_feature_used_num = 0
    for user_pref in user_preferenes:
        questionnaire_feature_used_num += user_pref.counter
    return render_template('admin.html', cars_num=cars_num, users_num=users_num, questionnaire_feature_used_num=questionnaire_feature_used_num, user=current_user, users=users)




@admin.route('/delete-user', methods=['POST'])
def deleteUser():
    data = request.get_json()
    user_id = data.get('userId') 
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted', category='success')

    return jsonify({})    


@admin.route('/car-list', methods=['GET', 'POST'])
@login_required
def carList():

    if current_user.first_name != 'Admin' and current_user.email != 'admin@gmail.com':
        flash('You do not have the permission necessary to access this page', category='error')
        return redirect(url_for('views.home'))

    cars = Car.query.all()
    brands = CarBrand.query.all()
    return render_template('car-list.html', cars=cars, brands=brands, user=current_user)


@admin.route('/user-control', methods=['GET', 'POST'])
@login_required
def user_control():
    users = User.query.all()
    return render_template('user-control.html', users=users, user=current_user)







def api_resposne(prompt):

    # api_key = os.environ.get("AIzaSyAR7KKq1WrQBIt00MVYsHe3FV6OA7XuyU8")
    print(api_key)
    if not api_key:
        flash('API key is not set in environment variables', category='error')
        return json.dumps({'error': 'API key is missing'})

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    response_text = response.text
    print("API Response:")
    print(response_text)
    return response_text




def get_car_details_from_ai(car_brand_name, car_model, year):
    
    prompt = f"""
    Please provide the following details for a car based on the given information. Each line must start with the line number, followed by the value in the format:
    `Line Number. Value`
    Let's start (if you don't know about the mentioned car model, give the information about the closest car model you know!)

    - Car Brand: {car_brand_name} 
    - Car Model: {car_model}
    - Year of Manufacture: {year}

    Fill in the details for the following fields:

    1. Range (km): (integer)
    2. Car Weight (kg): (integer)
    3. Horse Power (hp): (integer)
    4. Acceleration (0-100 km/h): (float)
    5. Fast Charging Time (minutes): (integer)
    6. Manufacturing Country (one country): (string)
    7. Car Segment (choose maximum two from the following options as they are written: A (Mini Cars), B (Small Cars), C (Medium Cars), D (Large Cars), Jeep, Sedan, SUV, Premium, Sport, Hatchback): (string)
    8. EURO NCAP Safety Rating (0 - 5 stars): (integer) 
    9. Multimedia Screen Size (in inches): (float)
    10. Entry price in Israel (price starts from for the current model, don't add additinal characters such as ',' because it should be an integer): (Integer)

    
    Ensure that each line begins with the correct line number followed by the value, as shown in the example.
    Please provide only the numerical values or strings for each field as specified.
    """

    # api_key = os.environ.get("AIzaSyAR7KKq1WrQBIt00MVYsHe3FV6OA7XuyU8")
    print(api_key)
    if not api_key:
        flash('API key is not set in environment variables', category='error')
        return redirect(url_for('views.home'))

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    response_text = response.text
    print("API Response:")
    print(response_text)
    return response_text



def parse_ai_response(ai_response_text):
    parsed_data = {}

    lines = ai_response_text.strip().split('\n')
    

    def extract_value(line):
        match = re.search(r'[.:]\s*(.*)', line)
        if match:
            return match.group(1).strip()
        return ''  

    def safe_convert(value, type_func, default_value):
        try:
            return type_func(value)
        except ValueError:
            return default_value


    for line in lines:
        value = extract_value(line)
        if line.startswith('1.'):
            parsed_data['range'] = safe_convert(value, int, 0)
        elif line.startswith('2.'):
            parsed_data['car_weight'] = safe_convert(value, int, 0)
        elif line.startswith('3.'):
            parsed_data['horse_power'] = safe_convert(value, int, 0)
        elif line.startswith('4.'):
            parsed_data['acceleration'] = safe_convert(value, float, 0.0)
        elif line.startswith('5.'):
            parsed_data['fast_charging_time'] = safe_convert(value, int, 0)
        elif line.startswith('6.'):
            parsed_data['manufacturing_country'] = value or 'Unknown'
        elif line.startswith('7.'):
            parsed_data['car_segment'] = value or 'Unknown'
        elif line.startswith('8.'):
            parsed_data['euro_ncap_rating'] = safe_convert(value, int, 0)
        elif line.startswith('9.'):
            parsed_data['screen_size'] = safe_convert(value, float, 0.0)
        elif line.startswith('10.'):
            parsed_data['price'] = safe_convert(value, int, 0)


    return parsed_data
       






@admin.route('/auto-fill-car-details', methods=['POST'])      
@login_required  
def auto_fill_car_details():

    data = request.json
    car_brand_name = data.get('car_brand')
    car_model = data.get('car_model')
    year = data.get('year')

    if not all([car_brand_name, car_model, year]):
        flash('Values are missing! You must fill Brand, Model and Year for using this feature', category='error')
        print('values in add car are missing')
        return jsonify([])
        # return redirect(url_for('views.home'))

    ai_data = get_car_details_from_ai(car_brand_name, car_model, year)
    if 'error' in ai_data:
        return jsonify(ai_data), 500

    parsed_data = parse_ai_response(ai_data)
    for key, value in parsed_data.items():
        print(f"{key}: {value}")
    return jsonify(parsed_data)







@admin.route('/add-car', methods=['GET', 'POST'])      
@login_required  
def add_car():

    if current_user.first_name != 'Admin' and current_user.email != 'admin@gmail.com':
        flash('You do not have the permission necessary to access this page', category='error')
        return redirect(url_for('views.home'))


    if request.method == 'POST':
        car_brand_name = request.form.get('car_brand')
        car_model = request.form.get('car_model')
        car_range = int(request.form.get('range'))
        weight = int(request.form.get('weight'))
        horse_power = int(request.form.get('horse_power'))
        fast_charging_time = int(request.form.get('fast_chargingTime'))
        usage = 'Null'
        manufacturing_country = request.form.get('manufacturing_country')
        segment = json.dumps(request.form.getlist('car_segment'))
        daily_commute = car_range*0.75
        # daily_commute = int(request.form.get('daily_commute'))
        price = int(request.form.get('price'))
        isSafety_rating = int(request.form.get('ncap_rating'))
        screen_size = float(request.form.get('screen_size'))
        car_data_url = request.form.get('car_data_url')
        img = request.form.get('car_image')
        acceleration = float(request.form.get('acceleration'))
        year = float(request.form.get('year'))
        car_brand = CarBrand.query.filter_by(name=car_brand_name).first()


        if not car_brand:
            flash('Invalid car brand selected!', category='error')
            return redirect(url_for('admin.add_car'))

        
        print(img)
        new_car = Car(
            model=car_model,
            range=car_range,
            horse_power=horse_power,
            fast_chargingTime=fast_charging_time,
            price=price,
            usage=usage,
            daily_commute=daily_commute,
            manufacturing_country=manufacturing_country,
            segment=segment,
            isSafety_rating = isSafety_rating,
            screen_size = screen_size,
            img=img,
            brand_id=car_brand.id,
            weight=weight,
            acceleration=acceleration,
            year=year,
            car_data_url=car_data_url,
            car_data_list_info=json.dumps([]),  
            car_data_final_range=json.dumps([])  
        )

        db.session.add(new_car)
        db.session.commit()
        flash('Car added successfully!', 'success')


        if new_car:
            print('ok')
            (car_data_list_info, car_data_final_range)  = car_pages.createData(new_car)
            if car_data_list_info and car_data_final_range:
                new_car.car_data_list_info = car_data_list_info
                new_car.car_data_final_range = car_data_final_range
                db.session.commit()


        car_model_filename = f"{car_model}.html"
        # car_model_filename = f"{car_model.replace(' ', '-')}.html"
        car_model_path = os.path.join(admin.root_path, 'cars', car_model_filename)

        with open(car_model_path, 'w') as file:
            file.write(
                f"""{{% extends "car_page_pattern.html" %}}
                {{% block title %}}{car_model}{{% endblock %}}
                {{% block content %}}
                {{% endblock %}}""")

        print(car_brand_name, car_model, car_range, fast_charging_time)
    
    car_brands = CarBrand.query.order_by(asc(CarBrand.name)).all()
    return render_template('add-car.html', car_brands=car_brands, user=current_user)






@admin.route('/update-car-brands', methods=['POST'])
def update_car_brands():
    return jsonify({})


@admin.route('/delete-car', methods=['POST'])
def delete_car():
    data = request.get_json()
    car_id = data.get('carId')
    car = Car.query.get(car_id)

    if car:
        db.session.delete(car)
        db.session.commit()

        car_model_filename = f"{car.model.replace(' ', '-')}.html"
        car_model_path = os.path.join(admin.root_path, 'cars', car_model_filename)

        if os.path.exists(car_model_path):
            os.remove(car_model_path)

        flash('Car deleted', category='success')
        return jsonify({'success': True}) 
    else:
        return jsonify({'success': False}), 404 
    

@admin.route('/edit-car/<int:car_id>', methods=['GET'])
@login_required
def edit_car(car_id):

    car_brands = CarBrand.query.all()
    car = Car.query.get_or_404(car_id)
    return render_template('edit-car.html', car=car, car_brands=car_brands, user=current_user)



@admin.route('/edit-car/<int:car_id>', methods=['POST'])
@login_required
def update_car(car_id):
    car = Car.query.get_or_404(car_id)

    old_page_name = car.model
    new_page_name = request.form.get('car_model')
    old_car_data_url = request.form.get('car_data_url')
    
    new_brand = request.form.get('car_brand')
    brand = CarBrand.query.filter_by(name=new_brand).first()
    car.brand_id = brand.id
 

    car.model = request.form.get('car_model')
    car.range = request.form.get('range')
    car.fast_chargingTime = request.form.get('fast_chargingTime')
    car.weight = request.form.get('weight')
    car.horse_power = request.form.get('horse_power')
    car.acceleration = request.form.get('acceleration')
    car.manufacturing_country = request.form.get('manufacturing_country')
    car.isSafety_rating = request.form.get('ncap_rating')
    car.screen_size = request.form.get('screen_size')
    car.img = request.form.get('car_image')
    car.price = request.form.get('price')
    car.year = request.form.get('year')
    car.car_data_url = request.form.get('car_data_url')

    segments = json.dumps(request.form.getlist('segment'))
    if segments:
        print('segment changed', segments)
        car.segment = segments
    else:
        car.segment = []   


    if old_car_data_url != car.car_data_url:
        print('ok')
        (car_data_list_info, car_data_final_range)  = car_pages.createData(car)
        if car_data_list_info and car_data_final_range:
            print('ok')
            car.car_data_list_info = car_data_list_info
            car.car_data_final_range = car_data_final_range
        else:
            car.car_data_list_info = []
            car.car_data_final_range = []

    
    db.session.commit()



    flash('Car details updated successfully', category='success')


    old_html_filename = f"{old_page_name}.html"
    new_html_filename = f"{new_page_name}.html"

    old_html_path = os.path.join(admin.root_path, 'cars', old_html_filename)
    new_html_path = os.path.join(admin.root_path, 'cars', new_html_filename)


    if os.path.exists(old_html_path):
        os.rename(old_html_path, new_html_path)
        
    return redirect(url_for('admin.carList'))





@admin.route('/addNewBrand', methods=['POST'])      
@login_required  
def addNewBrand():
    if request.method == 'POST':
        name = request.form.get('new_brand')
        if name:
            new_brand = CarBrand(name=name)
            db.session.add(new_brand)
            db.session.commit()
            flash('A new brand was added', category='success')
        else:
            flash('Brand name cannot be empty', category='error')

    return redirect(url_for('admin.add_car'))


@admin.route('/delete-brand', methods=['POST'])
@login_required
def delete_brand():
    data = request.get_json()
    brand_name = data.get('brandId')

    brand = CarBrand.query.filter_by(name=brand_name).first()

    print(brand_name)
    if brand:
        db.session.delete(brand)
        db.session.commit()
        flash('Car brand deleted', category='success')
        return jsonify({'success': True})
    else:
        print('ok')
        return jsonify({'success': False}), 404
    

@admin.route('/edit-brand', methods=['POST'])
@login_required
def edit_brand():
    data = request.get_json()
    brand_name = data.get('brandId')
    new_name = data.get('newName')
    print(new_name)
    print(brand_name)
    if not brand_name or not new_name:
        return jsonify({'success': False, 'message': 'Missing brand ID or new name'}), 400
    
    brand = CarBrand.query.filter_by(name=brand_name).first()

    if brand:
        print('ok')
        brand.name = new_name
        db.session.commit()
        flash('Car brand updated', category='success')
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Brand not found'}), 404





@admin.route('/statistics', methods=['GET', 'POST'])
@login_required
def create_statistics():

    if current_user.first_name != 'Admin' and current_user.email != 'admin@gmail.com':
        flash('You do not have the permission necessary to access this page', category='error')
        return redirect(url_for('views.home'))


    # Query for user preferences
    results_prefs = db.session.query(
        func.strftime('%Y-%m', CurrentUserPreferences.created_at).label('month'),
        func.sum(CurrentUserPreferences.counter).label('total_count')
    ).group_by('month').all()

    months_prefs = [res.month for res in results_prefs]
    counts_prefs = [res.total_count for res in results_prefs]

    months_prefs = [datetime.strptime(m, '%Y-%m') for m in months_prefs]

    print("Results from query:")
    for r in results_prefs:
        print(f"Month: {r.month}, Total Count: {r.total_count}")   


    df_prefs = pd.DataFrame({
        'Month': months_prefs,
        'Count': counts_prefs
    })

    print("DataFrame contents:")
    print(df_prefs)

    fig_prefs = go.Figure()
    fig_prefs.add_trace(go.Bar(
        x=df_prefs['Month'],
        y=df_prefs['Count'],
        name='Preferences',
        marker=dict(
            color=df_prefs['Count'],
            colorscale='Viridis',  
            colorbar=dict(
                title='Total Count'
            )
        ),
        hovertemplate='Month: %{x|%b %Y}<br>Total Count: %{y}<extra></extra>'
    ))

    fig_prefs.update_layout(
        title='Monthly Use Preferences Form Feature',
        title_x=0.5,
        title_font_size=20,
        xaxis_title='Month',
        yaxis_title='Total Count',
        xaxis=dict(
            tickformat='%b %Y',
            dtick='M1',
            tickmode='array',
            tickvals=df_prefs['Month'],
            ticktext=[date.strftime('%b %Y') for date in df_prefs['Month']],
            title_font_size=14
        ),
        yaxis=dict(
            title='Count',
            title_font_size=14,
            tickformat=',',
            rangemode='tozero'
        ),
        template='plotly_white',
        plot_bgcolor='rgba(255,255,255,0.1)',
        paper_bgcolor='rgba(255,255,255,0.1)',
        margin=dict(l=50, r=50, t=50, b=100),
        height=500
    )

    graph_html_prefs = fig_prefs.to_html(full_html=False, include_plotlyjs='cdn', div_id='statistics-graph-prefs')




    # Query for user sign-ups
    results_users = db.session.query(
        func.strftime('%Y-%m', User.created_at).label('month'),
        func.count(User.id).label('total_count')
    ).group_by('month').all()

    months_users = [res.month for res in results_users]
    counts_users = [res.total_count for res in results_users]

    months_users = [datetime.strptime(m, '%Y-%m') for m in months_users]

    df_users = pd.DataFrame({
        'Month': months_users,
        'Count': counts_users
    })

    fig_users = go.Figure()
    fig_users.add_trace(go.Bar(
        x=df_users['Month'],
        y=df_users['Count'],
        name='Sign-Ups',
        marker=dict(
            color=df_users['Count'],
            colorscale='Viridis',  
            colorbar=dict(
                title='Total Count'
            )
        ),
        hovertemplate='Month: %{x|%b %Y}<br>Total Sign-Ups: %{y}<extra></extra>'
    ))

    fig_users.update_layout(
        title='Monthly User Sign-Ups',
        title_x=0.5,
        title_font_size=20,
        xaxis_title='Month',
        yaxis_title='Total Sign-Ups',
        xaxis=dict(
            tickformat='%b %Y',
            dtick='M1',
            tickmode='array',
            tickvals=df_users['Month'],
            ticktext=[date.strftime('%b %Y') for date in df_users['Month']],
            title_font_size=14
        ),
        yaxis=dict(
            title='Count',
            title_font_size=14,
            tickformat=',',
            rangemode='tozero'
        ),
        template='plotly_white',
        plot_bgcolor='rgba(255,255,255,0.1)',
        paper_bgcolor='rgba(255,255,255,0.1)',
        margin=dict(l=50, r=50, t=50, b=100),
        height=500
    )

    graph_html_users = fig_users.to_html(full_html=False, include_plotlyjs='cdn', div_id='statistics-graph-users')

    return render_template('statistics.html', user=current_user, graph_html_prefs=graph_html_prefs, graph_html_users=graph_html_users)



@admin.route('/edit-user', methods=['POST'])
@login_required
def edit_user():
    data = request.get_json()
    user_id = data.get('userId')
    field = data.get('field')
    value = data.get('value')

    user = User.query.get_or_404(user_id)
    
    if field == 'first_name':
        user.first_name = value
    elif field == 'email':
        user.email = value
    elif field == 'password':
        user.set_password(value) 

    db.session.commit()

    flash('Successfully updated', category='success')
    return jsonify({'status': 'success'})
