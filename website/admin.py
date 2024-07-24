from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import User, Car, CarBrand
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import json


admin = Blueprint('admin', __name__)

@admin.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():
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
    cars = Car.query.all()
    return render_template('car-list.html', cars=cars, user=current_user)



@admin.route('/add-car', methods=['GET', 'POST'])      
@login_required  
def add_car():
    if request.method == 'POST':
        car_brand_name = request.form.get('car_brand')
        car_model = request.form.get('car_model')
        car_range = request.form.get('range')
        fast_charging_time = request.form.get('fast_chargingTime')

        car_brand = CarBrand.query.filter_by(name=car_brand_name).first()
        print(car_brand_name)
        if not car_brand:
            flash('Invalid car brand selected!', category='error')
            return redirect(url_for('admin.add_car'))

        
        new_car = Car(
            model=car_model,
            range=car_range,
            fast_chargingTime=fast_charging_time,
            brand_id=car_brand.id  
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
    car = Car.query.get_or_404(car_id)
    return render_template('edit-car.html', car=car, user=current_user)



@admin.route('/edit-car/<int:car_id>', methods=['POST'])
@login_required
def update_car(car_id):
    car = Car.query.get_or_404(car_id)
    car.model = request.form.get('car_model')
    car.range = request.form.get('range')
    car.fast_chargingTime = request.form.get('fast_chargingTime')

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




