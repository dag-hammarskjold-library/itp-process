from mongoengine import connect, Document, StringField, EmbeddedDocumentListField, EmbeddedDocument
from app.config import DevelopmentConfig as Config

class Rule(EmbeddedDocument):
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
    '''
    name = StringField()
    module = StringField
    command = StringField()
    parameters = StringField()

class Section(Document):
    name = StringField()
    body = StringField()
    session = StringField()
    rules = EmbeddedDocumentListField(Rule)

    meta = {'collection': Config.collection_prefix + 'section'}