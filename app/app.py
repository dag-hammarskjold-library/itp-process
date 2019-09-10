from flask import Flask, render_template, request, abort, jsonify, Response, session,url_for,redirect,flash
from functools import wraps
from requests import get
import boto3, re, time, os, pymongo
from mongoengine import connect, Document, StringField
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import DevelopmentConfig as Config

###############################################################################################
# Create FLASK APPLICATION
###############################################################################################

app = Flask(__name__)

# generation secret key
app.secret_key=b'a=pGw%4L1tB{aK6'
db = connect(host=Config.connect_string)

####################################################
# BASIC ROUTINES AND ROUTES
####################################################  

def calcRecord(Rs):
    """ JUST RETURN THE NUMBER OF RECORSET OF ONE RECORDSET PASSED AS PARAMETER """
    recup=0
    return recup

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You are not authorized to view this resource. Please login first.")
            return redirect(url_for('login'))
    return wrap
# Deprecating this route, should just use / instead
#@app.route("/main")
#def main():
#    """ Default route of the application (Login) """
#    myUser=session["username"]
#    return render_template('main.html',myUser=myUser)

@app.route("/administration")
@login_required
def administration():
    try:
        if "username" in session:
            total=0
            myRecord=total
            return render_template('administration.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

@app.route("/")
@app.route("/login")
def login():
    """ Default route of the application (Login) """
    return render_template('login.html')

@app.route("/logout")
def logout():
    """ In order to manage the logout of the application """ 
    try:
        session.pop("username",None)
        session.pop("email",None)
        return render_template('login.html')
    except:
        return redirect(url_for('appError'))


# bad url
@app.errorhandler(404) 
def not_found(error): 
    """ In order to manage the 404 error """ 
    flash('The page requested is not available in this App  !!! ','error')
    return render_template('error.html'), 404

# bad url
@app.route("/apperror")
def appError():
    """ In order to manage the unexpected error """ 
    flash('Something happened in the system !!! ','error')
    return render_template('general_error.html'), 404


####################################################
# USER MANAGEMENT ROUTES
####################################################  

# Rename to /users for RESTfulness
@app.route("/listeuser")
def listeUser():
    """ List of User """
    try:
        if "username" in session:
            total=0
            myRecord=total
            return render_template('listeuser.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

# Rename to /users/new
@app.route("/createuser", methods=['GET', 'POST'])
def createUser():
    """ User creation """
    try:
        if "username" in session:
            if request.method == 'POST':
                flash('New User Saved in the database !!! ', 'message')
                return redirect(url_for('listeUser'))
            if request.method == 'GET':
                return render_template('user.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

# Rename /users/<id>/edit
@app.route("/updateuser", methods=['POST'])
def updateUser():
    """ User update """
    try:
        if "username" in session:
            return redirect(url_for('listeUser'))
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))


# Rename to /users/<id>
@app.route("/displayuser/<email>", methods=['GET'])
def displayUser(email):
    """ Display one User record """
    try:    
        if "username" in session:
            if request.method == 'GET':
                session["email"]=email
                myUser=Itpp_User.query.filter(Itpp_User.email==email).first()
                return render_template('updateuser.html',myUser=myUser)
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

#delete the user
@app.route("/delete/<email>", methods=['GET'])
def deleteUser(email):
    """ User deletion """
    try:      
        if "username" in session:
            if request.method == 'GET':
                myUserToDelete=Itpp_User.query.filter(Itpp_User.email==email).first()
                flash('User deleted !!! ', 'message')
                return redirect(url_for('listeUser'))
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

# check of the user exists
@app.route("/checkUser", methods=['POST'])
def checkUser():
    """ User check Identification """
    # Remove this section, as it is insecure.
    try: 
        # Tip for admin
        if (request.form["inputEmail"]=="admin@un.org" and request.form["inputPassword"]=="admin"):
            session["username"]="admin"
            session["email"]="admin@un.org"
            return redirect(url_for('main'))

        # Normal way
        
        myResult=Itpp_User.query.filter(Itpp_User.email==request.form["inputEmail"],Itpp_User.password==request.form["inputPassword"]).first()
        if myResult:
            session["username"]=myResult.username
            return redirect(url_for('main'))
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

####################################################
# Section management routes
####################################################

@app.route('/sections')
def list_sections():
    pass

@app.route('/sections/<id>', methods=['GET', 'POST', 'PATCH','DELETE'])
def get_section_by_id(id):
    pass

@app.route('/sections/new')
@login_required
def create_section():
    pass

####################################################
# RULE MANAGEMENT ROUTES
####################################################  


# Rename to /rules/new for RESTfulness
# GET returns form
# POST attempts to create the rule from the form contents
@app.route("/createrule", methods=['GET', 'POST'])
def createRule():
    """ Rule creation """
    try:
        if "username" in session:
            if request.method == 'POST':
                flash('New Rule Saved in the database !!! ', 'message')
                return redirect(url_for('listeRule'))
            if request.method == 'GET':
                return render_template('createrule.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

# Remove this route
# special one
@app.route("/createrule01", methods=['GET', 'POST'])
def createRule01():
    return render_template('createrule01.html')

# Rename to /rules
@app.route("/listerule")
def listeRule():
    """ List of Rule """
    try:
        if "username" in session:
            total=0
            myRecord=total
            return render_template('listerule.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

# Add routes:
# /rules/<id>, GET
# /rules/<id>/edit, GET and either POST or PATCH
# /rules/<id>/delete, POST


####################################################
# PROCESS MANAGEMENT ROUTES
####################################################  

# Rename /processes
@app.route("/listeprocess")
def listeProcess():
    """ List of Process """
    try:
        if "username" in session:
            total=0
            myRecord=total
            return render_template('listeprocess.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))


# Rename /processes/new
@app.route("/createprocess", methods=['GET', 'POST'])
def createProcess():
    """ Process creation """
    if "username" in session:
        if request.method == 'POST':
            flash('New Process Saved in the database !!! ', 'message')
            return redirect(url_for('listeProcess'))
        if request.method == 'GET':
            return render_template('createprocess.html')
    else:
        flash('Unknown user !!! ','error')
        return render_template('login.html')

# Others
# /processes/<id>
# /processes/<id>/edit
# /processes/<id>/delete

####################################################
# START APPLICATION
####################################################  

if __name__=="__main__":
    app.run(debug=True)