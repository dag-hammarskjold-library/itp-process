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
# BASIC RUTINES AND ROUTES
####################################################  

@app.route("/main")
def main():
    """ Default route of the application (Login) """
    myUser=session["username"]
    myTime=session["startSession"]
    return render_template('main.html',myUser=myUser,myTime=myTime)

@app.route("/administration")
def administration():
    return render_template('administration.html')

@app.route("/")
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

@app.route("/listeuser")
def listeUser():
    return render_template('listeuser.html')


@app.route("/createuser", methods=['GET', 'POST'])
def createUser():
    return render_template('createuser.html')

@app.route("/updateuser", methods=['POST'])
def updateUser():
    return redirect(url_for('listeUser'))

@app.route("/displayuser/<email>", methods=['GET'])
def displayUser(email):
    return render_template('updateuser.html')

#delete the user
@app.route("/delete/<email>", methods=['GET'])
def deleteUser(email):
    return redirect(url_for('listeUser'))

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
# PROCESS MANAGEMENT ROUTES
####################################################  

@app.route("/listeprocess")
def listeProcess():
    return render_template('listeprocess.html')

@app.route("/createprocess", methods=['GET', 'POST'])
def createProcess():
    return render_template('createprocess.html')
####################################################
# START APPLICATION
####################################################  

if __name__=="__main__":
    app.run(debug=True)