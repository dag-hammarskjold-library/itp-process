import re
import json
from app.config import Config
from app.forms import MissingFieldReportForm, MissingSubfieldReportForm, SelectAuthority
from dlx import DB
from dlx.marc import Bib, Auth, Matcher, OrMatch
from app.reports import AuthNotFound, InvalidInput, _get_body_session
import pymongo
from pymongo import MongoClient

DB.connect(Config.connect_string)
db_client=MongoClient(Config.connect_string)
db=db_client['undlFiles']
rules_coll = db['itpp_rules']
snapshot_coll=db['itpp_snapshot_test']
itp_bib_fields=[]

'''
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
'''

def _list_of_subfields(bib, field, sbflds):
    temp_lst=[]
    
    for field in bib.get_fields(field):
        temp_dict={}
        for subfield in field.subfields:
            for k,v in Bib.serialize_subfield(subfield).items():
                if k in sbflds:
                    temp_dict[k]= v
        temp_lst.append(temp_dict)
    return temp_lst

class Snapshot(object):
    def __init__(self,args):
        # these attributes must be implmeted by the subclass
        self.name = None
        self.title = None
        self.description = "New Snapshot"
        #self.category = None
        self.form_class = SelectAuthority
        self.expected_params = ["authority"]
        #self.DB=DB.connect(Config.connect_string)
        #self.db_client=MongoClient(Config.connect_string)
        #self.db=db_client['undlFiles']
        #self.rules_coll = db['itpp_rules']
        #self.snapshot_coll=db['itpp_snapshot_test']
        #self.stored_criteria = None
        #self.output_fields = None
        self.body, self.session=_get_body_session(args['authority'])
        #self.session=_get_body_session(args['authority'])

          
    def validate_args(self,args):
        for param in self.expected_params:
            if param not in args.keys():
                raise Exception('Expected param "{}" not found'.format(param))
            
    def execute(self,args):
        itp_bib_fields=[]
        self.validate_args(args)
        body,session = _get_body_session(args['authority'])
        print("body = "+body)
        i=0
        #1. get the list of fields for the ITP 
        for doc in self.rules_coll.find({"$and":[{"body":body},{"session":session},{"name":"filter fields"}]}):
            itp_bib_fields.extend(doc["parameters"]["actions"]["bibs"])
        set_itp_bib_fields=sorted(set(itp_bib_fields))
                
        # 2. prepare a proper structure of tuples for easier processing e.g.
        # [[(035,a)], [(089,a)], [(191,9), (191,a),  (191,b),  (191,c)]]
        sbflds=[]
        itpp_fields=[]
        f=''
        for itp_field in set_itp_bib_fields:
            #temp_f.append((itp_field.split("$")[0],itp_field.split("$")[1]))
            if itp_field !="001":
                if itp_field.split("$")[0] !=f:
                    temp_f=[]
                    temp_f.append((itp_field.split("$")[0],itp_field.split("$")[1]))
                    itpp_fields.insert(len(itpp_fields),temp_f)
                else:
                    temp_f.append((itp_field.split("$")[0],itp_field.split("$")[1]))
                f=itp_field.split("$")[0]
                s_f=itp_field.split("$")[1]

        #3. find the bibs
        bibs = Bib.match(
            OrMatch(
                    Matcher('191',('b',body+'/'),('c',session)),
                    Matcher('791',('b',body+'/'),('c',session))
                    )
                )
        #4. go over bibs and construct dict members of the itpp_list
        for bib in bibs:
            #bib=Bib.match_id('1161969')
            bib_dict={}
            if "ITS" in bib.get_values('930','a'):
                bib_dict["record_type"]="ITS"
            elif "VOT" in bib.get_values('930','a'):
                bib_dict["record_type"]="VOT"
            else:
                bib_dict["record_type"]="BIB"

            bib_dict["record_id"]=bib.id
            for itpp_field_subfields in itpp_fields:
                #flds=[]
                sbflds=[]
                for elem in itpp_field_subfields:
                    field=elem[0]
                    sbflds.extend(elem[1])
                temp_dict={}
                temp_dict[field]=_list_of_subfields(bib,field,sbflds)
                if len(temp_dict[field])>1:
                    bib_dict[field]=temp_dict[field]
                elif len(temp_dict[field])==1:
                    bib_dict[field]=temp_dict[field][0]
                else:
                    bib_dict[field]=""
            #itpp_dict_list=[]  
            #for itpp_subfields in itpp_fields:
            #    itpp_dict_field={}
            #    itpp_dict_subfield={}
            #    for subfield in itpp_subfields:
            #        itpp_dict_subfield[subfield[1]]=bib.get_value(subfield[0],subfield[1])
            #    itpp_dict_field[subfield[0]]=itpp_dict_subfield
            #    itpp_dict_list.insert(len(itpp_dict_list),itpp_dict_field)
            #for dict in itpp_dict_list:
            #    bib_dict.update(dict)
        #insert constructed dicts
            i=i+1
            '''snapshot_coll.update(
                {"record_id":bib_dict["record_id"]},
                bib_dict,
                {upsert:true}
            )'''
            try:
                self.snapshot_coll.insert_one(bib_dict)
            except:
                warning="somthing wrong with insert into MDb"
        return i








