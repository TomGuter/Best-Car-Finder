import base64
from datetime import datetime
import io
from turtle import pd
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from sqlalchemy import func
from .models import CurrentUserPreferences, User, Car, CarBrand
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import json
from werkzeug.utils import secure_filename
import os
import plotly.graph_objects as go
import pandas as pd


admin = Blueprint('admin', __name__)

@admin.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():
    if current_user.first_name != 'Admin' and current_user.email != 'admin@gmail.com':
        flash('You do not have the permission necessary to access this page', category='error')
        return redirect(url_for('views.home'))

    users = User.query.all()
    return render_template('admin.html', user=current_user, users=users)




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
    return render_template('car-list.html', cars=cars, user=current_user)


@admin.route('/user-control', methods=['GET', 'POST'])
@login_required
def user_control():
    users = User.query.all()
    return render_template('user-control.html', users=users, user=current_user)



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
        screen_size = int(request.form.get('screen_size'))
        img = request.form.get('car_image')
        acceleration = float(request.form.get('acceleration'))
        year = float(request.form.get('year'))
        car_brand = CarBrand.query.filter_by(name=car_brand_name).first()
        print(year)
        print(car_brand_name)
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
            year=year
        )

        db.session.add(new_car)
        db.session.commit()
        flash('Car added successfully!', 'success')

        print(car_brand_name, car_model, car_range, fast_charging_time)
    
    car_brands = CarBrand.query.all()
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

    segments = request.form.getlist('segment')
    if segments:
        car.segments = segments
    else:
        car.segments = []   
    # car.car_segment = segments if segments else []
 
    # segments = request.form.getlist('car_segment')
    # car.segment = segments
    # print()
    
    db.session.commit()
    flash('Car details updated successfully', category='success')
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

    months_prefs = [r.month for r in results_prefs]
    counts_prefs = [r.total_count for r in results_prefs]

    months_prefs = [datetime.strptime(m, '%Y-%m') for m in months_prefs]

    df_prefs = pd.DataFrame({
        'Month': months_prefs,
        'Count': counts_prefs
    })

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
        hovertemplate='Month: %{x|%b %Y}<br>Total Count: %{y}<extra></extra>',
        width=0.1
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

    months_users = [r.month for r in results_users]
    counts_users = [r.total_count for r in results_users]

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
        hovertemplate='Month: %{x|%b %Y}<br>Total Sign-Ups: %{y}<extra></extra>',
        width=0.1
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