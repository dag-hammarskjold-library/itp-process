import re
from warnings import warn
from app.forms import MissingFieldReportForm, MissingSubfieldReportForm, SelectAuthority, SelectAgendaAuthority, SelectPVRangeAuthority
from dlx.marc import Bib, Auth, Matcher, OrMatch, BibSet, AuthSet, QueryDocument, Condition, Raw, Or
from dlx.file import File, Identifier
from bson.regex import Regex
from natsort import natsorted
from collections import Counter

### Report base class. Not for use.

class Report(object):
    def __init__(self):
        self.form_class = SelectAuthority
        
        # these attributes must be implemented by the subclasses
        for att in ('name', 'title', 'description', 'category', 'form_class', 'expected_params', 'field_names'):
            if not hasattr(self, att):
                raise Exception('Required attribute "{}" is missing')
    
    def validate_args(self,args):
        for param in self.expected_params:
            if param not in args.keys():
                raise Exception('Expected param "{}" not found'.format(param))
            
    def execute(self,args):
        raise Exception('execute() must be implemented by the subclass')

### Missing field type

class MissingField(Report):
    def __init__(self, tag):
        self.name = '{}_missing_{}'.format(self.type, tag)
        self.title = 'Missing field - ' + tag
        #self.description = '{} records from the given body/session that don\'t have a {} field.'.format(self.type.title(),tag)
        self.description = ''
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.tag = tag

        self.field_names = ['Record Type', 'Record ID', 'Document Symbol']
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, ('b', body), ('c', session)),
            Condition('930', ('a', Regex('^' + self.type_code))),
            Condition(self.tag, modifier='not_exists'),
        )
        
        if self.type == 'bib' and self.tag == '992':
            query.add_condition(Condition(self.symbol_field, ('a', Regex(r'(SR\.|PV\.)'))))
        
        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, '930': 1}):
            results.append([bib.get_value('930', 'a'), bib.id, bib.get_value(self.symbol_field, 'a')])
           
        return results
        
class MissingFields(Report):
    def __init__(self, tags):
        self.name = '{}_missing_fields_{}'.format(self.type, '+'.join(tags))
        self.title = 'Missing fields - {}'.format(' + '.join(tags))
        #self.description = '{} records from the given body/session that don\'t have a {} field.'.format(self.type.title(),tag)
        self.description = ''
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.tags = tags

        self.field_names = ['Record ID', f'{self.symbol_field}$a', '930$a']
        
    def execute(self, args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, ('b', body), ('c', session)),
            Condition('930', ('a', Regex('^' + self.type_code))),
        )
        
        query.add_condition(Or(*[Condition(tag, modifier='not_exists') for tag in self.tags]))
        
        #if self.type == 'bib' and self.tag == '992':
        #    query.add_condition(Condition(self.symbol_field, ('a', Regex(r'(SR\.|PV\.)'))))
        
        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, '930': 1}):            
            results.append([bib.id, bib.get_value(self.symbol_field, 'a'), '; '.join(bib.get_values('930', 'a'))])
           
        return results    
        
### Missing subfield type

class MissingSubfield(Report):
    def __init__(self, tag, code):
        self.name = '{}_missing_{}'.format(self.type,tag + code)
        self.title = 'Missing subfield - {}${}'.format(tag,code)
        self.description = '{} records from the given body/session where {} is missing sufield ${}.'.format(self.type.title(), tag, code)
        self.description = ''

        self.tag = tag
        self.code = code
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.field_names = ['Record Type', 'Record ID', 'Document Symbol']
        
        if self.tag == '991':
            self.field_names += ['991$a', '991$b', '991$c', '991$d', '991$e', '991$z']
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, ('b', body), ('c', session)),
            Condition('930', ('a', Regex('^' + self.type_code))),
            Condition(self.tag, modifier='exists'),
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, self.tag: 1, '930': 1}):
            for field in bib.get_fields(self.tag):
                if not field.get_value(self.code):
                    row = [bib.get_value('930', 'a'), str(bib.id), bib.get_value(self.symbol_field, 'a')]
                    
                    if self.tag == '991':
                        row += [field.get_value(x) for x in ('a','b', 'c', 'd', 'e', 'z')]
                        
                    results.append(row)
                    
        if self.tag == '991':
            results = natsorted(results, key=lambda x: x[4])
                
        return results

### Incorrect sesssion type

class IncorrectSession(Report):
    def __init__(self):
        self.name = '{}_incorrect_session_{}'.format(self.type, self.symbol_field)
        self.title = 'Incorrect session - {}'.format(self.symbol_field)
        self.description = ''
        
        self.form_class = SelectPVRangeAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Record ID', *['{}${}'.format(self.symbol_field, x) for x in ('a', 'b', 'c', 'q', 'r')]]
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        bibset = BibSet.from_query(
            QueryDocument(
                Condition(self.symbol_field, {'b': body, 'c': session}),
                Condition('930', {'a': Regex(f'^{self.type_code}')}),
            ),
            projection={self.symbol_field: 1}
        )
        
        results = []

        for bib in bibset:      
            for field in bib.get_fields(self.symbol_field):
                symbol = field.get_value('a')
                
                bs = field.get_value('b')[0:-1] + field.get_value('c')
                sym_bs = ''.join(_body_session_from_symbol(symbol))
                
                if bs[0] == 'E' and bs[-2:] == '-S':
                    bs = bs.replace('-S', '')
                
                if sym_bs != bs:
                    match = re.search('/(PV\.|SR\.|Agenda/)(\d+)', symbol)
                
                    if match and (args['pv_min'] or args['pv_max']):
                        pv = match.group(2)
                        
                        if pv < args['pv_min'] or pv > args['pv_max']:      
                            results.append([bib.id] + [field.get_value(x) for x in ('a', 'b', 'c', 'q', 'r')])                        
                                    
                    else:
                        results.append(
                            [bib.id, ';'.join(bib.get_values(self.symbol_field, 'a'))] + \
                            [field.get_value(x) for x in ('b', 'c', 'q', 'r')]
                        )

        return results

##
        
class FieldMismatch(Report):
    def __init__(self, tag1, tag2):
        self.tag1 = tag1
        self.tag2 = tag2
        
        self.name = f'{self.type}_mismatch_{tag1}_{tag2}'
        self.title = f'Field mismatch - {tag1} & {tag2}'
        self.description = '' #f'{self.type} records where {tag1} does not match {tag2}'.capitalize()
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Record ID', f'${self.symbol_field}a', f'{self.tag1}$a', f'{self.tag2}$a']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^{}'.format(self.type_code))})
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, self.tag1: 1, self.tag2: 1}):
            if bib.get_value(self.tag1, 'a') != bib.get_value(self.tag2, 'a'):
                results.append([bib.id, bib.get_value(self.symbol_field, 'a'), bib.get_value(self.tag1, 'a'), bib.get_value(self.tag2, 'a')])
                
        return results
        
### incorrect 991
  
class Incorrect991(Report):
    def __init__(self):
        self.name = '{}_incorrect_991'.format(self.type)
        self.title = "Incorrect field - 991"
        self.description = ""
        
        self.form_class = SelectAgendaAuthority
        self.expected_params = ['authority', 'agenda_document']
    
        self.field_names = ['Record ID', self.symbol_field + '$a', '991$a', '991$b', '991$c', '991$d', '991$e']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, {'b': body, 'c': session}),
            Condition('930', {'a': Regex(f'^{self.type_code}')}),
            Condition('991', modifier='exists')
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, '991': 1}):
            for field in bib.get_fields('991'):
                aparts = field.get_value('a').split('/')
                ag_doc = args['agenda_document'].upper()
                syms = bib.get_values(self.symbol_field, 'a')

                if ag_doc:
                    field_doc = field.get_value('a')
                
                    if ag_doc[0] == field_doc[0]:
                        #the agenda is for the same body  
                        if field_doc != ag_doc:
                            row = [field.get_value(x) for x in ('a', 'b', 'c', 'd', 'e')]
                            row.insert(0, '; '.join(syms))
                            row.insert(0, bib.id)
                            results.append(row)
                else:
                    found = 0
                    
                    for sym in syms:
                    
                        if _body_session_from_symbol(sym):
                            xbody, xsession =  _body_session_from_symbol(sym)
                        else:
                            # can't derive session from symbol
                            # get from the user input
                            xbody, xsession = body[0:-1], session
                    
                        if aparts[0:2] == [xbody, xsession]:                
                            found += 1
                    
                    if found == 0: # and bib.get_value(self.symbol_field, 'a')[:4] != 'S/PV':
                        row = [field.get_value(x) for x in ('a', 'b', 'c', 'd', 'e')]
                        row.insert(0, '; '.join(syms))
                        row.insert(0, bib.id)
                        results.append(row)
                
        return results

### Incorrect 992

class Incorrect992(Report):
    def __init__(self):
        self.name = '{}_incorrect_field_992'.format(self.type)
        self.title = "Incorrect field - 992"
        self.description = ""
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Symbol', '{} record ID'.format(self.type), '992$a', 'Bib record ID', '992$a']

    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('791', {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^{}'.format(self.type_code))})
        )
        
        results = []
        check = {}
        
        for bib in BibSet.from_query(query, projection={'791': 1, '992': 1}):
            sym = bib.get_value('791', 'a')
            date1 = bib.get_value('992', 'a')
            date2 = ''
            
            if sym in check:
                date2 = check[sym].get_value('992', 'a')
            else:
                to_check = Bib.find_one(QueryDocument(Condition('191', {'a': sym})).compile(), {'992': 1})
                
                if to_check:
                    date2 = to_check.get_value('992', 'a')
                    check[sym] = to_check
                else:
                    warn(sym + ' not found')
                    check[sym] = Bib()
                    
            if date1 != date2:
                results.append([bib.get_value('791', 'a'), bib.id, date1, check[sym].id, date2])
            
        return results

# Duplicate agenda

class DuplicateAgenda(Report):
    def __init__(self):
        self.name = self.type + '_duplicate_agenda'
        self.title = "Duplicate agenda item"
        self.description = "" #self.type.title() + " records that contain duplicate agenda items (991 field)" 
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']

        self.field_names = ['Record ID', 'Symbol', 'Duplicated 991']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
       
        query = QueryDocument(
            Condition(self.symbol_field, {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^' + self.type_code)})
        )
       
        results = []
       
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, '991': 1}):
            seen = {}
            
            for field in bib.get_fields('991'):
                for subfield in filter(lambda x: x.code == 'a', field.subfields):
                    if subfield.xref in seen:
                        results.append([bib.id, bib.get_value(self.symbol_field, 'a'), field.get_values('a', 'b', 'c', 'd', 'e', 'f', 'z')])
                    else:
                        seen[subfield.xref] = True
                        
        return results

# Missing files

class MissingFiles(Report):
    def __init__(self):
        self.name = self.type + '_missing_files'
        self.title = "Missing files"
        self.description = self.type.capitalize() + " records where the English version of the file was not found"
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.field_names = ['Symbol']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^' + self.type_code)})
        )
        
        results, seen = [], {}
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1}):
            symbol = bib.get_value(self.symbol_field, 'a')
            # ignore "parts"
            base_symbol = re.split('[\[ ][A-Z]\]?', symbol)[0]
            
            if base_symbol in seen:
                continue
            
            if not next(File.find_by_identifier_language(Identifier('symbol', base_symbol), 'EN'), None):
                results.append([symbol])
                
            seen[base_symbol] = True
                
        return results
            
### Auth reports

class AgendaList(Report):
    def __init__(self):
        self.name = 'agenda_list'
        self.title = 'Agenda list'
        self.description = '' #'Agenda items from the given session'
        
        self.category = "OTHER"
        self.form_class = SelectAgendaAuthority
        self.expected_params = ['authority']
        
        self.output_fields = [('191', 'a'), ('991', 'b'), ('991', 'd')]
        self.field_names = ['Document Symbol', 'Auth#', 'Agenda Item No.', 'Agenda Title', 'Agenda Subject', 'Attached to at least one bib']
        
    def execute(self,args):
        self.validate_args(args)
        #body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            #Condition('191', {'a': Regex('^{}{}'.format(body, session))})
            Condition('191', {'a': Regex('^{}'.format(args['authority']))})
        )
        
        results = []
        
        for auth in AuthSet.from_query(query):
            attached = 'Y' if Bib.find_one({'991.subfields.xref': auth.id}) else 'N'
            
            results.append([auth.get_value('191', 'a'), auth.id, auth.get_value('191', 'b'), auth.get_value('191', 'c'), auth.get_value('191', 'd'), attached])

        sorted_results = natsorted(results, key=lambda x: x[2])
        
        return sorted_results

### Bib reports
# These reports are on records that have field 191 and 930$a='UND'

class BibReport(Report):
    def __init__(self):
        self.type = 'bib'
        self.category = 'BIB'
        self.type_code = 'UND'
        self.symbol_field = '191'
     
class BibIncorrect793Comm(Report):
    def __init__(self):
        self.name = 'bib_incorrect_793_committees'
        self.title = 'Incorrect and/or missing field – 793 (Committees)'
        self.description = '191 starts with "A/C.<committee number>" and 793$a does not equal the committe number'

        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Document Symbol']
        
        BibReport.__init__(self)
        
    def execute(self,args):
        self.validate_args(args)
     
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('191', ('b',body), ('c',session)),
            Condition('930', ('a', Regex('^UND'))),
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={'191': 1, '793': 1}):
            m = re.match(r'^A/C\.(\d)/', bib.get_value('191', 'a'))
            
            if m and bib.get_value('793','a') != '0' + m.group(1):
                results.append([bib.get_value('191', 'a')]) 

        return results
       
class BibIncorrect793Plen(BibReport):
    def __init__(self):
        self.name = 'bib_incorrect_793_plenary'
        self.title = 'Incorrect and/or missing field – 793 (Plenary)'
        self.description = '191 starts with "A/RES" or "A/<session>/L." or "A/<session>/PV." and 793$a does not equal "PL"'
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Document Symbol', '793$a']
        
        BibReport.__init__(self)
        
    def execute(self,args):
        self.validate_args(args)
     
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('191', ('b',body), ('c',session)),
            Condition('930', ('a', Regex('^UND'))),
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={'191': 1,'793': 1}):
            if re.match(r'^A/RES/', bib.symbol()) or re.match(r'^A/' + session + r'/(L|PV)\.', bib.symbol()):
                if bib.get_value('793', 'a') != 'PL':
                    results.append([bib.get_value('191', 'a'), bib.get_value('793', 'a')]) 

        return results

class BibMissingField(BibReport, MissingField):
    def __init__(self, tag):
        BibReport.__init__(self)
        MissingField.__init__(self, tag)
        
class BibMissingFields(BibReport, MissingFields):
    def __init__(self, tags):
        BibReport.__init__(self)
        MissingFields.__init__(self, tags)
        
class BibMissingSubfield(BibReport, MissingSubfield):
    def __init__(self, tag, code):
        BibReport.__init__(self)
        MissingSubfield.__init__(self, tag, code)

class BibMissingSubfield991_d(BibMissingSubfield):
    def __init__(self):
        BibReport.__init__(self)
        #MissingSubfield.__init__(self, '991', 'd')
        
        self.name = 'bib_missing_991d'
        self.title = 'Missing subfield - {}${}'.format('991', 'd')
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.field_names = ['Record Type', 'Record ID', 'Document Symbol', '991$a', '991$b', '991$c', '991$d', '991$e', '991$z']
    
    def execute(self,args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, ('b', body), ('c', session)),
            Condition('930', ('a', Regex('^' + self.type_code))),
            Condition('991', modifier='exists')
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, '991': 1, '930': 1}):
            for field in bib.get_fields('991'):
                if not field.get_value('d'):
                    results.append([bib.get_value('930', 'a'), str(bib.id), bib.get_value(self.symbol_field, 'a')] + [field.get_value(x) for x in ('a','b', 'c', 'd', 'e', 'z')])
                
        sorted_results = natsorted(results, key=lambda x: x[4])
        
        return sorted_results

class BibIncorrect991(BibReport, Incorrect991):
    def __init__(self):
        BibReport.__init__(self)
        Incorrect991.__init__(self)
        
class BibIncorrectSession191(BibReport, IncorrectSession):
    def __init__(self):
        BibReport.__init__(self)
        IncorrectSession.__init__(self)
        
class BibIncorrectSubfield191_9(BibReport):
    def __init__(self):
        self.name = 'bib_incorrect_subfield_191_9'
        self.title = 'Incorrect subfield - 191$9'
        self.description = ''
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
       
        self.field_names = ['Record ID', '191$a', '191$9']
        
        BibReport.__init__(self)
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        bibset = BibSet.from_query(
            QueryDocument(
                Condition('191', {'b': body, 'c': session}),
                Condition('930', {'a': Regex('^UND')})
            ),
            projection={'191': 1}
        )
        
        results = []

        for bib in bibset:
            for field in bib.get_fields('191'):
                sym = field.get_value('a')
                flag = False
                
                if sym[:1] == 'A':
                    if field.get_value('9')[:1] != 'G':
                        flag = True
                elif sym[:1] == 'E':
                    if field.get_value('9')[:1] != 'C':
                        flag = True
                elif sym[:1] == 'S':
                    if field.get_value('9')[:1] != 'X':
                        flag = True
                
                if flag is True:
                    results.append([bib.id, field.get_value('a'), field.get_value('9')])
                    
        return results
        
class BibMissing999_c_t(BibReport):
    def __init__(self):
        self.name = 'bib_missing_subfield_value_999_c_t'
        self.title = 'Records not revised' #'Missing subfield value - 999$c t'
        self.description = ''
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
       
        self.field_names = ['Record ID', '191$a', '999$a', '999$b', '999$c']
        
        BibReport.__init__(self)
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        bibset = BibSet.from_query(
            QueryDocument(
                Condition('191', {'b': body, 'c': session}),
                Condition('930', {'a': Regex('^UND')})
            ),
            projection={'191': 1, '999': 1}
        )
        
        results = []
        
        for bib in bibset:
            if len(list(filter(lambda x: x == 't', bib.get_values('999', 'c')))) == 0:
                results.append([bib.id, bib.get_value('191', 'a'), '; '.join(bib.get_values('999', 'a')), '; '.join(bib.get_values('999', 'b')), '; '.join(bib.get_values('999', 'c'))])
            
        return results

class BibMissingSubfieldValue(BibReport):
    def __init__(self, tag, code, value):
        BibReport.__init__(self)
        
        self.name = 'bib_missing_subfield_value_{}_{}_{}'.format(tag, code, value)
        self.title = 'Incorrect and/or missing - {}${} {}'.format(tag, code, value)
        self.description = ''
        
        self.tag = tag
        self.code = code
        self.value = value
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']

        self.field_names = ['Record ID', '191$a']
        
        if self.tag == '991':
            for x in ('a', 'b', 'c', 'd', 'e', 'f', 'z'):
                self.field_names.append('991${}'.format(x))
                                                        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('191', {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^UND')}),
            Condition(self.tag, modifier='exists'),
            #Condition(self.tag, {self.code: self.value}, modifier='not')
        )
        
        if self.tag == '991' and self.code == 'f' and self.value == 'X27':
            query.add_condition(
                Condition('991', {'e': Regex('Participation')})
            )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={'191': 1, self.tag: 1}):
            for field in bib.get_fields(self.tag):
                row = []
                
                if field.get_value(self.code) != self.value:
                    row = [bib.id, '; '.join(bib.get_values('191', 'a'))]
                    
                    if self.tag == '991':
                        if self.code == 'f' and self.value == 'X27' and 'Participation' not in field.get_value('e'):
                            continue
                            
                        for x in ('a', 'b', 'c', 'd', 'e', 'f', 'z'):
                            row.append(field.get_value(x))
                    
                    results.append(row)

        sorted_results = natsorted(results, key=lambda x: x[1])
        
        return sorted_results

class BibMissingAgendaIndicator(BibReport):
    def __init__(self):
        BibReport.__init__(self)
        
        self.name = 'bib_missing_agenda_indicator'
        self.title = 'Agenda item missing indicator'
        self.description = ''
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Record ID', '191$a', '991']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('191', {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^UND')})
        )
        
        results = []
        
        # no query by indicator in dlx yet :\
        for bib in BibSet.from_query(query, projection={'191': 1, '991': 1}):
            for field in bib.get_fields('991'):
                if field.ind1 == ' ':
                    results.append([bib.id, bib.get_value('191', 'a'), field.to_mrk()])
                    
        return results

class BibDuplicateAgenda(BibReport, DuplicateAgenda):
    def __init__(self):
        BibReport.__init__(self)
        DuplicateAgenda.__init__(self)

class BibRepeated515_520(BibReport):
    def __init__(self):
        self.name = 'bib_repeated_515_520'
        self.title = 'Duplicate 515 and 520'
        self.description = 'Bibs with 515 or 520 repeated'
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
       
        self.field_names = ['Record ID', '191$a', '515', '520']
        
        BibReport.__init__(self)

    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])

        bibset = BibSet.from_query(
            QueryDocument(
                Condition('191', {'b': body, 'c': session}),
                Condition('930', {'a': Regex('^UND')}),
                # detect fields that have more than one element in the array
                Or(
                    Raw({'515.1': {'$exists': True}}),
                    Raw({'520.1': {'$exists': True}}),
                )
            ),
            projection={'191': 1, '515': 1, '520': 1}
        )

        results = []

        for bib in bibset:
            results.append(
                [
                    bib.id, bib.get_value('191', 'a'), 
                    '; '.join(bib.get_values('515', 'a')),
                    '; '.join(bib.get_values('520', 'a')),
                ]
            )

        return results
          
class BibEndingWithPeriod515_520(BibReport):
    def __init__(self):
        self.name = 'bib_ending_with_period_515_520'
        self.title = '515 or 520 not ending with period'
        self.description = 'Bibs with 515 or 520 not ending with period'
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
       
        self.field_names = ['Record ID', '191$a', '515', '520']
        
        BibReport.__init__(self)

    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])

        bibset = BibSet.from_query(
            QueryDocument(
                Condition('191', {'b': body, 'c': session}),
                Condition('930', {'a': Regex('^UND')}),
                Or(
                    Raw({'$and': [{'515': {'$exists': True}}, {'515.subfields.value': Regex('[^\.]$')}]}),
                    Raw({'$and': [{'520': {'$exists': True}}, {'520.subfields.value': Regex('[^\.]$')}]})
                )
            ),
            projection={'191': 1, '515': 1, '520': 1}
        )

        results = []

        for bib in bibset:
            results.append(
                [
                    bib.id, bib.get_value('191', 'a'), 
                    '; '.join(bib.get_values('515', 'a')),
                    '; '.join(bib.get_values('520', 'a')),
                ]
            )

        return results

### Speech reports
# These reports are on records that have 791 and 930="ITS"
class SpeechReport(Report):
    def __init__(self):
        self.category = "SPEECH"
        self.type = 'speech'
        self.type_code = 'ITS'
        self.symbol_field = '791'
    
class SpeechMissingField(SpeechReport, MissingField):
    def __init__(self, tag):
        SpeechReport.__init__(self)
        MissingField.__init__(self, tag)
        
class SpeechMissingSubfield(SpeechReport, MissingSubfield):
    def __init__(self,tag,code):
        SpeechReport.__init__(self)
        MissingSubfield.__init__(self, tag, code)

class SpeechDuplicateRecord(SpeechReport):
    def __init__(self):
        SpeechReport.__init__(self)
        
        self.name = 'speech_duplicate_record'
        self.title = "Duplicate records" #"Duplicate speech records"
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']

        self.field_names = ['791$a', '700$a', '710$a', '711$a', '991$d', 'Record IDs'] 
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('791', {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^ITS')})
        )
        
        seen = {}
        results = []
        count = Counter()
        
        for bib in BibSet.from_query(query, projection={'269': 1, '700': 1, '710': 1, '711': 1, '791': 1, '991': 1}):
            vals = [
                bib.get_value('269', 'a'),
                *[str(x) for x in bib.get_xrefs('700')],
                *[str(x) for x in bib.get_xrefs('710')],
                *[str(x) for x in bib.get_xrefs('711')],
                bib.get_value('791', 'a'),
                *[str(x) for x in bib.get_xrefs('991')]
            ]
            
            key = ';'.join(vals)
            
            if key in seen: 
                seen[key].append(bib.id)
            else:
                seen[key] = [bib.id]
            
        for key in seen.keys():
            if len(seen[key]) > 1:
                ids = seen[key]
                bib = Bib.match_id(ids[0])
                results.append([bib.get_value('791', 'a'), bib.get_value('700', 'a'), bib.get_value('710', 'a'), bib.get_value('711', 'a'), bib.get_value('991', 'd'), ids])
        
        return results

class SpeechIncompleteAuthSubfieldG(SpeechReport):
    def __init__(self):
        SpeechReport.__init__(self)
        self.name = 'speech_incomplete_subfield_g'
        self.title = "Incomplete authorities - subfield g"
        self.description = "Child records referenced from speech record fields 700, 710, or 711 that do not have a mother record, or whose mother record is missing 905$a or 915$a"
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']

        self.field_names = ['Child ID', 'Child heading $a', 'Child heading $g', 'Mother ID', 'Mother 905$a', 'Mother 915$a']
    
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('791', {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^ITS')})
        )
        
        auth_ids = []
        
        for bib in BibSet.from_query(query, projection={'700': 1, '710': 1, '711': 1}):
            auth_ids += bib.get_xrefs('700') + bib.get_xrefs('710') + bib.get_xrefs('711')
            
        query = {'_id': {'$in': auth_ids}}
        results = []
        
        for auth in AuthSet.from_query(query, projection={'100': 1, '110': 1, '111': 1, '905': 1, '915': 1}):
            if auth.heading_field.get_value('g'):
                mother = Auth.find_one(
                    QueryDocument(
                        Condition(auth.heading_field.tag, {'a': auth.heading_value('a')}),
                        Condition(auth.heading_field.tag, {'g': auth.heading_value('g')}, modifier='not')
                    ).compile()
                )
                   
                if mother is None:
                    results.append([auth.id, auth.heading_value('a'), auth.heading_value('g'), '', 'N/A', 'N/A'])
                elif not mother.get_field('905') or not mother.get_field('915'):
                    results.append(
                        [
                            auth.id, 
                            auth.heading_value('a'), 
                            auth.heading_value('g'),
                            mother.id,
                            mother.get_value('905', 'a'), 
                            mother.get_value('915', 'a')
                        ]
                    )
                        
        return results

class SpeechIncompleteAuthMother(SpeechReport):
    def __init__(self):
        SpeechReport.__init__(self)
        self.name = 'speech_incomplete_mother'
        self.title = "Incomplete authorities - mother record"
        self.description = "Mother records referenced from speech record fields 700, 710, or 711 that are missing 905 or 915"
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']

        self.field_names = ['Authority ID', 'Heading', 'Heading $g', '905$a', '915$a']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('791', {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^ITS')})
        )
        
        auth_ids = []
        
        for bib in BibSet.from_query(query, projection={'700': 1, '710': 1, '711': 1}):
            auth_ids += bib.get_xrefs('700') + bib.get_xrefs('710') + bib.get_xrefs('711')
            
        query = {'_id': {'$in': auth_ids}}
        results = []
        
        for auth in AuthSet.from_query(query, projection={'100': 1, '110': 1, '111': 1, '905': 1, '915': 1}):
            if auth.heading_field.get_value('g'):
                continue
            
            if not auth.get_field('905') or not auth.get_field('915'):
                results.append([auth.id, auth.heading_value('a'), auth.get_value('g'), auth.get_value('905', 'a'), auth.get_value('915', 'a')])

        return results
    
class SpeechIncorrect991(SpeechReport, Incorrect991):
    def __init__(self):
        SpeechReport.__init__(self)
        Incorrect991.__init__(self)

class SpeechIncorrect992(SpeechReport, Incorrect992):
    def __init__(self):
        SpeechReport.__init__(self)
        Incorrect992.__init__(self)
        
class SpeechIncorrectSession791(SpeechReport, IncorrectSession):
    def __init__(self):    
        SpeechReport.__init__(self)
        IncorrectSession.__init__(self)

class SpeechDuplicateAgenda(SpeechReport, DuplicateAgenda):
    def __init__(self):
        SpeechReport.__init__(self)
        DuplicateAgenda.__init__(self)
   
class SpeechMissingFields(SpeechReport, MissingFields):
    def __init__(self, tags):
        SpeechReport.__init__(self)
        MissingFields.__init__(self, tags)

class SpeechMissingAgendaIndicator(SpeechReport):
    def __init__(self):
        SpeechReport.__init__(self)
        
        self.name = 'speech_missing_agenda_indicator'
        self.title = 'Agenda item missing indicator'
        self.description = ''
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Record ID', '791$a', '991']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition('791', {'b': body, 'c': session}),
            Condition('930', {'a': Regex('^ITS')})
        )
        
        results = []
        
        # no query by indicator in dlx yet :\
        for bib in BibSet.from_query(query, projection={'791': 1, '991': 1}):
            for field in bib.get_fields('991'):
                if field.ind1 == ' ':
                    results.append([bib.id, bib.get_value('791', 'a'), field.to_mrk()])
                    
        return results
        
class SpeechMismatch(SpeechReport, FieldMismatch):
    def __init__(self, tag1, tag2):
        SpeechReport.__init__(self)
        FieldMismatch.__init__(self, tag1, tag2)
        
class Speech039_930(SpeechReport):
    def __init__(self):
        SpeechReport.__init__(self)
        
        self.name = f'{self.type}_mismatch_039_930'
        self.title = f'Field mismatch - 039 & 930'
        self.description = '' #f'{self.type} records where 039 = {self.type_code} and 930 does not'.capitalize()
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Record ID', f'${self.symbol_field}a', f'039$a', f'930$a']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, {'b': body, 'c': session}),
            Condition('039', {'a': Regex('^{}'.format(self.type_code))})
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, '039': 1, '930': 1}):
            
            if self.type_code in bib.get_values('039', 'a'):
                if self.type_code not in bib.get_values('930', 'a'):
                    results.append([bib.id, bib.get_value(self.symbol_field, 'a'), bib.get_value('039', 'a'), bib.get_value('930', 'a')])
                
        return results
    
class Speech700g(SpeechReport):
    def __init__(self):
        SpeechReport.__init__(self)
        
        self.name = '700_g'
        self.title = 'Records with subfield g'
        self.description = 'Records with 700 $g'
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Bib ID', '791$a', 'Authority ID', '700$a', '700$g']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, {'b': body, 'c': session}),
            Condition('039', {'a': Regex('^{}'.format(self.type_code))}),
            Condition('700', {'g': Regex('^.')})
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={'791': 1, '700': 1}):
            results.append([bib.id, bib.get_value('791', 'a'), bib.get_xref('700', 'a'), bib.get_value('700', 'a'), bib.get_value('700', 'g')])
            
        return results

class SpeechMissingFiles(SpeechReport, MissingFiles):
    def __init__(self):
        SpeechReport.__init__(self)
        MissingFiles.__init__(self)

class SpeechMissingFields_700_710(SpeechReport):
    def __init__(self, tags=['700', '710']):
        SpeechReport.__init__(self)
         
        self.name = '{}_missing_fields_{}'.format(self.type, '+'.join(tags))
        self.title = 'Missing fields - {}'.format(' + '.join(tags))
        #self.description = '{} records from the given body/session that don\'t have a {} field.'.format(self.type.title(),tag)
        self.description = ''
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.tags = tags

        self.field_names = ['Record ID', f'{self.symbol_field}$a', '700', '710']
        
    def execute(self, args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, ('b', body), ('c', session)),
            Condition('930', ('a', Regex('^' + self.type_code))),
        )
        
        query.add_condition(Or(*[Condition(tag, modifier='exists') for tag in self.tags]))

        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, '930': 1, '700': 1, '710': 1}):
            if not bib.get_value('700', 'a') or not bib.get_value('710', 'a'):
                results.append([bib.id, bib.get_value(self.symbol_field, 'a'), bib.get_values('700'), bib.get_values('710')])
            
        return results
        
class SpeechParens700(SpeechReport):
    def __init__(self):
        SpeechReport.__init__(self)
        
        self.name = '700_parens'
        self.title = '700 with  parentheses'
        self.description = ''
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Record ID', f'{self.symbol_field}$a', '700$a']
        
    def execute(self, args):
        self.validate_args(args)
        
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, ('b', body), ('c', session)),
            Condition('930', ('a', Regex('^' + self.type_code))),
            Or (
                Condition('700', ('a', Regex(r'\('))),
                #Condition('700', ('g', Regex(r'\(')))
            )
        )
        
        results = []
        
        for bib in BibSet.from_query(query):
            for field in bib.get_fields('700'):
                if '(' in field.get_value('a'): #  or '(' in field.get_value('g'):
                    results.append([bib.id, bib.get_value(self.symbol_field, 'a'), field.get_value('a') + ' ' + field.get_value('g')])
                    
        return results

class SpeechIdentical700_710_791(SpeechReport):
    def __init__(self):    
        SpeechReport.__init__(self)
        self.name = 'speech_identical_700_710_791'
        self.title = 'Identical 700 + 710 + 791'
        self.description = 'Speech records where 700, 710, or 791 exists more than once in the same record with the same value'
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        self.field_names = ['Record ID', f'791', '700', '710']

    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])

        #query = QueryDocument.from_string(f"791__b:'{body}' AND 791__c:'{session}'")
        query = QueryDocument(
            Condition(self.symbol_field, ('b', body), ('c', session)),
            Condition('930', ('a', Regex(f'^{self.type_code}'))),
            # records where these fields have more than one element in the field array
            Raw({'$or': [{'700.1': {'$exists': True}}, {'710.1': {'$exists': True}}, {'791.1': {'$exists': True}}]}),
        )

        results = []

        for bib in BibSet.from_query(query, projection={'700': 1, '710': 1, '791': 1}):
            for tag in ('700', '710', '791'):
                fields = [x.to_mrk() for x in bib.get_fields(tag)]

                for field in fields:
                    # the number of times this field serialized to mrk is repeated
                    count = len(list(filter(lambda x: x == field, fields)))
                    
                    if count > 1:
                        results.append(
                            [
                                bib.id,
                                bib.get_values('791', 'a'),
                                bib.get_values('700', 'a'),
                                bib.get_values('710', 'a')
                            ]
                        )

                        continue

        return results

### Vote reports
# These reports are on records that have 791 and 930="VOT"

class VoteReport(Report):
    def __init__(self):
        self.type = 'vote'
        self.category = 'VOTING'
        self.type_code = 'VOT'
        self.symbol_field = '791'

class VoteIncorrectSession(VoteReport, IncorrectSession):
    def __init__(self):
        VoteReport.__init__(self)
        IncorrectSession.__init__(self)

class VoteMissingField(VoteReport, MissingField):
    def __init__(self, tag):
        VoteReport.__init__(self)
        MissingField.__init__(self, tag)

class VoteMissingSubfield(VoteReport, MissingSubfield):
    def __init__(self,tag,code):
        VoteReport.__init__(self)
        MissingSubfield.__init__(self, tag, code)
        
class VoteMismatch(VoteReport, FieldMismatch):
    def __init__(self, tag1, tag2):
        VoteReport.__init__(self)
        FieldMismatch.__init__(self, tag1, tag2)
  
class VoteIncorrect991(VoteReport, Incorrect991):
    def __init__(self):
        VoteReport.__init__(self)
        Incorrect991.__init__(self)
        
class VoteIncorrect992(VoteReport, Incorrect992):
    def __init__(self):
        VoteReport.__init__(self)
        Incorrect992.__init__(self)

class Vote039_930(VoteReport):
    def __init__(self):
        VoteReport.__init__(self)
        
        self.name = f'{self.type}_mismatch_039_930'
        self.title = f'Field mismatch - 039 & 930'
        self.description = f'{self.type} records where 039 = {self.type_code} and 930 does not'.capitalize()
        
        self.form_class = SelectAuthority
        self.expected_params = ['authority']
        
        self.field_names = ['Record ID', f'${self.symbol_field}a', f'039$a', f'930$a']
        
    def execute(self, args):
        self.validate_args(args)
        body, session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Condition(self.symbol_field, {'b': body, 'c': session})
        )
        
        results = []
        
        for bib in BibSet.from_query(query, projection={self.symbol_field: 1, '039': 1, '930': 1}):
            if self.type_code in bib.get_values('039', 'a'):
                if self.type_code not in bib.get_values('930', 'a'):
                    results.append([bib.id, bib.get_value(self.symbol_field, 'a'), bib.get_value('039', 'a'), bib.get_value('930', 'a')])
                
        return results

class VoteMissingFiles(VoteReport, MissingFiles):
    def __init__(self):
        VoteReport.__init__(self)
        MissingFiles.__init__(self)
    
### "Other" reports

class AnyMissingField(Report):
    def __init__(self,tag):
        #super().__init__(self)
        
        self.name = 'any_missing_field'
        self.tag = tag
        self.title = 'Missing field - ' + tag
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

class VoteAnyMissing930(Report):
    def __init__(self):
        self.name = 'any_missing_930'
        self.tag = '930'
        self.title = 'Missing field - ' + self.tag
        self.description = 'Any records from the given body/session that do not contain a value in 930$a starting with "UND", "ITS", or "VOT".'
        self.category = "VOTING"
        self.form_class = SelectAuthority
        
        self.expected_params = ['authority']    
        self.field_names = ['Record ID', 'Document Symbol', '930$a']
        
    def execute(self, args):
        self.validate_args(args)
    
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Or(
                Condition('191', {'b': body, 'c': session}),
                Condition('791', {'b': body, 'c': session})
            ),
            Condition('040', {'a': 'NNUN'}),
            Condition('040', {'a': 'DHC'}, modifier='not'),
            Condition('930', {'a': Regex('^(UND|ITS|VOT)')}, modifier='not')
        )

        results = []
        
        for bib in BibSet.from_query(query, projection={'191': 1, '791': 1, '930': 1}):
            results.append([bib.id, bib.get_value('191', 'a') or bib.get_value('791', 'a'), '; '.join(bib.get_values('930', 'a'))])
            
        return results

class BibAnyMissing930(Report):
    def __init__(self):
        self.name = 'any_missing_930'
        self.tag = '930'
        self.title = 'Missing field - ' + self.tag
        self.description = 'Any records from the given body/session that do not contain a value in 930$a starting with "UND", "ITS", or "VOT".'
        self.category = "BIB"
        self.form_class = SelectAuthority
        
        self.expected_params = ['authority']    
        self.field_names = ['Record ID', 'Document Symbol', '930$a']
        
    def execute(self, args):
        self.validate_args(args)
    
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Or(
                Condition('191', {'b': body, 'c': session}),
                Condition('791', {'b': body, 'c': session})
            ),
            Condition('040', {'a': 'NNUN'}),
            Condition('040', {'a': 'DHC'}, modifier='not'),
            Condition('930', {'a': Regex('^(UND|ITS|VOT)')}, modifier='not')
        )

        results = []
        
        for bib in BibSet.from_query(query, projection={'191': 1, '791': 1, '930': 1}):
            results.append([bib.id, bib.get_value('191', 'a') or bib.get_value('791', 'a'), '; '.join(bib.get_values('930', 'a'))])
            
        return results

class SpeechAnyMissing930(Report):
    def __init__(self):
        self.name = 'any_missing_930'
        self.tag = '930'
        self.title = 'Missing field - ' + self.tag
        self.description = 'Any records from the given body/session that do not contain a value in 930$a starting with "UND", "ITS", or "VOT".'
        self.category = "SPEECH"
        self.form_class = SelectAuthority
        
        self.expected_params = ['authority']    
        self.field_names = ['Record ID', 'Document Symbol', '930$a']
        
    def execute(self, args):
        self.validate_args(args)
    
        body,session = _get_body_session(args['authority'])
        
        query = QueryDocument(
            Or(
                Condition('191', {'b': body, 'c': session}),
                Condition('791', {'b': body, 'c': session})
            ),
            Condition('040', {'a': 'NNUN'}),
            Condition('040', {'a': 'DHC'}, modifier='not'),
            Condition('930', {'a': Regex('^(UND|ITS|VOT)')}, modifier='not')
        )

        results = []
        
        for bib in BibSet.from_query(query, projection={'191': 1, '791': 1, '930': 1}):
            results.append([bib.id, bib.get_value('191', 'a') or bib.get_value('791', 'a'), '; '.join(bib.get_values('930', 'a'))])
            
        return results

### For use by the main app to access the reports
     
class ReportList(object):
    reports = [
        
        # predefined reports
        
        ############ bib category #############
        
        # (1) Missing subfield value - 999$c t
        BibMissing999_c_t(),
        # (2) Incorrect session - 191
        BibIncorrectSession191(),
        # (3) Incorrect subfield - 191$9
        BibIncorrectSubfield191_9(),
        # (4) Missing field - 991
        BibMissingField('991'),
        # (5) Missing subfield value - 991$z I
        BibMissingSubfieldValue('991', 'z', 'I'),
        # (6) Duplicate agenda item
        BibDuplicateAgenda(),
        # (7) Agenda item misisng indicator
        BibMissingAgendaIndicator(),
        # (8) Missing field - 930
        BibAnyMissing930(),
        # (9) Incorrect field - 991
        BibIncorrect991(),
        # (10) Missing subfield - 991$d
        #BibMissingSubfield991_d(),
        BibMissingSubfield('991', 'd'),
        # (11) Missing field - 992
        BibMissingField('992'),
        # (11.1) Duplicate 515 and 520
        BibRepeated515_520(),
        # 515 520 missing period
        BibEndingWithPeriod515_520(),
        # (12) Incorrect field - 793 (Committees)
        BibIncorrect793Comm(),
        # (13) Incorrect field - 793 (Plenary)
        BibIncorrect793Plen(),
        # (14) Missing subfield value - 991$f X27
        BibMissingSubfieldValue('991', 'f', 'X27'),
        
        # Missing field - 793
        #BibMissingField('793'), # *** disable as per VW - same as "Incorrect"
        # Missing subfield - 191$9
        #BibMissingSubfield('191','9'), # *** disable as per VW - same as "Incorrect"
        #BibMissingField('930'),

        ############# speech category ###############
        
        # (1) Duplicate speech records
        SpeechDuplicateRecord(),
        # 1.1  Identical 700 + 710 + 791
        SpeechIdentical700_710_791(),
        # (2) Incorrect session - 791
        SpeechIncorrectSession791(),
        # (3) Missing fields - 700 + 710
        SpeechMissingFields_700_710(),
        # (New Report) Speeches with parentheses in 700 field
        SpeechParens700(),
        # (4) Incomplete authorities - mother record
        SpeechIncompleteAuthMother(),
        # Incomplete authorities # *** split into two reports below as per VW
        # SpeechIncompleteAuthority(),
        # (5) Incomplete authorities - subfield g
        SpeechIncompleteAuthSubfieldG(),
        # (6) 700 - g
        Speech700g(),
        # (7) Missing field - 039
        SpeechMissingField('039'),
        # (8) Missing field - 930
        SpeechAnyMissing930(),
        # (9) Field mismatch - 039 & 930
        #SpeechMismatch('039', '930'),
        Speech039_930(),
        # (10) Missing field - 991
        SpeechMissingField('991'),
        # (11) Agenda item missing indicator
        SpeechMissingAgendaIndicator(),
        # (12) Incorrect field - 991
        SpeechIncorrect991(),
        # (13) Duplicate agenda item
        SpeechDuplicateAgenda(),
        # (14) Missing subfield - 991$d
        SpeechMissingSubfield('991','d'),
        #SpeechMissingField('930'),
        
        # (15) Missing field - 992
        SpeechMissingField('992'),
        # (16) Incorrect field - 992
        SpeechIncorrect992(),
        # (17) Field mismatch - 269 & 992
        SpeechMismatch('269', '992'), 
        # (18) Missing files
        SpeechMissingFiles(),
        
        
        ################ voting category ############

        # (1) Incorrect session - 791
        VoteIncorrectSession(),
        # (2) Missing field - 039
        VoteMissingField('039'),
        # (3) Missing field - 930
        VoteAnyMissing930(),
        # (4) Field mismatch - 039 & 930
        #VoteMismatch('039', '930'),
        Vote039_930(),
        # (5) Missing field - 992
        VoteMissingField('992'),
        # (6) Incorrect field - 992
        VoteIncorrect992(),
        # (7) Field mismatch - 269 & 992
        VoteMismatch('269', '992'),
        # (8) Missing field - 991
        VoteMissingField('991'),
        # (9) Incorrect field - 991
        VoteIncorrect991(),
        # (10) Missing subfield - 991$d
        VoteMissingSubfield('991','d'),
        # (11) Missing files
        VoteMissingFiles(),

        #VoteMissingField('930'),

        ########## other ##########
        
        # (1) Agenda List
        AgendaList(), 
        
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
    
def _process_results(generator, output_fields):
    results = []
    
    for bib in generator:
        results.append(['; '.join(bib.get_values(*out)) for out in output_fields])
    
    # list of lists
    return results
    
def _body_session_from_symbol(symbol):
    sparts = symbol.split('/')
    body = sparts[0]
    session = None
                    
    if body == 'A':
        if sparts[1][0:1] == 'C' or sparts[1] in ['RES', 'INF', 'BUR', 'DEC']: 
            session = sparts[2]
            
            if 'ES-' in session:
                match = re.match(r'.*ES\-(\d+)', session)
                session = match.group(1) + 'emsp'
                
        elif 'ES-' in sparts[1]:
            match = re.match(r'.*ES\-(\d+)', sparts[1])
            session = match.group(1) + 'emsp'
        else:
            session = sparts[1]
    elif body == 'S':
        if sparts[1] in ['PRST']:
            year = sparts[2][:4]
        elif sparts[1]== 'RES':
            match = re.search(r'\((.+)\)', symbol)
            year = match.group(1)
        elif re.match(r'\d\d\d\d$', sparts[1]):
            year = sparts[1]
        else:
            warn('could not read ' + symbol)
            return [body, '']
        
        try:
            session = _sc_convert(year)
        except(ValueError):
            warn('could not read ' + symbol)
            return [body, '']      
    elif body == 'E':
        if sparts[1]== 'RES': 
            session = sparts[2]
        else:
            session = sparts[1]
        
    else:
        return [body, '']
    
    return [body, session]

def _sc_convert(year):
    return str(int(year) - 1945)
