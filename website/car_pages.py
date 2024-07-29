from cmath import sqrt
import re
from flask import Blueprint, redirect, render_template, request, flash, jsonify, url_for, session
from flask_login import login_required, current_user
from .models import Note, Car, CarBrand, CurrentUserPreferences, UserWishList
from . import db
from bs4 import BeautifulSoup
import requests


car_pages = Blueprint('car_pages', __name__)



# @car_pages.route('/ionic-5', methods=['GET', 'POST'])
# @login_required
# def ionic_5():
#     url = "https://ev-database.org/car/1662/Hyundai-IONIQ-5-Long-Range-2WD"

#     real_time_car_data = []
#     final_real_range_data = []
#     # REQUEST WEBPAGE AND STORE IT AS A VARIABLE
#     page_to_scrape = requests.get(url)

#     # USE BEAUTIFULSOUP TO PARSE THE HTML AND STORE IT AS A VARIABLE
#     soup = BeautifulSoup(page_to_scrape.text, 'html.parser')


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
#                     final_real_range_data.append(('Ev-Database', digits_only))

                   


#     for label, value in final_real_range_data:
#         print(f"{label}: {value}")

#     for label, value in real_time_car_data:
#         print(f"{label}: {value}")



#     return render_template('Ionic-5.html', real_time_car_data=real_time_car_data, final_real_range_data=final_real_range_data, user=current_user)




@car_pages.route('/car-data/<model_name>/<brand_name>', methods=['GET', 'POST'])
@login_required
def car_data(model_name, brand_name):
    url = request.args.get('url')
    if not url:
        return "URL provided is wrong", 400
    #url = requests.get(url)
    print(url)
    #url = "https://ev-database.org/car/1662/Hyundai-IONIQ-5-Long-Range-2WD"
    # Construct the URL based on the model and brand names

    # REQUEST WEBPAGE AND STORE IT AS A VARIABLE
    page_to_scrape = requests.get(url)

    # USE BEAUTIFULSOUP TO PARSE THE HTML AND STORE IT AS A VARIABLE
    soup = BeautifulSoup(page_to_scrape.text, 'html.parser')

    real_time_car_data = []
    final_real_range_data = []
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 2:
                label = cols[0].text.strip()
                value = cols[1].text.strip()

                real_time_car_data.append((label, value)) 
                if 'electric range' in label.lower():
                    digits_only = re.sub(r'\D', '', value)            
                    final_real_range_data.append((f'{brand_name} - {model_name}', digits_only))


    template_name = f"{model_name}.html"

    # Print data for debugging (optional)
    # for label, value in final_real_range_data:
    #     print(f"{label}: {value}")

    # for label, value in real_time_car_data:
    #     print(f"{label}: {value}")
     

    return render_template(template_name, real_time_car_data=real_time_car_data, final_real_range_data=final_real_range_data, user=current_user)