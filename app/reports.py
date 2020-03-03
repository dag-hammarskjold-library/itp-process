import re
from app.forms import MissingFieldReportForm, MissingSubfieldReportForm, SelectAuthority
from dlx.marc import Bib, Auth, Matcher, OrMatch, BibSet, QueryDocument, Condition
from bson.regex import Regex

#DB.connect(Config.connect_string)

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
        self.field_names = ['Record Type','Record ID', 'Document Symbol']
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Condition(self.symbol_field,('b',body),('c',session)),
            Condition('930',('a',Regex('^' + self.type_code))),
            Condition(self.tag,modifier='not_exists'),
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
            (self.symbol_field,'a')
        ]
        self.field_names = ['Record Type','Record ID', 'Document Symbol']
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Condition(self.symbol_field,('b',body),('c',session)),
            Condition('930',('a',Regex('^' + self.type_code))),
            Condition(self.tag,modifier='exists'),
            Condition(self.tag,(self.code,Regex('^.*')),modifier='not'),
            project=[f[0] for f in self.output_fields]
        )
        
        # list of lists
        return _process_results(bibs,self.output_fields)

### 

### Bib reports
# These reports are on records that have field 191 and 930$a='UND'

class BibAgenda(Report):
    def __init__(self):
        self.name = 'agenda_list'
        self.title = 'Agenda list'
        self.description = 'Agenda items from Bib records in the given session'
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [('191', 'a'), ('991', 'b'), ('991', 'd')]
        self.field_names = ['Document Symbol', 'Auth#', 'Agenda Item No.', 'Agenda Subject']
        
    def execute(self,args):
        self.validate_args(args)
        
        body, session = _get_body_session(args['authority'])
        
        bibset = BibSet.from_query(
            QueryDocument(
                Condition('191',('b',body),('c',session)),
                Condition('930',('a',Regex('^UND'))),
                Condition('991',('d',Regex('^.*'))),
            ),
            projection={'191': 1, '991': 1}
        )
        
        results = []
         
        for bib in bibset:
            sym = '; '.join(bib.get_values('191', 'a'))

            for field in bib.get_fields('991'):
                results.append([sym, field.get_xrefs()[0], field.get_value('b'), field.get_value('d')])

        return results
        
class BibIncorrect793Comm(Report):
    def __init__(self):
        self.name = 'bib_incorrect_793_committees'
        self.title = 'Incorrect field - 793 (Committees)'
        self.description = 'Bib records where 191 starts with "A/C.<committee number>" and 793$a does not equal the committe number'
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [('191','a')]
        self.field_names = ['Document Symbol']
        
    def execute(self,args):
        self.validate_args(args)
     
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Condition('191',('b',body),('c',session)),
            Condition('930',('a',Regex('^UND'))),
            project = ['191','793']
        )
        
        results = []
        for bib in bibs:
            m = re.match(r'^A/C\.(\d)/', bib.symbol())
            if m and bib.get_value('793','a') != '0' + m.group(1):
                results.append(bib) 

        return _process_results(results,self.output_fields)
       
class BibIncorrect793Plen(Report):
    def __init__(self):
        self.name = 'bib_incorrect_793_plenary'
        self.title = 'Incorrect field - 793 (Plenary)'
        self.description = 'Bib records where 191 starts with "A/RES" or "A/<session>/L." and 793$a does not equal with "PL"'
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [('191','a')]
        self.field_names = ['Document Symbol']
        
    def execute(self,args):
        self.validate_args(args)
     
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Condition('191',('b',body),('c',session)),
            Condition('930',('a',Regex('^UND'))),
            project = ['191','793']
        )
        
        results = []
        for bib in bibs:
            if re.match(r'^A/RES/',bib.symbol()) or re.match(r'^A/.+/L\.', bib.symbol()):
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

class BibIncorrect991(Report):
    def __init__(self):
        # WIP
        # S/PV symbols are not implemented becasue no there was no criteria provided for detecting session
        # This implenetation does not acount for double-symboled records at this time. todo.
        
        self.name = 'bib_incorrect_991'
        self.title = 'Incorrect field - 991'
        self.description = 'Bib records with a 991 that does not contain the correct agenda document symbol'
        self.category = "BIB"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [('191', 'a'), ('991', 'a'), ('991', 'b'), ('991', 'c'), ('991', 'd'), ('991', 'e')]
        self.field_names = ['191$a', '991$a', '991$b', '991$c', '991$d', '991$e']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        bibset = BibSet.from_query(
            QueryDocument(
                Condition('191', {'b': body, 'c': session}),
                Condition('930', {'a': Regex('^UND')}),
            ),
            projection={'191': 1, '991': 1}
        )
        
        results = []
        
        def sc_convert(year):
            return str(int(year) - 1945)
            
        for bib in bibset:
            sym = bib.get_value('191', 'a')
            sparts = sym.split('/')
            body = sparts[0]
                                
            if body == 'A':
                if sparts[1][0:1] == 'C' or sparts[1] in ['RES', 'INF', 'BUR']: 
                    year = sparts[2]
                else:
                    year = sparts[1]
            elif body == 'S':
                if sparts[1][:2] == 'PV':
                    continue
                elif sparts[1] in ['Agenda', 'PRST']:
                    year = sparts[2]
                elif sparts[1]== 'RES':
                    match = re.search(r'\((.+)\)', sym)
                    year = match.group(1)
                elif re.match(r'\d\d\d\d$', sparts[1]):
                    year = sparts[1]
                else:
                    continue
                    
                session = sc_convert(year)
            elif body == 'E':
                if sparts[1]== 'RES': 
                    session = sparts[2]
                else:
                    session = sparts[1]
            else:
                continue
            
            for val in bib.get_values('991', 'a'):
                aparts = val.split('/')
                
                if '/'.join(aparts[0:2]) != '/'.join([body, session]):                
                    row = bib.get_values('991', 'a', 'b', 'c', 'd', 'e')
                    row.insert(0, bib.get_value('191', 'a'))
                    results.append(row)

        return results

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

class VoteReport(Report):
    def __init__(self):
        self.type = 'vote'
        self.category = 'VOTING'
        self.type_code = 'VOT'
        self.symbol_field = '791'

class VoteIncorrectSession(VoteReport):
    def __init__(self):
        super().__init__()
        
        self.name = 'vote_incorrect_session'
        self.title = 'Incorrect session - 791'
        self.description = 'Vote records that have the incorrect session in 791$r'
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.output_fields = [('001',None),('791','a')]
        self.field_names = ['Record ID','791']
        
    def execute(self,args):
        self.validate_args(args)
     
        body,session = _get_body_session(args['authority'])
        
        bibs = Bib.match(
            Condition('791',('b',body),('c',session)),
            Condition('930',('a','VOT')),
            project=['001','791']
        )
        
        results = []
        for bib in bibs:
            for symbol in bib.get_values('791','a'):
               
                match = re.match(r'^A/RES/(\d+)',symbol)
                if match:
                    check = bib.get_value('791','r')
                    if check != 'A' + match.group(1):                        
                        results.append(bib)
                        break
                    
                match = re.match(r'^S/RES/(\d{4})',symbol)
                if match: 
                    check = bib.get_value('791','r')
                    if check != 'S' + match.group(1):
                        results.append(bib)
                        break
                    
                match = re.match(r'^E/RES/(\d{4})',symbol)
                if match:
                    check = bib.get_value('791','r')
                    if check != 'E' + match.group(1):
                        results.append(bib)
                        break

        return _process_results(results,self.output_fields)

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
        
        self.field_names = ['Record Type','Record ID', 'Document Symbol']
        
    def execute(self,args):
        self.validate_args(args)
    
        body,session = _get_body_session(args['authority'])
    
        bibs = Bib.match(
            OrMatch(
                Condition('191',('b',body),('c',session)),
                Condition('791',('b',body),('c',session))
            ),
            Condition(self.tag,modifier='not_exists'),
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
        BibAgenda(), #WIP
        # Incorrect field - 793 (Committees)
        BibIncorrect793Comm(),
        # Incorrect field - 793 (Plenary)
        BibIncorrect793Plen(),
        # Incorrect field - 991
        BibIncorrect991(),
        # Incorrect session - 191
        # Incorrect subfield - 191$9
        # Missing field - 793
        BibMissingField('793'), # *** disable as per VW
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
        VoteIncorrectSession(),
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
    def __init__(self, msg):
        super().__init__(msg)

class InvalidInput(Exception):
    def __init__(self, msg):
        super().__init__(msg)

### utility functions

def _get_body_session(string):
    try:
        auth_id = int(string)
        auth = Auth.match_id(auth_id)
    except ValueError:
        try:
            body,session = string.split('/')
            auth = next(Auth.match(Condition('190',('b',body+'/'),('c',session))),None)
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
        results.append(['; '.join(bib.get_values(*out)) for out in output_fields])
    
    # list of lists
    return results
    
