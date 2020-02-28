import logging
from flask import Flask, render_template, request, abort, jsonify, Response, session,url_for,redirect,flash
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from requests import get
import boto3, re, os, pymongo
from mongoengine import connect,disconnect
from app.reports import ReportList, AuthNotFound, InvalidInput, _get_body_session
from app.snapshot import Snapshot
from flask_mongoengine.wtf import model_form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from app.models import Itpp_log, Itpp_user, Itpp_section, Itpp_rule, Itpp_snapshot, Itpp_itp
from app.forms import LoginForm, SectionForm
from datetime import datetime
from werkzeug.utils import secure_filename
from app.config import Config
from dlx import DB
from dlx.marc import Bib, Auth, BibSet, QueryDocument,Condition,Or
from bson.json_util import dumps
import bson
import time, json
from zappa.asynchronous import task


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

@app.route("/itpp_itps/<itp_id>/sections/<section_id>/execute")
@login_required
def execute_section(itp_id, section_id):
    itp = Itpp_itp.objects.get(id=itp_id, sections__id=section_id)
    return jsonify({
        'itp_id': str(itp.id),
        'section_id': str(section_id),
        'rules': itp.sections.rules
    })

@app.route("/itpp_itps/<itp_id>/sections/<section_id>/delete")
@login_required
def delete_section(itp_id,section_id):
    try:
        itp = Itpp_itp.objects(id=itp_id)[0]
        itp.update(pull__sections__id=bson.ObjectId(section_id))
        return redirect(url_for('update_itpp_itp', id=itp_id, mode='sections'))

        '''
        return json.dumps({
            "success":True, 
            "redirect": url_for('update_itpp_itp', id=itp_id, mode='sections')
        }), 200, {'ContentType':'application/json'}
        '''
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
# START APPLICATION
####################################################  

if __name__=="__main__":
    app.run(debug=True)