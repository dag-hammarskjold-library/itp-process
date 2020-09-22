import logging
from flask import Flask, render_template, request, abort, jsonify, Response, session,url_for,redirect,flash,send_file
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from requests import get
import boto3, re, os, pymongo
from botocore.exceptions import ClientError
from mongoengine import connect,disconnect
from app.reports import ReportList, AuthNotFound, InvalidInput, _get_body_session
from app.aggregations import process_section, lookup_code, lookup_snapshots, section_summary
from app.snapshot import Snapshot
from flask_mongoengine.wtf import model_form
from wtforms.validators import DataRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from app.models import Itpp_log, Itpp_user, Itpp_section, Itpp_rule, Itpp_snapshot, Itpp_itp
from app.forms import LoginForm, SectionForm
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import Config
from dlx import DB
from dlx.marc import Bib, Auth, BibSet, QueryDocument,Condition,Or
from bson.json_util import dumps
from bson.objectid import ObjectId
import bson
import time, json, io, uuid, math
from time import sleep
from zappa.asynchronous import task, get_async_response
from pymongo import MongoClient
from copy import deepcopy
from app.word import generateWordDocITPITSC,generateWordDocITPITSP,generateWordDocITPITSS,generateWordDocITPSOR,generateWordDocITPRES,generateWordDocITPSUBJ,generateWordDocITPDSL,generateWordDocITPMEET,generateWordDocITPAGE
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from boto3 import client
import platform


###############################################################################################
# Create FLASK APPLICATION
###############################################################################################

# setting up the flask app

app = Flask(__name__)

# setting up the secret key and connect to the database

app.secret_key=b'a=pGw%4L1tB{aK6'
connect(host=Config.connect_string,db=Config.dbname)
URL_BY_DEFAULT = Config.url_prefix


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message =""

s3 = boto3.client('s3')


####################################################
# BASIC ROUTINES AND ROUTES
####################################################  

@app.route('/_clear')
def clear_session():
    session.clear()
    return redirect(url_for('main'))

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

@app.route("/users/<id>/validate")
@login_required
def validate_user_by_id(id):
    try:
        user = Itpp_user.objects.get(id=id)
    except:
        abort(404)
    
    if user.email == 'admin@un.org':
        flash("The user identified by admin@un.org cannot be validated.")
        return redirect(request.referrer)

    ses_client = boto3.client('ses')
    response = ses_client.get_identity_verification_attributes(
        Identities = [
            user.email
        ]
    )

    print(response)

    try:
        verification_status = response['VerificationAttributes'][user.email]['VerificationStatus']
        if verification_status != 'Success':
            flash("The user's validation is still pending.")
        else:
            user.ses_verified = 'Success'
            user.save()
            flash("The user's validation was successful.")
    except KeyError:
        ses_client.verify_email_identity(EmailAddress=user.email)
        user.ses_verified = 'Pending'
        user.save()
        flash("We have sent a validation email to the user.")

    return redirect(request.referrer)

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
#@login_required
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
    snapshot=Snapshot('ZZZZ','0001')
    return render_template('snapshot.html', snapshots=snapshot.list())

@task
def transform_and_write_snapshot(body, session):
    form = "Select Authority"
    snapshot=Snapshot(body,session) # snapshot class uses A and 72
    if snapshot is None:
        abort(400)
    if not (body,session) is None:
        warning = None
        try:
            snapshot.transform_write()
        except InvalidInput:
            number=0
            warning = 'Invalid input'
        except AuthNotFound:
            number=0
            warning = 'Session authority not found'
        except:
            warning = 'Unknown Problem'
        #return render_template('snapshot.html', snapshot=snapshot, snapshots=snapshot.list(), form=form, recordNumber=snapshot.snapshot_len,url=URL_BY_DEFAULT,errorMail=warning)
    else:
        snapshot= None
        #return redirect(url_for('main'))    
        #return render_template('snapshot.html', snapshot=snapshot, snapshots=snapshot.list(),form=form)    


@app.route("/executeSnapshot",methods=["POST"])
@login_required
def executeSnapshot():
    form = "Select Authority"
    number=0
    body,session=_get_body_session(request.form.get("authority"))
    body=body.split('/')[0]#_get_body_session returns A/ and 72 ; only temporary to ensure that rules are correctly read
    print(f"body and session are {body} and {session}")
    transform_and_write_snapshot(body, session)
    # the code of the execution should be here
    # don't forget to return the number of records created
    #flash(f'The snapshot execution process is in progress! Number of records is {snapshot.snapshot_len} ','message')    
    return redirect(url_for('main'))


####################################################
# ITPP ITP Routes
####################################################

@app.route("/itpp_itps")
@login_required
def list_itpp_itps():
    itps = Itpp_itp.objects
    return render_template('itpp_itp/list.html', data=itps)

@app.route("/itpp_itps/new", methods=['GET','POST'])
@login_required
def create_itpp_itp():
    if request.method == 'POST':
        name = request.form.get('name',None)
        body = request.form.get('body',None)
        itp_session = request.form.get('session',None)
        body_session_auth = request.form.get('bodySessionAuth',None)
        try:
            itp = Itpp_itp(name=name, body=body, itp_session=itp_session, body_session_auth=body_session_auth)
            itp.save()
            flash("ITP Document creation succeeded.")
            itp_id = json.loads(dumps(itp.id))['$oid']
            return redirect(url_for('update_itpp_itp', id=itp_id, mode='sections'))
        except:
            flash("Could not create the ITP Document.")
            return render_template('itpp_itp/create.html')
    else:
        return render_template('itpp_itp/create.html')

@app.route("/itpp_itps/<id>/clone" )#methods=['POST'])
@login_required
def clone_itpp_itp(id):
    try:
        itp = Itpp_itp.objects.get(id=id)
        clone = Itpp_itp(
            name='Clone of ' + itp.name, 
            body=itp.body, 
            itp_session=itp.itp_session, 
            body_session_auth=itp.body_session_auth,
            sections = itp.sections
        )
        clone.save()
        flash("Cloned document successfully.")
        return redirect(url_for('list_itpp_itps'))
    except:
        flash("Could not clone the ITP Document.")
        raise
        return redirect(url_for('list_itpp_itps'))


@app.route("/itpp_itps/<id>")
@login_required
def get_itpp_itp_by_id(id):
    try:
        itp = Itpp_itp.objects.get(id=id)
        return render_template('itpp_itp/view.html', itp=itp)
    except:
        raise

@app.route("/itpp_itps/<id>/update", methods=['GET','POST'])
@login_required
def update_itpp_itp(id):
    if request.method == 'POST':
        name = request.form.get('name',None)
        body = request.form.get('body',None)
        itp_session = request.form.get('session',None)
        body_session_auth = request.form.get('bodySessionAuth',None)
        try:
            itp = Itpp_itp.objects.get(id=id)
            itp.name = name
            itp.body = body
            itp.itp_session = itp_session
            itp.body_session_auth = body_session_auth
            itp.save()
            flash("ITP Document save succeeded.")
            itp_id = json.loads(dumps(itp.id))['$oid']
            return json.dumps({
                "success":True, 
                "redirect": url_for('update_itpp_itp', id=itp_id, mode='sections')
            }), 200, {'ContentType':'application/json'}
        except:
            raise
            return json.dumps({"success":False}), 400, {'ContentType':'application/json'}
    mode = request.args.get('mode','meta')
    itp = Itpp_itp.objects.get(id=id)
    snapshots = Itpp_snapshot.objects
    if itp is not None:
        return render_template('itpp_itp/update.html', itp=itp, snapshots=snapshots, mode=mode)
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

@app.route("/itpp_itps/<id>/sections/new", methods=['POST'])
@login_required
def add_section(id):
    itp_id = request.form.get('itp_id',None)
    section_name = request.form.get('sectionName',None)
    section_order = request.form.get('sectionOrder',None)
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
            "redirect": url_for('update_itpp_itp', id=itp_id, mode='sections')
        }), 200, {'ContentType':'application/json'}
    except:
        raise
        return json.dumps({"success":False}), 400, {'ContentType':'application/json'}

@app.route("/itpp_itps/<target_itp_id>/sections/cloneFrom", methods=['POST'])
@login_required
def clone_section(target_itp_id):
    if request.method == 'POST':
        source_itp_id = request.form.get('sourceItpId',None)
        section_id = request.form.get('sectionId', None)
        source_itp = Itpp_itp.objects.get(id=source_itp_id)
        try:
            source_section = Itpp_itp.objects.get(id=bson.ObjectId(source_itp_id), sections__id=bson.ObjectId(section_id)).sections[0]
            target_itp = Itpp_itp.objects.get(id=target_itp_id)
            target_section = Itpp_section(
                name='Copy of ' + source_section.name,
                section_order = source_section.section_order,
                data_source = source_section.data_source,
                rules = source_section.rules
            )
            target_itp.sections.append(target_section)
            target_itp.save()
            flash("Clone succeeded.")
            return json.dumps({
                "success":True, 
                "redirect": url_for('update_itpp_itp', id=target_itp_id, mode='sections')
            }), 200, {'ContentType':'application/json'}
        except:
            raise
            return json.dumps({
                'success': False,
            }), 400, {'ContentType': 'application/json'}
    # method is GET
    itp_list = Itpp_itp.objects
    
@app.route("/itpp_itps/sections")
def list_all_sections():
    return_data = []
    for itp in Itpp_itp.objects:
        for section in itp.sections:
            return_data.append({'itp': {'id': str(itp.id), 'name': itp.name}, 'section': {'id': str(section.id), 'name': section.name}})
    return json.dumps(return_data), 200, {'ContentType': 'application/json'}

@app.route("/itpp_itps/<itp_id>/sections", methods=['GET','POST'])
def get_or_update_section(itp_id):
    if request.method == 'POST':
        section_id = request.form.get('section_id',None)
        name = request.form.get('sectionName',None)
        order = request.form.get('sectionOrder',None)
        #print(section_id, name, order)
        try:
            itp = Itpp_itp.objects.get(id=itp_id, sections__id=section_id)
            for section in itp.sections:
                if section.id == bson.ObjectId(section_id):
                    section.name=name
                    section.section_order=order

            itp.save()
            flash("ITP Document save succeeded.")
            itp_id = json.loads(dumps(itp.id))['$oid']
            return json.dumps({
                "success":True, 
                "redirect": url_for('update_itpp_itp', id=itp_id, mode='sections')
            }), 200, {'ContentType':'application/json'}
        except:
            raise
            return json.dumps({"success":False}), 400, {'ContentType':'application/json'}
    mode = request.args.get('mode','init')
    itp = Itpp_itp.objects.get(id=itp_id)
    snapshots = Itpp_snapshot.objects
    if itp is not None:
        return render_template('update_itpp_itp.html', itp=itp, snapshots=snapshots, mode=mode)
    else:
        flash("Not found")
        return redirect(url_for('list_itpp_itps'))

@app.route("/itpp_itps/<itp_id>/sections/<section_id>/delete")
@login_required
def delete_section(itp_id,section_id):
    try:
        itp = Itpp_itp.objects(id=itp_id)[0]
        itp.update(pull__sections__id=bson.ObjectId(section_id))
        return redirect(url_for('update_itpp_itp', id=itp_id, mode='sections'))

    except:
        raise

@app.route("/itpp_itps/<itp_id>/sections/<section_id>/rules", methods=['GET','POST'])
@login_required
def get_or_update_rule(itp_id,section_id):
    itp = Itpp_itp.objects.get(id=itp_id, sections__id=section_id)
    if request.method == 'POST':
        rule_id = request.form.get('rule_id',None)
        name = request.form.get('ruleName',None)
        order = request.form.get('processOrder',None)
        rule_type = request.form.get('ruleType',None)
        parameters = request.form.get('parameters',None)
        try:
            itp = Itpp_itp.objects.get(id=itp_id)
            section = None
            for section in itp.sections:
                if section.id == bson.ObjectId(section_id):
                    for rule in section.rules:
                        if rule.id == bson.ObjectId(rule_id):
                            rule.name = name
                            rule.process_order = order
                            rule.rule_type = rule_type
                            rule.parameters = parameters.split(',')
                            itp.save()
                            flash("Rule saved successfully")
                            print()
                            return json.dumps({
                                "success":True, 
                                "redirect": url_for('get_or_update_rule', itp_id=itp.id, section_id=section.id, mode='rules')
                            }), 200, {'ContentType':'application/json'}
        except:
            raise
            return json.dumps({"success":False}), 400, {'ContentType':'application/json'}

    for section in itp.sections:
        if section.id == bson.ObjectId(section_id):
            return render_template('itpp_itp/update.html', mode='rules', itp=itp, section=section, rules=section.rules)
    

@app.route("/itpp_itps/<itp_id>/sections/<section_id>/rules/new", methods=['GET','POST'])
@login_required
def add_rule(itp_id,section_id):
    itp = Itpp_itp.objects.get(id=itp_id, sections__id=section_id)
    if request.method == 'POST':
        name = request.form.get('ruleName',None)
        order = request.form.get('processOrder',None)
        rule_type = request.form.get('ruleType',None)
        parameters = request.form.get('parameters','').split(",")


        itp = Itpp_itp.objects.get(id=itp_id)
        section = next(filter(lambda x: x.id == bson.ObjectId(section_id),itp.sections),None)

        try:
            rule = Itpp_rule(
                name=name,
                process_order=order,
                rule_type=rule_type,
                parameters=parameters
            )
            section.rules.append(rule)
            itp.save()
            flash("ITP Rule creation succeeded.")
            rule_id = rule.id
            return json.dumps({
                "success":True, 
                "redirect": url_for('get_or_update_rule', itp_id=itp.id, section_id=section.id, mode='rules')
            }), 200, {'ContentType':'application/json'}
        except:
            raise
            return json.dumps({"success":False}), 400, {'ContentType':'application/json'}
    
    for section in itp.sections:
        if section.id == bson.ObjectId(section_id):
            return render_template('itpp_itp/update.html', mode='rules', itp=itp, section=section, rules=section.rules)

@app.route("/itpp_itps/<itp_id>/sections/<section_id>/rules/<rule_id>/delete")
@login_required
def delete_rule(itp_id, section_id, rule_id):
    try:
        itp = Itpp_itp.objects.get(id=itp_id)
        #itp.update(sections__id=bson.ObjectId(section_id),pull__sections__rules__id=bson.ObjectId(rule_id))
        #itp = Itpp_itp.objects(id=bson.ObjectId(itp_id), sections__id=bson.ObjectId(section_id), sections__rules__id=bson.ObjectId(rule_id))[0]
        for section in itp.sections:
            if section.id == bson.ObjectId(section_id):
                idx = 0
                for rule in section.rules:
                    if rule.id == bson.ObjectId(rule_id):
                        print(section.id, rule.id)
                        section.rules.pop(idx)
                        itp.save()
                    else:
                        idx += 1
                return render_template('itpp_itp/update.html', mode='rules', itp=itp, section=section, rules=section.rules)
                #return redirect(url_for('update_itpp_itp', id=itp_id, section=section, mode='rules'))
        
    except:
        raise


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
            
        return render_template(
            'report.html', 
            report = report, 
            form = form, 
            resultsSearch = results, 
            recordNumber = len(results), 
            url = URL_BY_DEFAULT, 
            errorMail = warning
        )        
    else:
        results = []        
        return render_template('report.html', report=report, form=form)

####################################################
# ITPP Display
####################################################

myMongoURI = Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase = myClient.undlFiles
myCollection = myDatabase['itp_sample_output_copy']

################## DISPLAY ALL THE RECORDS OF THE SECTION ###########################################################

@app.route('/itpp_itpsor/<offset>',methods=["GET"])
@login_required
def itpp_itpsor(offset=0):

    # delete old file in the server
    if os.path.exists('itpsor.docx'):
        deleteFile('itpsor.docx')
    
    # definition of the offset and the limit
    #offset=int(request.args["offset"])
    offset=int(offset)
    
    # retrieve the first value and the last value of the set
    firstId= myCollection.find().sort("_id",pymongo.ASCENDING)
    lastId=firstId[offset]["_id"]
    
    # retrieve the set of data
    myTotal = myCollection.find({'section': 'itpsor'}).count()
    
    # definition of the default limit
    if myTotal<100 :
        defaultLimit=10
    
    if myTotal >=100 and myTotal <= 1000 :
        defaultLimit=25
        
    if myTotal > 1000:
        defaultLimit=100
    

    myRecords = myCollection.find({"$and":[{"_id": {"$gte": lastId}},{'section': 'itpsor'}]}).sort("_id", pymongo.ASCENDING).limit(defaultLimit)

    myOffset=int(myTotal/defaultLimit)
    
    # dynamic url generation
    firstUrl=url_for('itpp_itpsor',offset=0)
    
    if offset < (myOffset*defaultLimit):
        nextUrl=url_for('itpp_itpsor',offset=offset+defaultLimit)
    else:
        nextUrl=url_for('itpp_itpsor',offset=offset)
        
    if offset >= defaultLimit:
        prevUrl=url_for('itpp_itpsor',offset=offset-defaultLimit) 
    else:
        prevUrl=url_for('itpp_itpsor',offset=offset)
        
    lastUrl=url_for('itpp_itpsor',offset=myOffset*defaultLimit)
    
    # return values to render
    return render_template('itpsor.html',
                           myRecords=myRecords,
                           nextUrl=nextUrl,
                           prevUrl=prevUrl,
                           firstUrl=firstUrl,
                           lastUrl=lastUrl,
                           totalRecord= myTotal,
                           myOffset=offset,
                           URL_PREFIX=URL_BY_DEFAULT
                           )

@app.route('/itpp_itpitsc/<offset>',methods=["GET"])
@login_required
def itpp_itpitsc(offset=0):
    
    # delete old file in the server
    if os.path.exists('itpitsc.docx'):
        deleteFile('itpitsc.docx')
    
    # definition of the offset and the limit
    offset=int(offset)
    
    # retrieve the first value and the last value of the set
    firstId= myCollection.find({'section': 'itpitsc'}, {'itshead': 1, 
       'itssubhead': 1, 'itsentry': 1, 'docsymbol': 1}).sort("_id",pymongo.ASCENDING)
    lastId=firstId[offset]["_id"]
    
    # retrieve the set of data
    myTotal = myCollection.find({'section': 'itpitsc'}).count()
    
    # definition of the default limit
    if myTotal<100 :
        defaultLimit=10
    
    if myTotal >=100 and myTotal <= 1000 :
        defaultLimit=25
        
    if myTotal > 1000:
        defaultLimit=100
    

    myRecords = myCollection.find({"$and":[{"_id": {"$gte": lastId}},{'section': 'itpitsc'}]}).sort("_id", pymongo.ASCENDING).limit(defaultLimit)

    myOffset=int(myTotal/defaultLimit)
    

    # dynamic url generation
    firstUrl=url_for('itpp_itpitsc',offset=0)
    
    if offset < (myOffset*defaultLimit):
        nextUrl=url_for('itpp_itpitsc',offset=offset+defaultLimit)
    else:
        nextUrl=url_for('itpp_itpitsc',offset=offset)
        
    if offset >= defaultLimit:
        prevUrl=url_for('itpp_itpitsc',offset=offset-defaultLimit) 
    else:
        prevUrl=url_for('itpp_itpitsc',offset=offset)
        
    lastUrl=url_for('itpp_itpitsc',offset=myOffset*defaultLimit)
    
    # return values to render
    return render_template('itpitsc.html',
                           myRecords=myRecords,
                           nextUrl=nextUrl,
                           prevUrl=prevUrl,
                           firstUrl=firstUrl,
                           lastUrl=lastUrl,
                           totalRecord= myTotal,
                           myOffset=offset,
                           URL_PREFIX=URL_BY_DEFAULT
                           )

@app.route('/itpp_itpitsp/<offset>',methods=["GET"])
@login_required
def itpp_itpitsp(offset=0):
    
    # delete old file in the server
    if os.path.exists('itpitsp.docx'):
        deleteFile('itpitsp.docx')
    
    # definition of the offset and the limit
    offset=int(offset)
    
    # retrieve the first value and the last value of the set
    firstId= myCollection.find({'section': 'itpitsp'}, {'itshead': 1, 
       'itssubhead': 1, 'docsymbol': 1}).sort("_id",pymongo.ASCENDING)
    lastId=firstId[offset]["_id"]
    
    # retrieve the set of data
    myTotal = myCollection.find({'section': 'itpitsp'}).count()
    
    # definition of the default limit
    if myTotal<100 :
        defaultLimit=10
    
    if myTotal >=100 and myTotal <= 1000 :      
        defaultLimit=25
        
    if myTotal > 1000:
        defaultLimit=100
    

    myRecords = myCollection.find({"$and":[{"_id": {"$gte": lastId}},{'section': 'itpitsp'}]}).sort("_id", pymongo.ASCENDING).limit(defaultLimit)

    myOffset=int(myTotal/defaultLimit)
    
    # dynamic url generation
    firstUrl=url_for('itpp_itpitsp',offset=0)
    
    if offset < (myOffset*defaultLimit):
        nextUrl=url_for('itpp_itpitsp',offset=offset+defaultLimit)
    else:
        nextUrl=url_for('itpp_itpitsp',offset=offset)
        
    if offset >= defaultLimit:
        prevUrl=url_for('itpp_itpitsp',offset=offset-defaultLimit) 
    else:
        prevUrl=url_for('itpp_itpitsp',offset=offset)
        
    lastUrl=url_for('itpp_itpitsp',offset=myOffset*defaultLimit)
    
    # return values to render
    return render_template('itpitsp.html',
                           myRecords=myRecords,
                           nextUrl=nextUrl,
                           prevUrl=prevUrl,
                           firstUrl=firstUrl,
                           lastUrl=lastUrl,
                           totalRecord= myTotal,
                           myOffset=offset,
                           URL_PREFIX=URL_BY_DEFAULT
                           )

@app.route('/itpp_itpitss/<offset>',methods=["GET"])
@login_required
def itpp_itpitss(offset=0):
    
    # delete old file in the server
    if os.path.exists('itpitss.docx'):
        deleteFile('itpitss.docx')
    
    # definition of the offset and the limit
    offset=int(offset)
    
    # retrieve the first value and the last value of the set
    firstId= myCollection.find({'section': 'itpitss'}, {'itshead': 1, 
       'itssubhead': 1, 'itsentry': 1, 'docsymbol': 1}).sort("_id",pymongo.ASCENDING)
    lastId=firstId[offset]["_id"]
    
    # retrieve the set of data
    myTotal = myCollection.find({'section': 'itpitss'}).count()

    # definition of the default limit
    if myTotal<100 :
        defaultLimit=10
    
    if myTotal >=100 and myTotal <= 1000 :
        defaultLimit=25
        
    if myTotal > 1000:
        defaultLimit=100

    myRecords = myCollection.find({"$and":[{"_id": {"$gte": lastId}},{'section': 'itpitss'}]}).sort("_id", pymongo.ASCENDING).limit(defaultLimit)

    myOffset=int(myTotal/defaultLimit)
    
    # dynamic url generation
    firstUrl=url_for('itpp_itpitss',offset=0)
    
    if offset < (myOffset*defaultLimit):
        nextUrl=url_for('itpp_itpitss',offset=offset+defaultLimit)
    else:
        nextUrl=url_for('itpp_itpitss',offset=offset)
        
    if offset >= defaultLimit:
        prevUrl=url_for('itpp_itpitss',offset=offset-defaultLimit) 
    else:
        prevUrl=url_for('itpp_itpitss',offset=offset)
        
    lastUrl=url_for('itpp_itpitss',offset=myOffset*defaultLimit)
    
    # return values to render
    return render_template('itpitss.html',
                           myRecords=myRecords,
                           nextUrl=nextUrl,
                           prevUrl=prevUrl,
                           firstUrl=firstUrl,
                           lastUrl=lastUrl,
                           totalRecord= myTotal,
                           myOffset=offset,
                           URL_PREFIX=URL_BY_DEFAULT
                           )
    
@app.route('/itpp_itpres/<offset>',methods=["GET"])
@login_required
def itpp_itpres(offset=0):
    
    # delete old file in the server
    if os.path.exists('itpres.docx'):
        deleteFile('itpres.docx')
    
    # definition of the offset and the limit
    offset=int(offset)
    
    # retrieve the first value and the last value of the set
    firstId= myCollection.find({'section': 'itpres'}, {'ainumber': 1, 
       'bodysession': 1, 'meeting': 1, 'docsymbol': 1, 'record_id': 1, 'section': 1, 'title': 1, 'vote': 1, 'votedate': 1, 'subject': 1, 'subjectsubtitle': 1}).sort("_id",pymongo.ASCENDING)
    lastId=firstId[offset]["_id"]
    
    # retrieve the set of data
    myTotal = myCollection.find({'section': 'itpres'}).count()

    # definition of the default limit
    if myTotal<100 :
        defaultLimit=10
    
    if myTotal >=100 and myTotal <= 1000 :
        defaultLimit=25
        
    if myTotal > 1000:
        defaultLimit=100

    myRecords = myCollection.find({"$and":[{"_id": {"$gte": lastId}},{'section': 'itpres'}]}).sort("_id", pymongo.ASCENDING).limit(defaultLimit)

    myOffset=int(myTotal/defaultLimit)
    
    # dynamic url generation
    firstUrl=url_for('itpp_itpres',offset=0)
    
    if offset < (myOffset*defaultLimit):
        nextUrl=url_for('itpp_itpres',offset=offset+defaultLimit)
    else:
        nextUrl=url_for('itpp_itpres',offset=offset)
        
    if offset >= defaultLimit:
        prevUrl=url_for('itpp_itpres',offset=offset-defaultLimit) 
    else:
        prevUrl=url_for('itpp_itpres',offset=offset)
        
    lastUrl=url_for('itpp_itpres',offset=myOffset*defaultLimit)
    
    # return values to render
    return render_template('itpres.html',
                           myRecords=myRecords,
                           nextUrl=nextUrl,
                           prevUrl=prevUrl,
                           firstUrl=firstUrl,
                           lastUrl=lastUrl,
                           totalRecord= myTotal,
                           myOffset=offset,
                           URL_PREFIX=URL_BY_DEFAULT
                           )

@app.route('/itpp_itpsubj/<offset>',methods=["GET"])
@login_required
def itpp_itpsubj(offset=0):
    
    # delete old file in the server
    if os.path.exists('itpsubj.docx'):
        deleteFile('itpsubj.docx')
    
    # definition of the offset and the limit
    offset=int(offset)
    
    # retrieve the first value and the last value of the set
    firstId= myCollection.find({'section': 'itpsubj'}, {
       'bodysession': 1,'_id': 1, 'section': 1, 'head': 1, 'subheading': 1}).sort("_id",pymongo.ASCENDING)
    lastId=firstId[offset]["_id"]
    
    # retrieve the set of data
    myTotal = myCollection.find({'section': 'itpsubj'}).count()

    # definition of the default limit
    if myTotal<100 :
        defaultLimit=10
    
    if myTotal >=100 and myTotal <= 1000 :
        defaultLimit=25
        
    if myTotal > 1000:
        defaultLimit=100

    myRecords = myCollection.find({"$and":[{"_id": {"$gte": lastId}},{'section': 'itpsubj'}]}).sort("_id", pymongo.ASCENDING).limit(defaultLimit)

    myOffset=int(myTotal/defaultLimit)
    
    # dynamic url generation
    firstUrl=url_for('itpp_itpsubj',offset=0)
    
    if offset < (myOffset*defaultLimit):
        nextUrl=url_for('itpp_itpsubj',offset=offset+defaultLimit)
    else:
        nextUrl=url_for('itpp_itpsubj',offset=offset)
        
    if offset >= defaultLimit:
        prevUrl=url_for('itpp_itpsubj',offset=offset-defaultLimit) 
    else:
        prevUrl=url_for('itpp_itpsubj',offset=offset)
        
    lastUrl=url_for('itpp_itpsubj',offset=myOffset*defaultLimit)
    
    # return values to render
    return render_template('itpsubj.html',
                           myRecords=myRecords,
                           nextUrl=nextUrl,
                           prevUrl=prevUrl,
                           firstUrl=firstUrl,
                           lastUrl=lastUrl,
                           totalRecord= myTotal,
                           myOffset=offset,
                           URL_PREFIX=URL_BY_DEFAULT
                           )

@app.route('/itpp_itpdsl/<offset>',methods=["GET"])
def itpp_itpdsl(offset=0):
    
    # delete old file in the server
    if os.path.exists('itpdsl.docx'):
        deleteFile('itpdsl.docx')
    
    # definition of the offset and the limit
    offset=int(offset)
    
    # retrieve the first value and the last value of the set
    firstId= myCollection.find({'section': 'itpdsl'}, {
       'bodysession': 1,'_id': 1, 'section': 1, 'committee': 1, 'series': 1 , 'docsymbol': 1}).sort("_id",pymongo.ASCENDING)
    lastId=firstId[offset]["_id"]
    
    # retrieve the set of data
    myTotal = myCollection.find({'section': 'itpdsl'}).count()

    # definition of the default limit
    if myTotal<100 :
        defaultLimit=10
    
    if myTotal >=100 and myTotal <= 1000 :
        defaultLimit=25
        
    if myTotal > 1000:
        defaultLimit=100

    myRecords = myCollection.find({"$and":[{"_id": {"$gte": lastId}},{'section': 'itpdsl'}]}).sort("_id", pymongo.ASCENDING).limit(defaultLimit)

    myOffset=int(myTotal/defaultLimit)
    
    # dynamic url generation
    firstUrl=url_for('itpp_itpdsl',offset=0)
    
    if offset < (myOffset*defaultLimit):
        nextUrl=url_for('itpp_itpdsl',offset=offset+defaultLimit)
    else:
        nextUrl=url_for('itpp_itpdsl',offset=offset)
        
    if offset >= defaultLimit:
        prevUrl=url_for('itpp_itpdsl',offset=offset-defaultLimit) 
    else:
        prevUrl=url_for('itpp_itpdsl',offset=offset)
        
    lastUrl=url_for('itpp_itpdsl',offset=myOffset*defaultLimit)
    
    # return values to render
    return render_template('itpdsl.html',
                           myRecords=myRecords,
                           nextUrl=nextUrl,
                           prevUrl=prevUrl,
                           firstUrl=firstUrl,
                           lastUrl=lastUrl,
                           totalRecord= myTotal,
                           myOffset=offset,
                           URL_PREFIX=URL_BY_DEFAULT
                           )

@app.route('/itpp_itpmeet/<offset>',methods=["GET"])
def itpp_itpmeet(offset=0):
    
    # delete old file in the server
    if os.path.exists('itpmeet.docx'):
        deleteFile('itpmeet.docx')
    
    # definition of the offset and the limit
    offset=int(offset)
    
    # retrieve the first value and the last value of the set
    firstId= myCollection.find({'section': 'itpmeet'}, {
       'bodysession': 1,'_id': 1, 'section': 1, 'committee1': 1, 'committee2': 1 , 'years': 1}).sort("_id",pymongo.ASCENDING)
    lastId=firstId[offset]["_id"]
    
    # retrieve the set of data
    myTotal = myCollection.find({'section': 'itpmeet'}).count()

    # definition of the default limit
    if myTotal<100 :
        defaultLimit=10
    
    if myTotal >=100 and myTotal <= 1000 :
        defaultLimit=25
        
    if myTotal > 1000:
        defaultLimit=100

    myRecords = myCollection.find({"$and":[{"_id": {"$gte": lastId}},{'section': 'itpmeet'}]}).sort("_id", pymongo.ASCENDING).limit(defaultLimit)

    myOffset=int(myTotal/defaultLimit)
    
    # dynamic url generation
    firstUrl=url_for('itpp_itpmeet',offset=0)
    
    if offset < (myOffset*defaultLimit):
        nextUrl=url_for('itpp_itpmeet',offset=offset+defaultLimit)
    else:
        nextUrl=url_for('itpp_itpmeet',offset=offset)
        
    if offset >= defaultLimit:
        prevUrl=url_for('itpp_itpmeet',offset=offset-defaultLimit) 
    else:
        prevUrl=url_for('itpp_itpmeet',offset=offset)
        
    lastUrl=url_for('itpp_itpmeet',offset=myOffset*defaultLimit)
    
    # return values to render
    return render_template('itpmeet.html',
                           myRecords=myRecords,
                           nextUrl=nextUrl,
                           prevUrl=prevUrl,
                           firstUrl=firstUrl,
                           lastUrl=lastUrl,
                           totalRecord= myTotal,
                           myOffset=offset,
                           URL_PREFIX=URL_BY_DEFAULT
                           )



################## UPDATE ###########################################################

@app.route('/itpp_updateRecord/<recordID>',methods=["POST"]) 
@login_required 
def itpp_updateRecord(recordID):
    
    # Retrieving the values from the form sent
    mySorentry=request.form["sorentry"]
    myDocSymbol=request.form["docsymbol"]
    mySornorm=request.form["sornorm"]
    mySornote=request.form["sornote"]
    
    # Defining and executing the request
    myCollection.update_one(
        {"_id": ObjectId(recordID)},
        {
            "$set": {
                "sorentry":mySorentry,
                "docSymbol":myDocSymbol,
                "sornorm":mySornorm,
                "sornote":mySornote
            }
        }
    )
    
    flash('Congratulations the record {} has been updated !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpsor',offset=0))


@app.route('/itpp_updateRecorditpitsc/<recordID>',methods=["POST"])  
@login_required
def itpp_updateRecorditpitsc(recordID):
    
    # Retrieving the values from the form sent
    myitshead=request.form["itshead"]
    myitssubhead=request.form["itssubhead"]
    myitsentry=request.form["itsentry"]
    mydocsymbol=request.form["docsymbol"]
    myrecord_id=request.form["record_id"]
    
    # Defining and executing the request
    myCollection.update_one(
        {"_id": ObjectId(recordID)},
        {
            "$set": {
                "itshead":myitshead,
                "itssubhead":myitssubhead,
                "itsentry":myitsentry,
                "docsymbol":mydocsymbol,
                "record_id":myrecord_id
            }
        }
    )
    
    flash('Congratulations the record {} has been updated !!! '.format(recordID), 'message')

    # Redirection 
    return redirect(url_for('itpp_itpitsc',offset=0))
    
 


@app.route('/itpp_updateRecorditpitsp/<recordID>',methods=["POST"])  
@login_required
def itpp_updateRecorditpitsp(recordID):
    
    # Retrieving the values from the form sent
    myitshead=request.form["itshead"]
    myitssubhead=request.form["itssubhead"]
    mydocsymbol=request.form["docsymbol"]
    myrecord_id=request.form["record_id"]
    
    # Defining and executing the request
    myCollection.update_one(
        {"_id": ObjectId(recordID)},
        {
            "$set": {
                "itshead":myitshead,
                "itssubhead":myitssubhead,
                "docsymbol":mydocsymbol,
                "record_id":myrecord_id
            }
        }
    )
    
    flash('Congratulations the record {} has been updated !!! '.format(recordID), 'message')

    # Redirection 
    return redirect(url_for('itpp_itpitsp',offset=0))



@app.route('/itpp_updateRecorditpitss/<recordID>',methods=["POST"])  
@login_required
def itpp_updateRecorditpitss(recordID):
    
    # Retrieving the values from the form sent
    myitshead=request.form["itshead"]
    myitssubhead=request.form["itssubhead"]
    myitsentry=request.form["itsentry"]
    mydocsymbol=request.form["docsymbol"]
    myrecord_id=request.form["record_id"]
    
    # Defining and executing the request
    myCollection.update_one(
        {"_id": ObjectId(recordID)},
        {
            "$set": {
                "itshead":myitshead,
                "itssubhead":myitssubhead,
                "itsentry":myitsentry,                
                "docsymbol":mydocsymbol,
                "record_id":myrecord_id
            }
        }
    )
    
    flash('Congratulations the record {} has been updated !!! '.format(recordID), 'message')

    # Redirection
    return  redirect(url_for('itpp_itpitss',offset=0))


@app.route('/itpp_updateRecorditpres/<recordID>',methods=["POST"])  
@login_required
def itpp_updateRecorditpres(recordID):
    
    # Retrieving the values from the form sent
    myainumber=request.form["ainumber"]
    mybodysession=request.form["bodysession"]
    myrecord_id=request.form["record_id"]
    mymeeting=request.form["meeting"]
    mysection=request.form["section"]
    mytitle=request.form["title"]
    myvotedate=request.form["votedate"]
    myvote=request.form["vote"]
    mysubject=request.form["subject"]
    mysubjectsubtitle=request.form["subjectsubtitle"]
    
    # Defining and executing the request
    myCollection.update_one(
        {"_id": ObjectId(recordID)},
        {
            "$set": {
                "ainumber":myainumber,
                "bodysession":mybodysession,          
                "record_id":myrecord_id,
                "meeting":mymeeting,
                "section":mysection,
                "title":mytitle,
                "votedate":myvotedate,                
                "vote":myvote,
                "subject":mysubject,
                "subjectsubtitle":mysubjectsubtitle             
            }
        }
    )
    
    flash('Congratulations the record {} has been updated !!! '.format(recordID), 'message')

    # Redirection
    return  redirect(url_for('itpp_itpres',offset=0))


@app.route('/itpp_updateRecorditpsubj/<recordID>',methods=["POST"])  
@login_required
def itpp_updateRecorditpsubj(recordID):
    
    # Retrieving the values from the form sent
    mySection=request.form["section"]
    myBodySession=request.form["bodysession"]
    myHead=request.form["head"]
    mySubHeading=request.form["subheading"]

    # Defining and executing the request
    myCollection.update_one(
        {"_id": ObjectId(recordID)},
        {
            "$set": {
                "section":mySection,          
                "bodysession":myBodySession,
                "head":myHead,
                "subheading":mySubHeading,         
            }
        }
    )
    
    flash('Congratulations the record {} has been updated !!! '.format(recordID), 'message')

    # Redirection
    return  redirect(url_for('itpp_itpsubj',offset=0))


@app.route('/itpp_updateRecorditpdsl/<recordID>',methods=["POST"])  
@login_required
def itpp_updateRecorditpdsl(recordID):
    
    # Retrieving the values from the form sent
    mySection=request.form["section"]
    myCommittee=request.form["committee"]
    mySeries=request.form["series"]
    myDocSymbol=request.form["docsymbol"]

    # Defining and executing the request
    myCollection.update_one(
        {"_id": ObjectId(recordID)},
        {
            "$set": {
                "section":mySection,          
                "committee":myCommittee,
                "series":mySeries,  
                "docsymbol":myDocSymbol       
            }
        }
    )
    
    flash('Congratulations the record {} has been updated !!! '.format(recordID), 'message')

    # Redirection
    return  redirect(url_for('itpp_itpdsl',offset=0))

@app.route('/itpp_updateRecorditpmeet/<recordID>',methods=["POST"])  
@login_required
def itpp_updateRecorditpmeet(recordID):
    
    # Retrieving the values from the form sent
    mySection=request.form["section"]
    myCommittee1=request.form["committee1"]
    myCommittee2=request.form["committee2"]
    myYear=request.form["years"]

    # Defining and executing the request
    myCollection.update_one(
        {"_id": ObjectId(recordID)},
        {
            "$set": {
                "section":mySection,          
                "committee1":myCommittee1,
                "committee2":myCommittee2,  
                "years":myYear       
            }
        }
    )
    
    flash('Congratulations the record {} has been updated !!! '.format(recordID), 'message')

    # Redirection
    return  redirect(url_for('itpp_itpdsl',offset=0))

################## DELETION ###########################################################

@app.route('/itpp_deleteRecord/<recordID>',methods=["POST"])  
@login_required
def itpp_deleteRecord(recordID):
    
    # Defining and executing the request
    myCollection.delete_one({"_id": ObjectId(recordID)})
    
    flash('Congratulations the record {} has been deleted !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpsor',offset=0))

@app.route('/itpitsc_deleteRecord/<recordID>',methods=["POST"])  
@login_required
def itpitsc_deleteRecord(recordID):
    
    # Defining and executing the request
    myCollection.delete_one({"_id": ObjectId(recordID)})
    
    flash('Congratulations the record {} has been deleted !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpitsc',offset=0))

@app.route('/itpitsp_deleteRecord/<recordID>',methods=["POST"])  
@login_required
def itpitsp_deleteRecord(recordID):
    
    # Defining and executing the request
    myCollection.delete_one({"_id": ObjectId(recordID)})
    
    flash('Congratulations the record {} has been deleted !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpitsp',offset=0))


@app.route('/itpitss_deleteRecord/<recordID>',methods=["POST"])  
@login_required
def itpitss_deleteRecord(recordID):
    
    # Defining and executing the request
    myCollection.delete_one({"_id": ObjectId(recordID)})
    
    flash('Congratulations the record {} has been deleted !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpitss',offset=0))

@app.route('/itpres_deleteRecord/<recordID>',methods=["POST"])  
@login_required
def itpres_deleteRecord(recordID):
    
    # Defining and executing the request
    myCollection.delete_one({"_id": ObjectId(recordID)})
    
    flash('Congratulations the record {} has been deleted !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpres',offset=0))

@app.route('/itpsubj_deleteRecord/<recordID>',methods=["POST"])  
@login_required
def itpsubj_deleteRecord(recordID):
    
    # Defining and executing the request
    myCollection.delete_one({"_id": ObjectId(recordID)})
    
    flash('Congratulations the record {} has been deleted !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpsubj',offset=0))


@app.route('/itpdsl_deleteRecord/<recordID>',methods=["POST"])  
@login_required
def itpdsl_deleteRecord(recordID):
    
    # Defining and executing the request
    myCollection.delete_one({"_id": ObjectId(recordID)})
    
    flash('Congratulations the record {} has been deleted !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpdsl',offset=0))

@app.route('/itpmeet_deleteRecord/<recordID>',methods=["POST"])  
@login_required
def itpmeet_deleteRecord(recordID):
    
    # Defining and executing the request
    myCollection.delete_one({"_id": ObjectId(recordID)})
    
    flash('Congratulations the record {} has been deleted !!! '.format(recordID), 'message')

    # Redirection to the main page about itpsor
    return redirect(url_for('itpp_itpmeet',offset=0))

################## DOWNLOAD ###########################################################

def deleteFile(filename):
    os.remove(filename) 


###### NEW DOWNLOAD ############

@app.route("/generateWordFile")
@login_required
def generateWordFile(param_title,param_subtitle,body_session,param_section):
    param_title = param_title
    param_subtitle = param_subtitle
    body_session = body_session
    param_section = param_section
    param_name_file_output = param_section
    myTab=body_session.split("/")
    key = '{}-{}-{}.docx'.format(myTab[0]+myTab[1],param_name_file_output,str(math.floor(datetime.utcnow().timestamp())))
 
    if os.environ.get('ZAPPA') == "true":
        if param_section=="itpres":
            response = get_document_async('generateWordDocITPRES', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
        if param_section=="itpsor":
            response = get_document_async('generateWordDocITPSOR', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
        if param_section=="itpitsc":
            response = get_document_async('generateWordDocITPITSC', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
        if param_section=="itpitsp":
            response = get_document_async('generateWordDocITPITSP', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
        if param_section=="itpitss":
            response = get_document_async('generateWordDocITPITSS', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
        if param_section=="itpsubj":
            response = get_document_async('generateWordDocITPSUBJ', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
        if param_section=="itpdsl":
            response = get_document_async('generateWordDocITPDSL', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
        if param_section=="itpmeet":
            response = get_document_async('generateWordDocITPMEET', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
        if param_section=="itpage":
            response = get_document_async('generateWordDocITPAGE', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)

        flash("The document is being generated and will be in the Downloads section shortly.")
        return redirect(request.referrer)

    else:

        if param_section=="itpres":
            document = get_document_async('generateWordDocITPRES', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
  
        if param_section=="itpsor":
            document = get_document_async('generateWordDocITPSOR', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
   
        if param_section=="itpitsc":
            document = get_document_async('generateWordDocITPITSC', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
     
        if param_section=="itpitsp":
            document = get_document_async('generateWordDocITPITSP', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)
     
        if param_section=="itpsubj":
            document = get_document_async('generateWordDocITPSUBJ', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)

        if param_section=="itpitss":
            document = get_document_async('generateWordDocITPITSS', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)

        if param_section=="itpdsl":
            document = get_document_async('generateWordDocITPDSL', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)

        if param_section=="itpmeet":
            document = get_document_async('generateWordDocITPMEET', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)

        if param_section=="itpage":
                    document = get_document_async('generateWordDocITPAGE', param_title, param_subtitle, body_session, param_section, param_name_file_output, key)


        file_stream = io.BytesIO()
        document.save(file_stream)
        file_stream.seek(0)
        return send_file(file_stream, as_attachment=True, attachment_filename=key)

@task(capture_response=True)
def get_document_async(document_name, param_title, param_subtitle, body_session, param_section, param_name_file_output, key):

    try:
        document = globals()[document_name](param_title, param_subtitle, body_session, param_section, param_name_file_output)
        s3_client = boto3.client('s3')
        filename = '/tmp/' + key
        document.save(filename)
        response = s3_client.upload_file(filename, Config.bucket_name, key)
        return True
    except ClientError as e:
        print(e)
        return False
    
    return True

####################################################################################### 

@app.route('/itpp_findRecord/<docSymbol>',methods=["POST"])  
def itpp_findRecord(docSymbol):

    # Defining and executing the request
    myRecord=myCollection.find({"docSymbol": docSymbol})
    if myRecord.count()==0:
        flash('No record found !!! ', 'error')

    # Redirection to the main page about itpsor
    return render_template('itpsor.html',
                           myRecord=myRecord
                           )


####################################################
# WORD DOCUMENTS LIST
####################################################  

@app.route("/files")
@login_required
def list_files():
 
    ############ PROCESS AWS (files created during the period)

    # assign the s3 object

    myS3 = Config.client

    # assign the appropiate bucket
    try:
        myList=s3.list_objects_v2(Bucket=Config.bucket_name)["Contents"]
    except KeyError:
        myList = []

    # definition of some variables

    myFilesNumber=0
    myData=[]

    # function to sort the record 
    def Sort(sub_li): 
        l = len(sub_li) 
        for i in range(0, l): 
            for j in range(0, l-i-1): 
                if (sub_li[j][1] > sub_li[j + 1][1]): 
                    tempo = sub_li[j] 
                    sub_li[j]= sub_li[j + 1] 
                    sub_li[j + 1]= tempo 
        return sub_li 

    # retrieving and building list of records 
    for obj in myList:
        #myRecord.clear()
        myRecord=[]
        myName= obj["Key"]
        myRecord.append(myName)

        myLastModified=obj["LastModified"]
        myRecord.append(myLastModified)

        mySize=obj["Size"]
        myRecord.append(mySize)

        myFilesNumber+=1

        # Add the record to the dataList
        myData.append(myRecord)
        
        print(myData)

    return render_template('generatedfiles.html',myData=Sort(myData),myFilesNumber=myFilesNumber)

@app.route("/files/download/<filename>")
@login_required
def newDownload(filename):    

    s3 = boto3.client('s3')
    try:
        s3_file = s3.get_object(Bucket=Config.bucket_name, Key=filename)
    except:
        abort(404)

    return send_file(s3_file['Body'], as_attachment=True, attachment_filename=filename)

@app.route('/itp/selectSection/',methods=["GET", "POST"])
@login_required
def selectSection():
    sections= lookup_code("section")
    bodysessions = lookup_snapshots()
    

    if request.method == "GET" :
    
        # Returning the view
        results = section_summary()
        
        return render_template('select_section.html',sections=sections,bodysessions=bodysessions,resultsSearch = results)

    else :
         # Calling the logic to generate the section      
        
        process_section(request.form.get('bodysession'),request.form.get('paramSection')) 
        
        # Returning the view
        results = section_summary()
        return render_template('select_section.html',sections=sections,bodysessions=bodysessions,resultsSearch = results)

        """
            results = section_summary()
            #print(results)
            return render_template('select_section.html',sections=sections,bodysessions=bodysessions,resultsSearch = results)
        """

    
@app.route("/wordGeneration",methods=["POST","GET"])
@login_required
def wordGeneration():

    # Setting some Variables

    myMongoURI=Config.connect_string
    myClient = MongoClient(myMongoURI)
    myDatabase=myClient.undlFiles
    myCollection=myDatabase['itp_sample_output_copy']
    listOfBodySession=[]
    listOfSection=[]

    # Queries to fill some data

    bodysessions=myCollection.find({}, {'bodysession': 1}).distinct('bodysession')
    sections=myCollection.find({}, {'section': 1 }).distinct('section')
    if request.method == "GET" :
    

        # Returning the view

        return render_template('wordgeneration.html',sections=sections,bodysessions=bodysessions)

    else :
         # Calling the logic to generate the file        
        generateWordFile(request.form.get('paramTitle'),request.form.get('paramSubTitle'),request.form.get('bodysession'),request.form.get('paramSection'))

        # Returning the view
        return render_template('wordgeneration.html',sections=sections,bodysessions=bodysessions)

####################################################
# START APPLICATION
####################################################  

if __name__=="__main__":
    app.run(debug=True)



