import re
import json
from dlx import DB, Bib, Auth
import pymongo

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
def get_ITPP_Shapshot_records(body, session):
    bibs = Bib.match_fields_or(
           ('191',('b', re.compile('^'+body),('c', session))),
           ('791',('b', re.compile('^'+body),('c', session)))
        )
    return bibs

# 2. pull a list of subfields to extract from the section docuement and create sbflds list
'''
for doc in rules_coll.find({"$and":[{"body":"A"},{"session":"72"},{"name":"filter fields"}]}):
    itp_bib_fields.extend(doc["parameters"]["actions"]["bibs"])
    #itp_auth_fields.extend(doc["parameters"]["actions"]["auths"])

set_itp_bib_fields=sorted(set(itp_bib_fields))
'''
sbflds=[]
itpp_fields=[]
f=''
# 3. prepare a proper structure of tuples for easier processing e.g.
# [[(035,a)], [(089,a)], [(191,9), (191,a),  (191,b),  (191,c)]]
for itp_field in sbflds:
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

# 4. Create a snapshot ; insert individual docs into a mongo DB
for bib in get_ITPP_Shapshot_records('A/','72'):
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
    
    #save each record using mongoengine model or insert one in mongoDB