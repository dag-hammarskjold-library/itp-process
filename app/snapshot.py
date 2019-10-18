import re
import json
from config import Config
from dlx import DB
from dlx.marc import Bib, Auth, Matcher, OrMatch
import pymongo
import reports

DB.connect(Config.connect_string)


# extend Bib class with itpp serialisation method
class Bib_itpp (Bib):
    def to_itpp(self, sbflds):
        #temp_lst=[]
        for field in self.get_fields():
            temp_dict={}
            for subfield in field.subfields:
                for k,v in self.serialize_subfield(subfield).items():
                    try:
                        if k in sbflds:
                            temp_dict[k]= v
                    except:
                        temp_dict[k]= v
        #temp_lst.append(temp_dict)
    #return temp_lst
        return temp_dict

# 1. records for ITP e.g. A72
#body=A/; session = 72
'''
def get_ITPP_Shapshot_records(body, session, lst_fields):
    bibs = Bib.match(
    OrMatch(
        Matcher('191',('b',body+'/'),('c',session)),
        Matcher('791',('b',body+'/'),('c',session))
    ),
        project=lst_fields
)
    return bibs

#print(len(list(get_ITPP_Shapshot_records('A','72'))))
'''
# 2. pull a list of subfields to extract from the section docuement and create sbflds list

for doc in rules_coll.find({"$and":[{"body":"A"},{"session":"72"},{"name":"filter fields"}]}):
    itp_bib_fields.extend(doc["parameters"]["actions"]["bibs"])
    #itp_auth_fields.extend(doc["parameters"]["actions"]["auths"])

set_itp_bib_fields=sorted(set(itp_bib_fields))

sbflds=[]
itpp_fields=[]
f=''

# 3. prepare a proper structure of tuples for easier processing e.g.
# [[(035,a)], [(089,a)], [(191,9), (191,a),  (191,b),  (191,c)]]
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

#lsit of fields for projectsions for Matcher object query
list_of_fields=[t[0] for t in sbflds]        
list_of_fields =['001','035','089','191','239','245','249','269','495','515','520','580','591','592','598','599','700','711', '791', '930', '949', '991', '992', '995','996']

''' 4. Create a snapshot ; insert individual docs into a mongo DB
for bib in get_ITPP_Shapshot_records('A','72',list_of_fields ):
    #bib=Bib.match_id('1161969')
    bib_dict={}
    bib_dict["record_type"]="bib"
    bib_dict["record_id"]=bib.id
    for itpp_field_subfields in itpp_fields:
        #flds=[]
        sbflds=[]
        for elem in itpp_field_subfields:
            field=elem[0]
            sbflds.extend(elem[1])
        bib_dict[field]=bib.to_itpp(sbflds)
        print(bib_dict)
''' 
    # 5. save each record using mongoengine model or insert one in mongoDB

    class Snapshot(object):
    def __init__(self):
        # these attributes must be implmeted by the subclass
        self.name = None
        self.created = None
        self.body_session_auth = None
        self.record = None
        self.form_class = None
        self.output_subfields=output_subfields
        self.expected_params=None

    def validate_args(self,args):
        for param in self.expected_params:
            if param not in args.keys():
                raise Exception('Param "{}" not found'.format(param))
        
    def execute(self,args):
        self.validate_args(args)
        
        # todo
        # generic execution
    
    # for individual bib retrieve all subfields and then in this function filter out all not in the sbflds
    def list_of_subfields(self, bib, field, sbflds):
    temp_lst=[]
    for field in bib.get_fields(field):
        temp_dict={}
        for subfield in field.subfields:
            for k,v in Bib.serialize_subfield(subfield).items():
                if k in sbflds:
                    temp_dict[k]= v
        temp_lst.append(temp_dict)
    return temp_lst


        class GA_snapshot(Snapshot):
        def __init__(self):
            #super().__init__(self)
            self.name = "General Assembly ITP Snapshot"
            self.created = DateTimeField(default=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
            self.body_session_auth = StringField()
            self.record = DictField()
            self.form_class = GASnapshotForm
            self.expected_params = ['authority', 'fields']
            self.output_subfields = [
                ('035','a'),
                ('089','a'),
                ('191','9'),
                ('191','a'),
                ('191','b'),
                ('191','c')
                ('930','a'),
            ]
            # list of fields needed for GA ITPs

        
    # overrides parent method    
    def execute(self,args):
        self.validate_args(args)
        
        auth = _get_auth(args['authority'])
        body,session = _get_body_session(auth)

        #may utilize projections of the match boject to optimise execution time and unnecessary carrying over fields
        bibs = Bib.match(
            OrMatch(
                    Matcher('191',('b',body),('c',session)),
                    Matcher('791',('b',body),('c',session))
                    )
        )
        # go over bibs and construct dict members of the itpp_list
        for bib in bibs:
            bib_dict={}
            if "ITS" in bib.get_values('930','a'):
                bib_dict["record_type"]="ITS"
            elif "VOT" in bib.get_values('930','a'):
                bib_dict["record_type"]="VOT"
            else:
                bib_dict["record_type"]="BIB"

            bib_dict["record_id"]=bib.id
            itpp_fields=args['subfields']
            #e.g.  [(035,a)], [(089,a)], [(191,9), (191,a),  (191,b),  (191,c)] are some itpp_field_subfields
            for itpp_field_subfields in itpp_fields:
                #flds=[]
                sbflds=[]
                for elem in itpp_field_subfields:
                    field=elem[0]
                    sbflds.extend(elem[1])
                bib_dict[field]=self.list_of_subfields(bib,field,sbflds)
            itpp_list.insert(len(itpp_list),bib_dict)
        return itpp_list

    