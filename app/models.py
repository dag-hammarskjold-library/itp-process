from mongoengine import *
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import time
from app.config import DevelopmentConfig as Config

class Itpp_user(UserMixin, Document):
    """
    Definition of the Itpp_user class
    """
    # definition of the list of fields of the class

    email = StringField(max_length=200, required=True, unique=True)
    username = StringField(max_length=200)
    password_hash = StringField(max_length=200)
    status = StringField(max_length=200)
    created = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    updated = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Itpp_log(Document):
    """
    Definition of the Itpp_log class
    """
    
    # definition of the list of fields of the class

    logUserName = StringField(max_length=200) # User performing the action
    logDescription = StringField(max_length=500) # Description of the action performed
    logCreationDate = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))) # date of the action performed

class Itpp_rule(EmbeddedDocument):
    '''
    This is an attempt to model the basic shape of a "rule", which is then 
    embedded into the Section document. For ease of use, it is assumed here 
    that command refers to a DLX function name, so that we can minimize the 
    code necessary to actually run the command.
    For instance:
    module = 'Bib'
    command = 'match_fields'
    paramaters = '191,('b','A'),('c','72')
    Would eventually unpack to:
    
    Bib.match_fields(('191,('b','A'),('c','72')))
    This is achieved via getattr. Assuming section is an Itpp_section object:
    for rule in section.rules:
        result = getattr(rule.module, rule.command)(rule.parameters)
    '''
    name = StringField()
    module = StringField
    command = StringField()
    parameters = StringField()

class Itpp_section(Document):
    """
    This provides fields for section building in the ITP Process app
    It has an embedded document list to hold a defined set of rules that apply
    to the section.
    """
    name = StringField()
    itp_body = StringField()
    itp_session = StringField()
    rules = EmbeddedDocumentListField(Itpp_rule)

class Itpp_document(Document):
    itp_body = StringField()
    itp_session = StringField()
    filter_fields = ListField()

class Itpp_snapshot(Document):
    name = StringField()
    documents = EmbeddedDocumentListField(Itpp_document)