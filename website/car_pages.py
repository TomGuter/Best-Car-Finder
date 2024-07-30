from cmath import sqrt
import json
import re
from flask import Blueprint, redirect, render_template, request, flash, jsonify, url_for, session
from flask_login import login_required, current_user
from .models import Note, Car, CarBrand, CurrentUserPreferences, UserWishList
from . import db
from bs4 import BeautifulSoup
import requests


car_pages = Blueprint('car_pages', __name__)





@car_pages.route('/car-data/<model_name>/<brand_name>', methods=['GET', 'POST'])
@login_required
def car_data(model_name, brand_name):
    
    car = Car.query.filter_by(model=model_name).filter(Car.brand.has(name=brand_name)).first()
    real_time_car_data = json.loads(car.car_data_list_info)
    final_real_range_data = json.loads(car.car_data_final_range)

    template_name = f"{model_name}.html"
    
    if len(real_time_car_data) == 0:
        flash('URL provided is wrong', category='error')
        return redirect(url_for('views.home'))
        
    for item in final_real_range_data:
        if isinstance(item, list) and len(item) == 2:
            label, value = item
            print(f"{label}: {value}")

    return render_template(template_name, real_time_car_data=real_time_car_data, final_real_range_data=final_real_range_data, car=car, user=current_user)









# @car_pages.route('/car-data/<model_name>/<brand_name>', methods=['GET', 'POST'])
# @login_required
# def car_data(model_name, brand_name):
#     url = request.args.get('url')
#     if not url:
#         return "URL provided is wrong", 400

#     # REQUEST WEBPAGE AND STORE IT AS A VARIABLE
#     page_to_scrape = requests.get(url)

#     # USE BEAUTIFULSOUP TO PARSE THE HTML AND STORE IT AS A VARIABLE
#     soup = BeautifulSoup(page_to_scrape.text, 'html.parser')

#     real_time_car_data = []
#     final_real_range_data = []
#     tables = soup.find_all('table')
#     for table in tables:
#         rows = table.find_all('tr')
#         for row in rows:
#             cols = row.find_all('td')
#             if len(cols) == 2:
#                 label = cols[0].text.strip()
#                 value = cols[1].text.strip()

#                 real_time_car_data.append((label, value)) 
#                 if 'electric range' in label.lower():
#                     digits_only = re.sub(r'\D', '', value)            
#                     final_real_range_data.append((f'{brand_name} - {model_name}', digits_only))


#     template_name = f"{model_name}.html"

#     if len(real_time_car_data) == 0:
#         flash('URL provided is wrong', category='error')
#         return redirect(url_for('views.home'))
        

#     # Print data for debugging (optional)
#     # for label, value in final_real_range_data:
#     #     print(f"{label}: {value}")

#     # for label, value in real_time_car_data:
#     #     print(f"{label}: {value}")
     
#     car = Car.query.filter_by(model=model_name).filter(Car.brand.has(name=brand_name)).first()

#     return render_template(template_name, real_time_car_data=real_time_car_data, final_real_range_data=final_real_range_data, car=car, user=current_user)









@car_pages.route('/car-data-comparison', methods=['GET', 'POST'])
@login_required
def createData(car):
    url = car.car_data_url
    if not url:
        return "URL provided is wrong", 400
    
    if car.car_data_list_info and car.car_data_final_range:
        final_real_range_data = json.loads(car.car_data_list_info)
        real_time_car_data = json.loads(car.car_data_list_info)
        return (real_time_car_data, final_real_range_data)
        

    # REQUEST WEBPAGE AND STORE IT AS A VARIABLE
    page_to_scrape = requests.get(url)

    # USE BEAUTIFULSOUP TO PARSE THE HTML AND STORE IT AS A VARIABLE
    soup = BeautifulSoup(page_to_scrape.text, 'html.parser')

    car_data = []
    range_data = []
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 2:
                label = cols[0].text.strip()
                value = cols[1].text.strip()

                car_data.append((label, value)) 
                if 'electric range' in label.lower():
                    digits_only = re.sub(r'\D', '', value)            
                    range_data.append((f'{car.brand.name} - {car.model}', digits_only))



    if len(car_data) == 0:
        flash('URL provided is wrong', category='error')
        return redirect(url_for('views.home'))

    final_real_range_data = json.dumps(range_data)
    real_time_car_data = json.dumps(car_data)
    return (real_time_car_data, final_real_range_data)