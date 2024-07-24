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
    return render_template("preferences.html", user=current_user)




