from flask import Flask, render_template, request, abort, jsonify, Response, session,url_for,redirect,flash
from requests import get
import boto3, re, time, os, pymongo
#from flask import Flask
#from flask_mongoalchemy import MongoAlchemy
#from flask_admin import Admin
#from flask_admin.contrib.sqla import ModelView
#from flask_login import UserMixin
#from bson.objectid import ObjectId
from mongoengine import connect, Document, StringField
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import DevelopmentConfig as Config

###############################################################################################
# Create FLASK APPLICATION
###############################################################################################

app = Flask(__name__)

#app.config['MONGOALCHEMY_CONNECTION_STRING'] = Config.DB
#app.config['MONGOALCHEMY_DATABASE'] = 'undlFiles'
#db = MongoAlchemy(app)
# generation secret key
app.secret_key=b'a=pGw%4L1tB{aK6'
db = connect(host=Config.connect_string)

#################################################
# USER CLASS  
####################################################

class Itpp_User(Document):
    """ Definition of the class for the management of the Users """
    username= StringField()
    password = StringField()
    email = StringField()

####################################################
# BASIC RUTINES AND ROUTES
####################################################  

def calcRecord(Rs):
    """ JUST RETURN THE NUMBER OF RECORSET OF ONE RECORDSET PASSED AS PARAMETER """
    myRs=Rs.query.all()
    recup=0
    for x in myRs:
        recup=recup +1
    return recup

@app.route("/")
def main():
    """ Default route of the application (Login) """
    return render_template('login.html')

@app.route("/logout")
def logout():
    """ In order to manage the logout of the application """ 
    try:
        # Release the session's variables
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

@app.route("/listeuser")
def listeUser():
    """ List of User """
    try:
        if "username" in session:
            if "username" in session:
                myUser=Utilisateur.query.all()
                total=0
                for rec in myUser:
                    total=total+1
                myRecord=total
                return render_template('listeuser.html',myUser=myUser,myRecord=myRecord)
            else:
                return render_template('login.html')   
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))


@app.route("/createuser", methods=['GET', 'POST'])
def createUser():
    """ User creation """
    try:
        if "username" in session:
            if request.method == 'POST':
                myUser=Utilisateur(
                    firstname=request.form["inputFirstName"],
                    lastname=request.form["inputLastName"],
                    username=request.form["inputUserName"],
                    password=request.form["inputPassword"],
                    email=request.form["inputEmail"])
                myUser.save()
                flash('User saved !!! ', 'message')
                return redirect(url_for('listeUser'))
            if request.method == 'GET':
                return render_template('newuser.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))


@app.route("/updateuser", methods=['POST'])
def updateUser():
    """ User update """
    try:
        if "username" in session:
            myUser=Utilisateur.query.filter(Utilisateur.email==session["email"]).first()
            myUser.firstname=request.form["inputFirstName"]
            myUser.lastname=request.form["inputLastName"]
            myUser.username=request.form["inputUserName"]
            myUser.password=request.form["inputPassword"]
            myUser.email=request.form["inputEmail"]
            myUser.save()
            flash('User updated !!! ', 'message')
            return redirect(url_for('listeUser'))
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))


@app.route("/displayuser/<email>", methods=['GET'])
def displayUser(email):
    """ Display one User record """
    try:    
        if "username" in session:
            if request.method == 'GET':
                session["email"]=email
                myUser=Utilisateur.query.filter(Utilisateur.email==email).first()
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
                myUserToDelete=Utilisateur.query.filter(Utilisateur.email==email).first()
                myUserToDelete.remove()
                flash('User deleted !!! ', 'message')
                return redirect(url_for('listeUser'))
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

# check of the user exists
@app.route("/checkuser", methods=['POST'])
def checkUser():
    """ User check Identification """
    try: 
        # Tip for admin
        if (request.form["inputEmail"]=="admin@un.org" and request.form["inputPassword"]=="admin"):
            session["username"]="admin"
            return redirect(url_for('menu'))

        # Normal way
        myResult=Utilisateur.query.filter(Utilisateur.email==request.form["inputEmail"],Utilisateur.password==request.form["inputPassword"]).first()
        if myResult:
            session["username"]=myResult.username
            return redirect(url_for('menu'))
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

# And start building your routes.
@app.route('/')
def index():
    return_data = "bar"
    return(render_template('index.html', data=return_data))


####################################################
# START APPLICATION
####################################################  

if __name__=="__main__":
    app.run(debug=True)