from flask import Flask, render_template, request, abort, jsonify, Response, session,url_for,redirect,flash
from requests import get
import boto3, re, os, pymongo
from mongoengine import connect,disconnect
from app.models import Itpp_log,Itpp_user
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

####################################################
# BASIC ROUTINES AND ROUTES
####################################################  

@app.route("/")
def main():
    """ Default route of the application (Login) """
    myUser=session["username"]
    myTime=session["startSession"]
    return render_template('main.html',myUser=myUser,myTime=myTime)

@app.route("/administration")
def administration():
    return render_template('administration.html')

@app.route("/login")
def login():
    """ Default route of the application (Login) """
    return render_template('login.html')

@app.route("/logout")
def logout():
    return render_template('login.html')

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
def list_users():
    users = Itpp_user.objects
    return render_template('listeuser.html', users=users)

# Create a user
@app.route("/users/create", methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        # Get, sanitize, and validate the data
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        created = datetime.now()

        user = Itpp_user(email=email, username=username, password=password, created=created)
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
def get_user_by_id(id):
    
    #return render_template('updateuser.html')
    return jsonify({"status":"Okay"})

# Update a user
@app.route("/users/<id>/update", methods=['GET','POST'])
def update_user(id):
    try:
        user = Itpp_user.objects(email=id)[0]
    except IndexError:
        flash("The user was not found.")
        return redirect(url_for('list_users'))
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        user.email = email  #unsure if this is a good idea
        user.username = username
        user.password = password
        user.updated = datetime.now()

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
def delete_user(id):
    try:
        user = Itpp_user.objects(email=id)[0]
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

@app.route("/sections", methods=['GET'])
def list_sections():
    return render_template('listeprocess.html')

@app.route("/sections/new", methods=['GET', 'POST'])
def create_section():
    return render_template('createprocess.html')

@app.route("/sections/<id>", methods=['GET'])
def get_section_by_id(id):
    return jsonify({"status":"Okay"})

@app.route("/sections/<id>/update")
def update_section(id):
    return jsonify({"status":"Okay"})

@app.route("/sections/<id>/delete")
def delete_section(id):
    return jsonify({"status":"Okay"})

####################################################
# Rules Management
####################################################

@app.route("/rules", methods=['GET'])
def list_rules():
    return jsonify({"status":"Okay"})

@app.route("/rules/new", methods=['GET', 'POST'])
def create_rule():
    return jsonify({"status":"Okay"})

@app.route("/rules/<id>", methods=['GET'])
def get_rule_by_id(id):
    return jsonify({"status":"Okay"})

@app.route("/rules/<id>/update")
def update_rule(id):
    return jsonify({"status":"Okay"})

@app.route("/rules/<id>/delete")
def delete_rule(id):
    return jsonify({"status":"Okay"})

####################################################
# Reports Management
####################################################

@app.route("/reports", methods=['GET'])
def list_reports():
    return jsonify({"status":"Okay"})

#@app.route("/report/new", methods=['GET', 'POST'])
#def create_rule():
#    return jsonify({"status":"Okay"})

@app.route("/reports/<id>", methods=['GET'])
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