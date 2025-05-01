from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.medical_record import MedicalRecord, Notification
from app.forms import UpdateProfileForm, MedicalRecordForm
from app import db, s
import os
from werkzeug.utils import secure_filename
import pandas as pd
import json
import plotly.express as px
from datetime import datetime

bp = Blueprint('patient', __name__)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        try:
            if form.avatar.data:
                file = form.avatar.data
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                    os.makedirs(current_app.config['UPLOAD_FOLDER'])
                file.save(file_path)
                current_user.avatar = filename
            
            current_user.full_name = form.full_name.data
            current_user.phone = form.phone.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('patient.profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
    
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone
        form.email.data = current_user.email
    
    return render_template('profile.html', form=form)