from app.config import Config
from app.forms import MissingFieldReportForm, MissingSubfieldReportForm, SelectAuthority
from dlx import DB, Bib, Auth
from dlx.marc import Matcher
from bson.regex import Regex

DB.connect(Config.connect_string)

### Report base class. Not for use.

class Report(object):
    def __init__(self):
        # these attributes must be implmeted by the subclass
        self.name = None
        self.title = None
        self.description = None
        self.category = None
        self.form_class = None
        self.expected_params = None
        self.stored_criteria = None
        self.output_fields = None
           
    def validate_args(self,args):
        for param in self.expected_params:
            if param not in args.keys():
                raise Exception('Expected param "{}" not found'.format(param))
            
            
    def execute(self,args):
        raise Exception('execute() must be implemented by the subclass')


### Bib reports
# These reports are on records that have field 191

class BibMissingField(Report):
    def __init__(self,tag):
        self.tag = tag
        self.name = 'bib_missing_' + tag
        self.title = 'Bibs Missing ' + tag
        self.description = 'Bib records from the given body/session that don\'t have a {} field.'.format(tag)
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher(self.tag,modifier='not_exists'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)
        
class BibMissingSubfield(Report):
    def __init__(self,tag,code):
        self.tag = tag
        self.code = code
        self.name = 'speech_missing_' + tag + code
        self.title = 'Speech records Missing {}${}'.format(tag,code)
        self.description = 'Speech records from the given body/session that don\'t have a {}${} field.'.format(tag,code)
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher(self.tag,(self.code,Regex('^.*')),modifier='not'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)


### Speech reports
# These reports are on records that have 791 and 930="ITS"

class SpeechMissingField(Report):
    def __init__(self,tag):
        self.tag = tag
        self.name = 'speech_missing_' + tag
        self.title = 'Speech records Missing ' + tag
        self.description = 'Speech records from the given body/session that don\'t have a {} field.'.format(tag)
        self.category = "SPEECH"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('791',('b',body),('c',session)),
            Matcher('930',('a','ITS')),
            Matcher(self.tag,modifier='not_exists'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)
        
class SpeechMissingSubfield(Report):
    def __init__(self,tag,code):
        self.tag = tag
        self.code = code
        self.name = 'speech_missing_' + tag + code
        self.title = 'Speech records Missing {}${}'.format(tag,code)
        self.description = 'Speech records from the given body/session that don\'t have a {}${} field.'.format(tag,code)
        self.category = "SPEECH"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('791','a')
        ]
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('791',('b',body),('c',session)),
            Matcher('930',('a','ITS')),
            Matcher(self.tag,(self.code,Regex('^.*')),modifier='not'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)


### Vote reports
# These reports are on records that have 791 and 930="VOT"

class VotMissingField(Report):
    def __init__(self,tag):
        self.tag = tag
        self.name = 'vot_missing_' + tag
        self.title = 'Votes Missing ' + tag
        self.description = 'Vote records from the given body/session that don\'t have a {} field.'.format(tag)
        self.category = "VOTING"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('791',('b',body),('c',session)),
            Matcher('930',('a','VOT')),
            Matcher(self.tag,modifier='not_exists'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)

class VotMissingSubfield(Report):
    def __init__(self,tag,code):
        self.tag = tag
        self.code = code
        self.name = 'vot_missing_' + tag + code
        self.title = 'Votes Missing {}${}'.format(tag,code)
        self.description = 'Vote records from the given body/session that don\'t have a {}${} field.'.format(tag,code)
        self.category = "VOTING"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('791','a')
        ]
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('791',('b',body),('c',session)),
            Matcher('930',('a','VOT')),
            Matcher(self.tag,(self.code,Regex('^.*')),modifier='not'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)
        
        
### "Other" reports

class BibMissingFieldReport(Report):
    def __init__(self):
        #super().__init__(self)
        
        self.name = 'bib_missing_field'
        self.title = 'Bib Missing Field Report'
        self.description = 'This report returns bib numbers and document symbols based on a particular body and session for the specified field.'
        self.category = "OTHER"
        self.form_class = MissingFieldReportForm
        
        self.expected_params = ['authority','field']
       
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]

    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        tag = args['field']
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher(tag,modifier='not_exists'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)
        
class BibMissingSubfieldReport(Report):
    def __init__(self):
        self.name = 'bib_missing_subfield'
        self.title = 'Bib Missing Subfield Report'
        self.description = 'This report returns bib numbers and document symbols based on a particular body and session for the specified field and subfield.'
        self.category = "OTHER"
        self.form_class = MissingSubfieldReportForm
        
        self.expected_params = ('authority','field','subfield')
       
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]
        
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
    
        tag = args['field']
        subfield = args['subfield']
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher(tag,(subfield,Regex('^.')),modifier='not'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)


### For use by the main app to access the reports

class ReportList(object):
    reports = [

       # predefined reports

       # bib category 
       BibMissingField('793'),
       BibMissingField('991'),
       BibMissingField('992'),
       BibMissingSubfield('191','9'),
       BibMissingSubfield('991','d'),
       
       # speech category 
       SpeechMissingField('039'),
       SpeechMissingField('856'),
       SpeechMissingField('991'),
       SpeechMissingField('992'),
       
       # voting category 
       VotMissingSubfield('991','d'),
       VotMissingField('039'),
       VotMissingField('856'),
       VotMissingField('991'),
       VotMissingField('992'),
       VotMissingSubfield('991','d'),
       
       # report to customize reports

       BibMissingFieldReport(),
       BibMissingSubfieldReport(),
    ]
    
    def get_by_name(name):
        return next(filter(lambda r: name == r.name, ReportList.reports), None)
        
        
### utility functions

def _get_body_session(string):
    try:
        auth_id = int(string)
        auth = Auth.match_id(auth_id)
    except ValueError:
        body,session = string.split('/')
        auth = next(Auth.match(Matcher('190',('b',body+'/'),('c',session))),None)
        
    if auth is None:
        raise Exception('Auth not found')
    else:
        body = auth.get_value('190','b')
        session = auth.get_value('190','c')
        
    return (body,session)
    
def _process_results(generator,output_fields):
    results = []
    
    for bib in generator:
        results.append([bib.get_value(*out) for out in output_fields])
    
    # list of lists
    return results
    
