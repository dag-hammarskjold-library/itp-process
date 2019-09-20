from flask import Flask, render_template, request, abort, jsonify, Response, session,url_for,redirect,flash
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from requests import get
import boto3, re, os, pymongo
from mongoengine import connect,disconnect
from app.models import Itpp_log,Itpp_user, Itpp_section, Itpp_rule
from app.forms import LoginForm
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import DevelopmentConfig as Config
import time


###############################################################################################
# Create FLASK APPLICATION
###############################################################################################

# setting up the flask app

app = Flask(__name__)

# setting up the secret key and connect to the database

app.secret_key=b'a=pGw%4L1tB{aK6'
connect(host=Config.connect_string,db=Config.dbname)

login_manager = LoginManager()
login_manager.init_app(app)

####################################################
# BASIC ROUTINES AND ROUTES
####################################################  

@app.route("/")
def main():
    user = current_user
    if current_user:
        return render_template('main.html',myUser=user)
    else:
        return redirect(url_for('login'))

@app.route("/administration")
@login_required
def administration():
    return render_template('administration.html')

@login_manager.user_loader
def load_user(id):
    return Itpp_user.objects.get(id=id)

@app.route("/login", methods=['GET','POST'])
def login():
    """ Default route of the application (Login) """
    if current_user.is_authenticated:
        return redirect(url_for('main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Itpp_user.objects(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main'))
    return render_template('login.html', title='Sign In', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# bad url
@app.errorhandler(404) 
def not_found(error): 
    return render_template('error.html')

# bad url
@app.route("/apperror")
def appError():
    return render_template('general_error.html'), 404


####################################################
# USER MANAGEMENT ROUTES
####################################################  

@app.route("/users")
@login_required
def list_users():
    users = Itpp_user.objects
    return render_template('listeuser.html', users=users)

# Create a user
@app.route("/users/create", methods=['GET', 'POST'])
@login_required
def create_user():
    if request.method == 'POST':
        # Get, sanitize, and validate the data
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        created = datetime.now()

        user = Itpp_user(email=email, username=username, created=created)
        user.set_password(password)
        # This still allows submission of a blank user document. We need more validation.
        try:
            user.save(validate=True)
            flash("The user was created successfully.")
            return redirect(url_for('list_users'))
        except:
            flash("An error occurred trying to create the user. Please review the information and try again.")
            return redirect(url_for('create_user'))
    else:
        return render_template('createuser.html')

# Retrieve a user
@app.route("/users/<id>")
@login_required
def get_user_by_id(id):
    
    #return render_template('updateuser.html')
    return jsonify({"status":"Okay"})

# Update a user
@app.route("/users/<id>/update", methods=['GET','POST'])
@login_required
def update_user(id):
    try:
        user = Itpp_user.objects(id=id)[0]
    except IndexError:
        flash("The user was not found.")
        return redirect(url_for('list_users'))
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        user.email = email  #unsure if this is a good idea
        user.username = username
        user.updated = datetime.now()
        user.set_password(password)

        try:
            user.save(validate=True)
            flash("The user was updated successfully.")
            return redirect(url_for('list_users'))
        except:
            flash("An error occurred trying to create the user. Please review the information and try again.")
            return render_template('updateuser.html',user=user)
    else:
        return render_template('updateuser.html',user=user)

# Delete a user
@app.route("/users/<id>/delete")
@login_required
def delete_user(id):
    try:
        user = Itpp_user.objects(id=id)[0]
    except IndexError:
        flash("The user was not found.")
        return redirect(url_for('list_users'))
    try:
        user.delete()
        flash("User was successfully deleted.")
        return redirect(url_for('list_users'))
    except:
        flash("Ubable to delete user.")
        return redirect(url_for('list_users'))

# check of the user exists
@app.route("/checkUser", methods=['POST'])
@login_required
def checkUser():
    """ User check Identification """
    if (request.form["inputEmail"]=="admin@un.org" and request.form["inputPassword"]=="admin"):
        session["username"]="admin"
        session["email"]="admin@un.org"
        session["startSession"]=time.asctime( time.localtime(time.time()))
 
        return redirect(url_for('main'))


####################################################
# SECTIONS MANAGEMENT ROUTES
####################################################  

@app.route("/sections")
@login_required
def list_sections():
    sections = Itpp_section.objects
    return render_template('listeprocess.html', sections=sections)

@app.route("/sections/new", methods=['GET', 'POST'])
@login_required
def create_section():
    if request.method == 'POST':
        # Get, sanitize, and validate the data
        name = request.form.get('section_name')
        itp_body = request.form.get('body')
        itp_session = request.form.get('session')
        rules = request.form.get('rules')

        section = Itpp_section(name=name, itp_body=itp_body, itp_session=itp_session, rules=rules)
        try:
            section.save(validate=True)
            flash("The section was created successfully.")
            return redirect(url_for('list_sections'))
        except:
            flash("An error occurred trying to create the section. Please review the information and try again.")
            return redirect(url_for('create_section'))
    else:
        return render_template('createprocess.html')

@app.route("/sections/<id>")
@login_required
def get_section_by_id(id):
    # To do
    return jsonify({"status":"Okay"})

@app.route("/sections/<id>/update")
@login_required
def update_section(id):
    try:
        section = Itpp_section.objects(id=id)[0]
    except IndexError:
        flash("The section was not found.")
        return redirect(url_for('list_sections'))
    if request.method == 'POST':
        name = request.form.get('section_name')
        itp_body = request.form.get('itp_body')
        itp_session = request.form.get('itp_session')
        rules = request.form.get('rules')

        section.name = name
        section.itp_body = body
        section.itp_session = itp_session
        section.rules = rules

        try:
            section.save(validate=True)
            flash("The section was updated successfully.")
            return redirect(url_for('list_sections'))
        except:
            flash("An error occurred trying to create the section. Please review the information and try again.")
            return render_template('updateprocess.html',section=section)
    else:
        return render_template('updatprocess.html',section=section)

@app.route("/sections/<id>/delete")
@login_required
def delete_section(id):
    return jsonify({"status":"Okay"})

####################################################
# Rules Management
####################################################

@app.route("/rules", methods=['GET'])
@login_required
def list_rules():
    return jsonify({"status":"Okay"})

@app.route("/rules/new", methods=['GET', 'POST'])
@login_required
def create_rule():
    return jsonify({"status":"Okay"})

@app.route("/rules/<id>", methods=['GET'])
@login_required
def get_rule_by_id(id):
    return jsonify({"status":"Okay"})

@app.route("/rules/<id>/update")
@login_required
def update_rule(id):
    return jsonify({"status":"Okay"})

@app.route("/rules/<id>/delete")
@login_required
def delete_rule(id):
    return jsonify({"status":"Okay"})

####################################################
# Reports Management
####################################################

@app.route("/reports", methods=['GET'])
@login_required
def list_reports():
    return jsonify({"status":"Okay"})

#@app.route("/report/new", methods=['GET', 'POST'])
#def create_rule():
#    return jsonify({"status":"Okay"})

@app.route("/reports/<id>", methods=['GET'])
@login_required
def get_report_by_id(id):
    return jsonify({"status":"Okay"})

#@app.route("/rules/<id>/update")
#def update_rule(id):
#    return jsonify({"status":"Okay"})

#@app.route("/rules/<id>/delete")
#def delete_rule(id):
#    return jsonify({"status":"Okay"})

####################################################
# START APPLICATION
####################################################  

if __name__=="__main__":
    app.run(debug=True)