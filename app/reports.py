from app.forms import FlaskForm, MissingFieldReportForm, MissingSubfieldReportForm
from dlx.marc.record import Matcher
from app.config import Config
from dlx import DB, Bib, Auth
from dlx.marc.record import Matcher
from bson.regex import Regex

DB.connect(Config.connect_string)

class Report(object):
    def __init__(self):
        # these attributes must be implmeted by the subclass
        self.name = None
        self.title = None
        self.description = None
        self.form_class = None
        self.expected_params = None
        self.stored_criteria = None
        self.output_fields = None
           
    def validate_args(self,args):
        for param in self.expected_params:
            if param not in args.keys():
                raise Exception('Param "{}" not found'.format(param))
        
    def execute(self,args):
        self.validate_args(args)
        
        # todo
        # generic execution
        
### standard reports
        
class MissingFieldReport(Report):
    def __init__(self):
        #super().__init__(self)
        
        self.name = 'missing_field'
        self.title = 'Missing Field Report'
        self.description = 'This report returns bib numbers and document symbols based on a particular body and session for the specified field.'
        self.form_class = MissingFieldReportForm
        
        self.expected_params = ('authority','field')
        self.stored_criteria = [],
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]
        
    # overrides parent method    
    def execute(self,args):
        self.validate_args(args)
        
        auth = _get_auth(args['authority'])
        body,session = _get_body_session(auth)
        
        tag = args['field']
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher(tag,modifier='not_exists'),
            project=['001','191','930']
        )
        
        results = []
        
        for bib in bibs:
            results.append([bib.get_value(*out) for out in self.output_fields])
        
        # list of lists
        return results
        
class MissingSubfieldReport(Report):
    def __init__(self):
        self.name = 'missing_subfield'
        self.title = 'Missing Subfield Report'
        self.description = 'This report returns bib numbers and document symbols based on a particular body and session for the specified field and subfield.'
        self.form_class = MissingSubfieldReportForm
        
        self.expected_params = ('authority','field','subfield')
        self.stored_criteria = [],
        self.output_fields = [
            ('930','a'),
            ('001',None),
            ('191','a')
        ]
        
    def execute(self,args):
        self.validate_args(args)
        
        auth = _get_auth(args['authority'])
        body,session = _get_body_session(auth)
    
        tag = args['field']
        subfield = args['subfield']
        
        bibs = Bib.match(
            Matcher('191',('b',body),('c',session)),
            Matcher(tag,(subfield,Regex('^.')),modifier='not'),
            project=['001','191','930']
        )
        
        results = []
        
        for bib in bibs:
            results.append([bib.get_value(*out) for out in self.output_fields])
        
        # list of lists
        return results

class ReportList(object):
    reports = [
       MissingFieldReport(),
       MissingSubfieldReport()
    ]
    
    def get_by_name(name):
        return next(filter(lambda r: name == r.name, ReportList.reports), None)        
        
### utility functions

def _get_auth(string):
    try:
        auth_id = int(string)
        auth = Auth.match_id(auth_id)
    except ValueError:
        body,session = string.split('/')
        auth = next(Auth.match(Matcher('190',('b',body+'/'),('c',session))),None)
        
    return auth
    
def _get_body_session(auth):
    if auth is None:
        return([['Auth not found']])
    else:
        body = auth.get_value('190','b')
        session = auth.get_value('190','c')
    
    return (body,session)
