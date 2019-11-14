from flask import Flask, render_template, request, abort, jsonify, Response, session,url_for,redirect,flash
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from requests import get
import boto3, re, os, pymongo
from mongoengine import connect,disconnect
from flask_mongoengine.wtf import model_form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from app.models import Itpp_log, Itpp_user, Itpp_section, Itpp_rule, Itpp_snapshot, Itpp_itp
from app.forms import LoginForm, SectionForm
from app.reports import ReportList, AuthNotFound, InvalidInput
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import DevelopmentConfig as Config
from dlx import DB, Bib, Auth
from bson.json_util import dumps
import time, json


###############################################################################################
# Create FLASK APPLICATION
###############################################################################################

# setting up the flask app

app = Flask(__name__)

# setting up the secret key and connect to the database

app.secret_key=b'a=pGw%4L1tB{aK6'
connect(host=Config.connect_string,db=Config.dbname)
URL_BY_DEFAULT = 'https://9inpseo1ah.execute-api.us-east-1.amazonaws.com/prod/symbol/'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message =""


####################################################
# BASIC ROUTINES AND ROUTES
####################################################  

@app.route("/")
@login_required
def main():
    user = current_user
    if current_user:
        return render_template('main.html',myUser=user,reports=ReportList.reports)
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
# Snapshots MANAGEMENT ROUTES
####################################################  
'''
Snapshots are the starting point of an ITP process. Once the ITP producer has 
validated the MARC data for the three relevant bodies and their resepective 
sessions, they will create a snapshot to begin the remaining part of the 
process.

The three bodies are A/ E/ and S/

The snapshot function (TBC) performs an Extraction of all the records for the 
three body/session identifiers and Filters the records to include only the 
fields the ITP report will need. What is saved in the database is the set of 
extracted and filtered records necessary to proceed.

From a snapshot, the ITP producer may begin assembling the sections that are 
part of each body/session document. 

So, in modeling terms: a snapshot has 3 documents; a document has many sections;
a section uses Rules to Display the values of specific fields, Grouped and 
Sorted.
'''
@app.route('/snapshots')
@login_required
def list_snapshots():
    pass
@app.route('/snapshots/<id>')
@login_required
def get_snapshot_by_id(id):
    b = 'A'
    s = '72'

    pass
@app.route('/snapshots/create')
@login_required
def create_snapshot():
    if request.args:
        '''
        params = []
        sessions = request.args.get('sessions').split(',')
        for s in sessions:
            params.append(('191','r',s))

        f,s,v = params[0]
        records = Bib.match_value(f,s,v)
        results = []
        for r in records:
            # do something
            pass
        '''
        
        return jsonify({'arguments':request.args})
    else:
        return jsonify({'status':'arguments required'})

@app.route('/snapshots/<id>/delete')
@login_required
def delete_snapshot(id):
    pass

@app.route("/displaySnapshot")
@login_required
def displaySnapshot():
    return render_template('snapshot.html')

@app.route("/executeSnapshot",methods=["POST"])
@login_required
def executeSnapshot():
    flash('The snapshot execution process is in progress !!! ','message')
    # the code of the execution should be here
    # don't forget to return the number of records created
    return redirect(url_for('main'))


####################################################
# ITPP ITP Routes
####################################################

@app.route("/itpp_itps")
@login_required
def list_itpp_itps():
    itps = Itpp_itp.objects
    #print(itps[0])
    return render_template('list_itpp_itps.html', data=itps)

@app.route("/itpp_itps/new", methods=['GET','POST'])
@login_required
def create_itpp_itp():
    if request.method == 'POST':
        name = request.form.get('name',None)
        body = request.form.get('body',None)
        itp_session = request.form.get('session')
        try:
            itp = Itpp_itp(name=name, body=body, itp_session=itp_session)
            itp.save()
            flash("ITP Document creation succeeded.")
            itp_id = json.loads(dumps(itp.id))['$oid']
            return json.dumps({
                "success":True, 
                "redirect": url_for('update_itpp_itp', id=itp_id, mode='add_sections')
            }), 200, {'ContentType':'application/json'}
        except:
            raise
            return json.dumps({"success":False}), 302, {'ContentType':'application/json'}
        #return redirect(url_for('list_itpp_itps'))
    return render_template('create_itpp_itp.html')

@app.route("/itpp_itps/<id>")
@login_required
def get_itpp_itp_by_id(id):
    pass

@app.route("/itpp_itps/<id>/update", methods=['GET','POST'])
@login_required
def update_itpp_itp(id):
    mode = request.args.get('mode','init')
    itp = Itpp_itp.objects.get(id=id)
    snapshots = Itpp_snapshot.objects
    if itp is not None:
        return render_template('update_itpp_itp.html', itp=itp, snapshots=snapshots, mode=mode)
    else:
        flash("Not found")
        return redirect(url_for('list_itpp_itps'))

@app.route("/itpp_itps/<id>/delete")
@login_required
def delete_itpp_itp(id):
    try:
        itp = Itpp_itp.objects(id=id)[0]
    except IndexError:
        flash("The ITP Document was not found.")
        return redirect(url_for('list_itpp_itps'))
    try:
        itp.delete()
        flash("ITP Document was successfully deleted.")
        return redirect(url_for('list_itpp_itps'))
    except:
        flash("Ubable to delete ITP Document.")
        return redirect(url_for('list_itpp_itps'))

@app.route("/itpp_itps/<itp_id>/sections")

@app.route("/itpp_itps/sections/new", methods=['POST'])
@login_required
def add_section():
    itp_id = request.form.get('itp_id',None)
    section_name = request.form.get('sectionName',None)
    section_order = request.form.get('setionOrder',None)
    data_source = request.form.get('dataSource',None)

    itp = Itpp_itp.objects(id=itp_id)[0]

    try:
        section = Itpp_section(
            name=section_name,
            section_order=section_order,
            data_source=data_source
        )
        itp.sections.append(section)
        itp.save()
        flash("ITP Section creation succeeded.")
        section_id = section.name
        return json.dumps({
            "success":True, 
            "redirect": url_for('update_itpp_itp', id=itp_id, mode='add_sections')
        }), 200, {'ContentType':'application/json'}
    except:
        raise
        return json.dumps({"success":False}), 302, {'ContentType':'application/json'}
    
    

@app.route("/itpp_itps/<itp_id>/sections/<section_id>", methods=['GET','POST'])

@app.route("/itpp_itps/<itp_id>/sections/<section_id>/delete")

@app.route("/itpp_itps/<itp_id>/sections/<section_id>/rules")
@login_required
def _expand_rules(itp_id,section_id):
    itp = Itpp_itp.objects.get(id=itp_id)
    section = itp.sections.get(name=section_id)
    if itp and section:
        return jsonify(section.rules)



####################################################
# Reports Management
####################################################

@app.route("/reports")
@login_required
def list_reports():
    return jsonify({"status":"Okay", "reports": [r.name for r in ReportList.reports]})

@app.route("/reports/<name>")
@login_required
def get_report_by_id(name):
    
    report = ReportList.get_by_name(name)
        
    if report is None:
        abort(400)
    
    form = report.form_class(formdata=request.args)
    
    if request.args:
        warning = None
        
        try:
            results = report.execute(request.args)
        except InvalidInput:
            results = []
            warning = 'Invalid input'
        except AuthNotFound:
            results = []
            warning = 'Session authority not found'
        except:
            raise
            
        return render_template('report.html', report=report, form=form, resultsSearch=results ,recordNumber=len(results),url=URL_BY_DEFAULT,errorMail=warning)
    else:
        results = []        
        return render_template('report.html', report=report, form=form)

####################################################
# START APPLICATION
####################################################  

if __name__=="__main__":
    app.run(debug=True)