from mongoengine import *
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId
import time
from app.config import Config


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

    meta = {'collection': Config.collection_prefix + 'Itpp_user' }


class Itpp_log(Document):
    """
    Definition of the Itpp_log class
    """
    
    # definition of the list of fields of the class

    logUserName = StringField(max_length=200) # User performing the action
    logDescription = StringField(max_length=500) # Description of the action performed
    logCreationDate = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))) # date of the action performed

    meta = {'collection': Config.collection_prefix + 'Itpp_log' }

class Itpp_snapshot(Document):
    """
    ITP Snapshot model

    An ITP Snapshot definition is a body and session (per spec, we use the 
    Authority# in the submission form). This collection stores the definition
    and each individual record that is generated by the snapshot definition.
    """
    snapshot_name = StringField()
    snapshot_date = DateTimeField()
    body_session_auth = StringField()
    created = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    record = DictField()

    meta = {'collection': Config.collection_prefix + 'Itpp_snapshot'}

class Itpp_rule(EmbeddedDocument):
    '''
    Rule model
    This is still very inadequate and doesn't really allow us to do much
    It will require a better understanding of the target serialization.
    '''
    id = ObjectIdField(default=ObjectId)
    name = StringField()
    process_order = StringField()
    rule_type = StringField() # e.g., group, sort, filter
    parameters = ListField()

class Itpp_section(EmbeddedDocument):
    """
    Section model

    A section consists of a data source (snapshot) and a collection of rules, 
    such as which fields to display, group, and sort; and any transformations 
    necessary to construct the final output.
    """
    id = ObjectIdField(default=ObjectId)
    name = StringField(unique=True,required=True)
    section_order = IntField()
    data_source = ReferenceField(Itpp_snapshot)
    rules = EmbeddedDocumentListField(Itpp_rule)

    #meta = {'collection': Config.collection_prefix + 'Itpp_section' }

class Itpp_itp(Document):
    """
    This is where the ITP Document building happens. A document is a collection
    of snapshots (typically three), each with its attendant sections and rules.
    """
    name = StringField(max_length=100)
    created = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    updated = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    body = StringField(max_length=10)
    itp_session = StringField(max_length=10)
    body_session_auth = StringField(max_length=32)
    sections = EmbeddedDocumentListField(Itpp_section)

    meta = {'collection': Config.collection_prefix + 'Itpp_document' }

    def get_section_by_id(self, id):
        this_section = next(filter(lambda x: x.id == id, self.sections),None)
        return(this_section)

    def delete_section(self, id):
        print(id)
        this_section = next(filter(lambda x: x.id == id, self.sections),None)
        if this_section is not None:
            self.sections.pop(this_section)
            self.save()
            print('deleted')