from flask import Flask, render_template, request, abort, jsonify, Response, session,url_for,redirect,flash
from requests import get
import boto3, re, os, pymongo
#from flask import Flask
#from flask_mongoalchemy import MongoAlchemy
#from flask_admin import Admin
#from flask_admin.contrib.sqla import ModelView
#from flask_login import UserMixin
#from bson.objectid import ObjectId
from mongoengine import connect, Document, StringField
from datetime import datetime
from werkzeug.utils import secure_filename
from config import DevelopmentConfig as Config
import time

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

####################################################
# BASIC RUTINES AND ROUTES
####################################################  

def calcRecord(Rs):
    """ JUST RETURN THE NUMBER OF RECORSET OF ONE RECORDSET PASSED AS PARAMETER """
    #myRs=Rs.query.all()
    recup=0
    #for x in myRs:
    #    recup=recup +1
    return recup

@app.route("/main")
def main():
    """ Default route of the application (Login) """
    myUser=session["username"]
    myTime=session["startSession"]
    return render_template('main.html',myUser=myUser,myTime=myTime)

@app.route("/administration")
def administration():
    try:
        if "username" in session:
            #myLog=Itpp_Log.query.all()
            total=0
            #for rec in myLog:
            #    total=total+1
            myRecord=total
            #return render_template('administration.html',myLog=myLog,myRecord=myRecord)
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
        # Creation Log
        #myLog=Itpp_Log(
        #    when=datetime.datetime.now(),
        #    description="Logout the application !!!",
        #    user=session["username"])
        #myLog.save()
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
            #myUser=Itpp_User.query.all()
            total=0
            #for rec in myUser:
            #    total=total+1
            myRecord=total
            #return render_template('listeuser.html',myUser=myUser,myRecord=myRecord)
            return render_template('listeuser.html')
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
                #myUser=Itpp_User(
                #    username=request.form["inputUser"],
                #    password=request.form["inputPassword"],
                #    email=request.form["inputEmail"])
                #myUser.save()
                    
                # Creation Log
                #myLog=Itpp_Log(
                #    when=datetime.datetime.now(),
                #    description="New User added !!!",
                #    user=session["username"])
                #myLog.save()

                flash('New User Saved in the database !!! ', 'message')
                return redirect(url_for('listeUser'))
            if request.method == 'GET':
                return render_template('user.html')
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
            #myUser=Itpp_User.query.filter(Itpp_User.email==session["email"]).first()
            #myUser.username=request.form["inputUser"]
            #myUser.password=request.form["inputPassword"]
            #myUser.email=request.form["inputEmail"]
            #myUser.save()
            #flash('User updated !!! ', 'message')
            # Creation Log
            #myLog=Itpp_Log(
            #        when=datetime.datetime.now(),
            #        description="User {} Updated !!!".format(myUser.username),
            #        user=session["username"])
            #myLog.save()
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
                #myUserToDelete.remove()
                flash('User deleted !!! ', 'message')
                # Creation Log
                #myLog=Itpp_Log(
                #when=datetime.datetime.now(),
                #description="User {} deleted !!!".format(myUserToDelete.username),
                #user=session["username"])
                #myLog.save()
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
    try: 
        # Tip for admin
        if (request.form["inputEmail"]=="admin@un.org" and request.form["inputPassword"]=="admin"):
            session["username"]="admin"
            session["email"]="admin@un.org"
            session["startSession"]=time.asctime( time.localtime(time.time()))
            # Creation Log
            #myLog=Itpp_Log(
            #    when=datetime.datetime.now(),
            #    description="New Connection !!!",
            #    user=session["username"])
            #myLog.save()
            return redirect(url_for('main'))

        # Normal way
        
        myResult=Itpp_User.query.filter(Itpp_User.email==request.form["inputEmail"],Itpp_User.password==request.form["inputPassword"]).first()
        if myResult:
            session["username"]=myResult.username
            # Creation Log
            #myLog=Itpp_Log(
            #    when=datetime.datetime.now(),
            #    description="New Connection !!!",
            #    user=session["username"])
            #myLog.save()
            return redirect(url_for('main'))
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

####################################################
# RULE MANAGEMENT ROUTES
####################################################  


@app.route("/createrule", methods=['GET', 'POST'])
def createRule():
    """ Rule creation """
    try:
        if "username" in session:
            if request.method == 'POST':
                #myUser=Itpp_User(
                #    username=request.form["inputUser"],
                #    password=request.form["inputPassword"],
                #    email=request.form["inputEmail"])
                #myUser.save()
                    
                # Creation Log
                #myLog=Itpp_Log(
                #    when=datetime.datetime.now(),
                #    description="New User added !!!",
                #    user=session["username"])
                #myLog.save()

                flash('New Rule Saved in the database !!! ', 'message')
                return redirect(url_for('listeRule'))
            if request.method == 'GET':
                return render_template('createrule.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))

# special one
@app.route("/createrule01", methods=['GET', 'POST'])
def createRule01():
    return render_template('createrule01.html')

@app.route("/listerule")
def listeRule():
    """ List of Rule """
    try:
        if "username" in session:
            #myUser=Itpp_User.query.all()
            total=0
            #for rec in myUser:
            #    total=total+1
            myRecord=total
            #return render_template('listerule.html',myUser=myUser,myRecord=myRecord)
            return render_template('listerule.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))


####################################################
# PROCESS MANAGEMENT ROUTES
####################################################  

@app.route("/listeprocess")
def listeProcess():
    """ List of Process """
    try:
        if "username" in session:
            #myUser=Itpp_User.query.all()
            total=0
            #for rec in myUser:
            #    total=total+1
            myRecord=total
            #return render_template('listprocess.html',myUser=myUser,myRecord=myRecord)
            return render_template('listeprocess.html')
        else:
            flash('Unknown user !!! ','error')
            return render_template('login.html')
    except:
        return redirect(url_for('appError'))



@app.route("/createprocess", methods=['GET', 'POST'])
def createProcess():
    """ Process creation """
#try:
    if "username" in session:
        if request.method == 'POST':
            #myUser=Itpp_User(
            #    username=request.form["inputUser"],
            #    password=request.form["inputPassword"],
            #    email=request.form["inputEmail"])
            #myUser.save()
                
            # Creation Log
            #myLog=Itpp_Log(
            #    when=datetime.datetime.now(),
            #    description="New User added !!!",
            #    user=session["username"])
            #myLog.save()

            flash('New Process Saved in the database !!! ', 'message')
            return redirect(url_for('listeProcess'))
        if request.method == 'GET':
            return render_template('createprocess.html')
    else:
        flash('Unknown user !!! ','error')
        return render_template('login.html')
#except:
#    return redirect(url_for('appError'))


####################################################
# START APPLICATION
####################################################  

if __name__=="__main__":
    app.run(debug=True)