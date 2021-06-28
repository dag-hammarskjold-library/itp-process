from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form
from wtforms import StringField, IntegerField, PasswordField, BooleanField, SubmitField, SelectField, SelectMultipleField
from wtforms.fields import SelectFieldBase
from wtforms.validators import DataRequired
#from app.models import Itpp_itp, Itpp_section, Itpp_rule, Itpp_snapshot

#class SectionForm(FlaskForm):
'''
name = request.form.get('section_name')
itp_body = request.form.get('body')
itp_session = request.form.get('session')
rules = request.form.get('rules')
'''
#name = StringField('Section Name', validators=[DataRequired()])
#itp_body = StringField('ITP Body', validators=[DataRequired()])
#itp_session = StringField('ITP Session', validators=[DataRequired()])
#rules = SelectField('Rules')

#ItpForm = model_form(Itpp_itp)
#SectionForm = model_form(Itpp_section, field_args={'rules': {SelectField(choices=Itpp_snapshot.objects)}})
#RuleForm = model_form(Itpp_rule)

class SectionForm(FlaskForm):
    
    name = StringField(validators=[DataRequired()])
    section_order = StringField()
    data_source = SelectField(choices=[])
    rules = SelectMultipleField(choices=[])

    def set_choices(self, field, data):
        this_f = getattr(self, field)
        this_f.choices = data

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class MissingFieldReportForm(FlaskForm):
    authority = StringField('Authority', validators=[DataRequired()])
    field = SelectField('Field',choices=[
                                        ('000','000'),('005','005'),('007','007'),('008','008'),
                                        ('010','010'),('019','019'),('020','020'),('022','022'),
                                        ('029','029'),('035','035'),('037','037'),('039','039'),
                                        ('040','040'),('041','041'),('049','049'),('069','069'),
                                        ('079','079'),('089','089'),('091','091'),('099','099'),
                                        ('100','100'),('110','110'),('111','111'),('130','130'),
                                        ('191','191'),('222','222'),('239','239'),('245','245'),
                                        ('246','246'),('247','247'),('249','249'),('250','250'),
                                        ('255','255'),('256','256'),('260','260'),('269','269'),
                                        ('300','300'),('310','310'),('321','321'),('362','362'),
                                        ('440','440'),('490','490'),('495','495'),('500','500'),
                                        ('505','505'),('515','515'),('520','520'),('529','529'),
                                        ('546','546'),('547','547'),('580','580'),('591','591'),
                                        ('592','592'),('593','593'),('594','594'),('595','595'),
                                        ('596','596'),('597','597'),('598','598'),('599','599'),
                                        ('600','600'),('610','610'),('611','611'),('630','630'),
                                        ('650','650'),('700','700'),('710','710'),('711','711'),
                                        ('730','730'),('740','740'),('767','767'),('770','770'),
                                        ('772','772'),('773','773'),('780','780'),('785','785'),
                                        ('789','789'),('791','791'),('793','793'),('830','830'),
                                        ('856','856'),('908','908'),('910','910'),('911','911'),
                                        ('920','920'),('930','930'),('949','949'),('952','952'),
                                        ('955','955'),('967','967'),('991','991'),('992','992'),
                                        ('993','993'),('995','995'),('996','996'),('999','999')]
    ,validators=[DataRequired()])
    
class SelectAuthority(FlaskForm):
    authority = StringField('Authority number or Series symbol (e.g. 896399 or A/74)', validators=[DataRequired()])

class SelectAgendaAuthority(FlaskForm):
    authority = StringField('Authority number or Series symbol (e.g. 896399 or A/74)', validators=[DataRequired()])
    agenda_document = IntegerField('Match this agenda document symbol (e.g. A/74/251)')

class SelectPVRangeAuthority(FlaskForm):
    authority = StringField('Authority number or Series symbol (e.g. 896399 or A/74)')
    pv_min = StringField('Min PV')
    pv_max = StringField('Max PV')

class MissingSubfieldReportForm(FlaskForm):
    authority = StringField('Authority ID', validators=[DataRequired()])
    field = SelectField('Field',choices=[
                                        ('000','000'),('005','005'),('007','007'),('008','008'),
                                        ('010','010'),('019','019'),('020','020'),('022','022'),
                                        ('029','029'),('035','035'),('037','037'),('039','039'),
                                        ('040','040'),('041','041'),('049','049'),('069','069'),
                                        ('079','079'),('089','089'),('091','091'),('099','099'),
                                        ('100','100'),('110','110'),('111','111'),('130','130'),
                                        ('191','191'),('222','222'),('239','239'),('245','245'),
                                        ('246','246'),('247','247'),('249','249'),('250','250'),
                                        ('255','255'),('256','256'),('260','260'),('269','269'),
                                        ('300','300'),('310','310'),('321','321'),('362','362'),
                                        ('440','440'),('490','490'),('495','495'),('500','500'),
                                        ('505','505'),('515','515'),('520','520'),('529','529'),
                                        ('546','546'),('547','547'),('580','580'),('591','591'),
                                        ('592','592'),('593','593'),('594','594'),('595','595'),
                                        ('596','596'),('597','597'),('598','598'),('599','599'),
                                        ('600','600'),('610','610'),('611','611'),('630','630'),
                                        ('650','650'),('700','700'),('710','710'),('711','711'),
                                        ('730','730'),('740','740'),('767','767'),('770','770'),
                                        ('772','772'),('773','773'),('780','780'),('785','785'),
                                        ('789','789'),('791','791'),('793','793'),('830','830'),
                                        ('856','856'),('908','908'),('910','910'),('911','911'),
                                        ('920','920'),('930','930'),('949','949'),('952','952'),
                                        ('955','955'),('967','967'),('991','991'),('992','992'),
                                        ('993','993'),('995','995'),('996','996'),('999','999')]
    ,validators=[DataRequired()])
    subfield = SelectField('SubField',choices=[
                                        ('0','0'),('1','1'),('2','2'),('3','3'),
                                        ('4','4'),('5','5'),('6','6'),('7','7'),
                                        ('8','8'),('9','9'),('a','a'),('b','b'),
                                        ('c','c'),('d','d'),('e','e'),('f','f'),
                                        ('g','g'),('h','h'),('i','i'),('j','j'),
                                        ('k','k'),('l','l'),('m','m'),('n','n'),
                                        ('o','o'),('p','p'),('q','q'),('r','r'),
                                        ('s','s'),('t','t'),('u','u'),('v','v'),
                                        ('w','w'),('x','x'),('y','y'),('z','z')]
    ,validators=[DataRequired()])