import re
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
        self.output_fields = None
    
    def validate_args(self,args):
        for param in self.expected_params:
            if param not in args.keys():
                raise Exception('Expected param "{}" not found'.format(param))
            
    def execute(self,args):
        raise Exception('execute() must be implemented by the subclass')

### Missing field type

class MissingField(Report):
    def __init__(self,tag):
        self.tag = tag
        self.name = '{}_missing_{}'.format(self.type,tag)
        self.title = 'Missing field - ' + tag
        self.description = '{} records from the given body/session that don\'t have a {} field.'.format(self.type.title(),tag)
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.output_fields = [
            ('930','a'),
            ('001',None),
            (self.symbol_field,'a')
        ]
        self.field_names = [('Record Type','Record ID', 'Document Symbol')]
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher(self.symbol_field,('b',body),('c',session)),
            Matcher('930',('a',Regex('^' + self.type_code))),
            Matcher(self.tag,modifier='not_exists'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)

### Missing subfield type

class MissingSubfield(Report):
    def __init__(self,tag,code):
        self.tag = tag
        self.code = code
        self.name = '{}_missing_{}'.format(self.type,tag + code)
        self.title = 'Missing subfield - {}${}'.format(tag,code)
        self.description = '{} records from the given body/session that don\'t have a {} field but no subfield ${}.'.format(self.type.title(),tag,code)
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]
        self.field_names = [('Record Type','Record ID', 'Document Symbol')]
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher(self.symbol_field,('b',body),('c',session)),
            Matcher('930',('a',Regex('^' + self.type_code))),
            Matcher(self.tag,modifier='exists'),
            Matcher(self.tag,(self.code,Regex('^.*')),modifier='not'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)

### 

### Bib reports
# These reports are on records that have field 191 and 930$a='UND'

class BibAgenda(Report):
    # WIP
    def __init__(self):
        self.name = 'agenda_list'
        self.title = 'Agenda list'
        self.description = 'Agenda items from Bib records in the given sesion'
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        #self.output_fields = []
        self.field_names = ['Document Symbol', 'Agenda Item No.', 'Agenda Subject']
        
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher('930',('a',Regex('^UND'))),
            Matcher('991',('d',Regex('^.*'))),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        #return _process_results(bibs,self.output_fields)
        
        results = []
        
        return results

class BibIncorrect793Comm(Report):
    def __init__(self):
        self.name = 'bib_incorrect_793_committees'
        self.title = 'Incorrect field - 793 (Committees)'
        self.description = 'Bib records where 191 starts with "A/C.<comitte number>" and 793$a does not equal the committe number'
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [('191','a')]
        self.field_names = [('Document Symbol')]
        
    def execute(self,args):
        self.validate_args(args)
     
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher('930',('a',Regex('^UND')))
        )
        
        results = []
        for bib in bibs:
            m = re.match('^A/C\.(\d)/', bib.symbol())
            if m and bib.get_value('793','a') != '0' + m[1]:
                results.append(bib) 

        return _process_results(results,self.output_fields)
       
class BibIncorrect793Plen(Report):
    def __init__(self):
        self.name = 'bib_incorrect_793_plenary'
        self.title = 'Incorrect field - 793 (Plenary)'
        self.description = 'Bib records where 191 starts with "A/RES" or "A/session/L." and 793$a does not equal with "PL"'
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [('191','a')]
        self.field_names = [('Document Symbol')]
        
    def execute(self,args):
        self.validate_args(args)
     
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher('930',('a',Regex('^UND')))
        )
        
        results = []
        for bib in bibs:
            if re.match('^A/RES/',bib.symbol()) or re.match('^A/{}/L\.'.format(session), bib.symbol()):
                if bib.get_value('793','a') != 'PL':
                    results.append(bib) 

        return _process_results(results,self.output_fields)

class BibMissingField(MissingField):
    def __init__(self,tag):
        self.type = 'bib'
        self.category = 'BIB'
        self.type_code = 'UND'
        self.symbol_field = '191'
        
        super().__init__(tag)
        
class BibMissingSubfield(MissingSubfield):
    def __init__(self,tag,code):
        self.type = 'bib'
        self.category = 'BIB'
        self.type_code = 'UND'
        self.symbol_field = '191'
        
        super().__init__(tag,code)
        
### Speech reports
# These reports are on records that have 791 and 930="ITS"
class SpeechMissingField(MissingField):
    def __init__(self,tag):
        self.type = 'speech'
        self.category = 'SPEECH'
        self.type_code = 'ITS'
        self.symbol_field = '791'
        
        super().__init__(tag)
        
class SpeechMissingSubfield(MissingSubfield):
    def __init__(self,tag,code):
        self.type = 'speech'
        self.category = 'SPEECH'
        self.type_code = 'ITS'
        self.symbol_field = '791'
        
        super().__init__(tag,code)

### Vote reports
# These reports are on records that have 791 and 930="VOT"
class VoteMissingField(MissingField):
    def __init__(self,tag):
        self.type = 'vote'
        self.category = 'VOTING'
        self.type_code = 'VOT'
        self.symbol_field = '791'
        
        super().__init__(tag)

class VoteMissingSubfield(MissingSubfield):
    def __init__(self,tag,code):
        self.type = 'vote'
        self.category = 'VOTING'
        self.type_code = 'VOT'
        self.symbol_field = '791'
        
        super().__init__(tag,code)
        
        
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
        
        self.field_names = [('Record Type','Record ID', 'Document Symbol')]
        
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
        #BibAgenda(), #WIP
        # Incorrect field - 793 (Committees)
        BibIncorrect793Comm(),
        # Incorrect field - 793 (Plenary)
        BibIncorrect793Plen(),
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
        BibMissingSubfield('991','d'),
        
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
        VoteMissingField('039'),
        # Missing field - 856
        VoteMissingField('856'),
        # Missing field - 991
        VoteMissingField('991'),
        # Missing field - 992
        VoteMissingField('992'),
        # Missing subfield - 991$d
        VoteMissingSubfield('991','d'),
        
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

class InvalidInput(Exception):
    def __init__(self,msg):
        super().__init__(msg)

### utility functions

def _get_body_session(string):
    try:
        auth_id = int(string)
        auth = Auth.match_id(auth_id)
    except ValueError:
        try:
            body,session = string.split('/')
            auth = next(Auth.match(Matcher('190',('b',body+'/'),('c',session))),None)
        except ValueError:
            raise InvalidInput('Invalid session')
        
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
    
