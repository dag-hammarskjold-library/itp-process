import re
import json
from app.config import Config
from app.forms import MissingFieldReportForm, MissingSubfieldReportForm, SelectAuthority
import dlx
from dlx import DB
from dlx.marc import Bib, Auth, Matcher, OrMatch
from app.reports import AuthNotFound, InvalidInput, _get_body_session
import pymongo
from pymongo import MongoClient

DB.connect(Config.connect_string)
db_client=MongoClient(Config.connect_string)
db=db_client['undlFiles']
rules_coll = db['itpp_rules']
snapshot_coll=db['itpp_snapshot_test1']
itp_bib_fields=[]


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
    def __init__(self,body, session):
        self.name = None
        self.title = None
        self.description = "New Snapshot"
        self.form_class = SelectAuthority
        self.expected_params = "authority"
        self.body =body
        self.session=session


    def list_of_subfields(self,bib,field,sbflds):
        temp_lst=[]
        
        for field in bib.get_fields(field):
            temp_dict={}
            for sub in field.subfields:
                if sub.code in sbflds:
                        temp_dict[sub.code]= sub.value
            temp_lst.append(temp_dict)
        return temp_lst    
            
    def execute(self,body,session):
        itp_bib_fields=[]
        i=0
        #1. get the list of fields for the ITP 
        for doc in rules_coll.find({"$and":[{"body":body},{"session":session},{"name":"filter fields"}]}):
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
                    Matcher('191',('b',self.body+'/'),('c',self.session)),
                    Matcher('791',('b',self.body+'/'),('c',self.session)),
                    ),
                    project=list({l[0][0] for l in itpp_fields})
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
            bib_dict["bodysession"]=self.body+self.session

            #print("bib.id = "+str(bib_dict["record_id"]))
            for itpp_field_subfields in itpp_fields:
                #flds=[]
                sbflds=[]
                for elem in itpp_field_subfields:
                    field=elem[0]
                    sbflds.extend(elem[1])
                temp_dict={}
                temp_dict[field]=self.list_of_subfields(bib,field,sbflds)
                if len(temp_dict[field])>1:
                    bib_dict[field]=temp_dict[field]
                elif len(temp_dict[field])==1:
                    bib_dict[field]=temp_dict[field][0]
                else:
                    bib_dict[field]=""
            i=i+1
            #print(str(i))
            
            '''snapshot_coll.update(
                {"record_id":bib_dict["record_id"]},
                bib_dict,
                {upsert:true}
            )'''
            try:
                snapshot_coll.insert_one(bib_dict)
            except:
                warning="something went wrong with insert into MDb"
        return i








