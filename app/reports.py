from app.config import Config
from app.forms import MissingFieldReportForm, MissingSubfieldReportForm, SelectAuthority
from dlx import DB
from dlx.marc import Bib, Auth, Matcher, OrMatch
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
# These reports are on records that have field 191 and 930$a='UND'

class BibMissingField(Report):
    def __init__(self,tag):
        self.tag = tag
        self.name = 'bib_missing_' + tag
        self.title = 'Missing field - ' + tag
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
            Matcher('930',('a','UND')),
            Matcher(self.tag,modifier='not_exists'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)
        
class BibMissingSubfield(Report):
    def __init__(self,tag,code):
        self.tag = tag
        self.code = code
        self.name = 'bib_missing_' + tag + code
        self.title = 'Missing subfield - {}${}'.format(tag,code)
        self.description = 'Bib records from the given body/session that don\'t have a {}${} field.'.format(tag,code)
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
            Matcher('930',('a','UND')),
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
        self.title = 'Missing field - ' + tag
        self.description = 'Speech records from the given body/session that don\'t have a {} field.'.format(tag)
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
        self.title = 'Missing subfield - {}${}'.format(tag,code)
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
        self.title = 'Missing field - ' + tag
        self.description = 'Vote records from the given body/session that don\'t have a {} field.'.format(tag)
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
        self.title = 'Missing subfield - {}${}'.format(tag,code)
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

class AnyMissingField(Report):
    def __init__(self,tag):
        #super().__init__(self)
        
        self.name = 'any_missing_field'
        self.tag = tag
        self.title = 'Missing Field - ' + tag
        self.description = 'Any records from the given body/session that don\'t have a {} field.'.format(tag)
        self.category = "OTHER"
        self.form_class = SelectAuthority
        
        self.expected_params = ['authority']
       
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a'),
            ('791','a')
        ]
        
    def execute(self,args):
        self.validate_args(args)
    
        body,session = _get_body_session(args['authority'])
    
        bibs = Bib.match(
            OrMatch(
                Matcher('191',('b',body),('c',session)),
                Matcher('791',('b',body),('c',session))
            ),
            Matcher(self.tag,modifier='not_exists'),
            project=[f[0] for f in self.output_fields]
        )
    
        # list of lists
        results = _process_results(bibs,self.output_fields)
        
        # combine 191 and 791
        
        return list(map(lambda row: [row[0], row[1], row[2] + row[3]], results))
        
### For use by the main app to access the reports
     
class ReportList(object):
    reports = [
        
        # predefined reports
        
        # bib category 
       
        # Agenda List
        # Incorrect field - 793 (Committees)
        # Incorrect field - 793 (Plenary)
        # Incorrect field - 991
        # Incorrect session - 191
        # Incorrect subfield - 191$9
        # Missing field - 793
        BibMissingField('793'),
        # Missing field - 991
        BibMissingField('991'),
        # Missing field - 992
        BibMissingField('992'),
        # Missing subfield - 191$9
        BibMissingSubfield('191','9'),
        # Missing subfield - 991$d
        BibMissingSubfield('191','d'),
        
        # Missing subfield value - 991$f X27
        # Missing subfield value - 991$z I
        # Missing subfield value - 999$c t
        
        # speech category 
        
        # Duplicate speech records
        # Field mismatch - 269 & 992
        # Incomplete authorities
        # Incorrect field - 991
        # Incorrect field - 992
        # Incorrect session - 791
        # Missing field - 039
        SpeechMissingField('039'),
        # Missing field - 856
        SpeechMissingField('856'),
        # Missing field - 991
        SpeechMissingField('991'),
        # Missing field - 992
        SpeechMissingField('992'),
        # Missing subfield - 991$d
        SpeechMissingSubfield('991','d'),
    
        # voting category

        # Field mismatch - 269 & 992
        # Incorrect field - 991
        # Incorrect field - 992
        # Incorrect session - 791
        # Missing field - 039
        VotMissingField('039'),
        # Missing field - 856
        VotMissingField('856'),
        # Missing field - 991
        VotMissingField('991'),
        # Missing field - 992
        VotMissingField('992'),
        # Missing subfield - 991$d
        VotMissingSubfield('991','d'),
        
        # other
        
        # Missing field - 930
        AnyMissingField('930'),
        # Missing field - any
        # Missing subfield - any
    ]
    
    def get_by_name(name):
        return next(filter(lambda r: name == r.name, ReportList.reports), None)
        
### exceptions

class AuthNotFound(Exception):
    def __init__(self,msg):
        super().__init__(msg)

### utility functions

def _get_body_session(string):
    try:
        auth_id = int(string)
        auth = Auth.match_id(auth_id)
    except ValueError:
        body,session = string.split('/')
        auth = next(Auth.match(Matcher('190',('b',body+'/'),('c',session))),None)
        
    if auth is None:
        raise AuthNotFound('Session authority not found')
    else:
        body = auth.get_value('190','b')
        session = auth.get_value('190','c')
        
    return (body,session)
    
def _process_results(generator,output_fields):
    results = []
    
    for bib in generator:
        results.append(['||'.join(bib.get_values(*out)) for out in output_fields])
    
    # list of lists
    return results
    
