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
