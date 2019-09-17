from mongoengine import *
import time
from app.config import DevelopmentConfig as Config

class Itpp_user(Document):
    """
    Definition of the Itpp_user class
    """
    # definition of the list of fields of the class

    userMail = StringField(max_length=200, required=True)
    userUserName = StringField(max_length=200)
    userPassword = StringField(max_length=200)
    userStatus = StringField(max_length=200)
    userCreationDate = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

   # meta = {
   #         'indexes': [
   #             'userMail',
   #             '$userMail',  
   #             '#userMail',
   #             'userPassword',
   #             '$userPassword',  
   #             '#userPassword'
   #         ]
   #     }

class Itpp_log(Document):
    """
    Definition of the Itpp_log class
    """
    
    # definition of the list of fields of the class

    logUserName = StringField(max_length=200) # User performing the action
    logDescription = StringField(max_length=500) # Description of the action performed
    logCreationDate = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))) # date of the action performed
