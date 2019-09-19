from mongoengine import *
import time
from app.config import DevelopmentConfig as Config

class Itpp_user(Document):
    """
    Definition of the Itpp_user class
    """
    # definition of the list of fields of the class

    email = StringField(max_length=200, required=True, unique=True)
    username = StringField(max_length=200)
    password = StringField(max_length=200)
    status = StringField(max_length=200)
    created = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    updated = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

class Itpp_log(Document):
    """
    Definition of the Itpp_log class
    """
    
    # definition of the list of fields of the class

    logUserName = StringField(max_length=200) # User performing the action
    logDescription = StringField(max_length=500) # Description of the action performed
    logCreationDate = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))) # date of the action performed
