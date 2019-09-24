import re
import json
from dlx import DB, Bib, Auth


#connect to the DLX DB 
# itpp_fields is a list of lists (subfields of the same field) containing tuples of (field, subfields)
itpp_fields=[]
#itp_fields is a list that is aggregated from the rules of all A72 sections and assembled here
itp_fields=["035$a","191$a","089$a","191$9", "191$c", "191$b"]
f=""

#generating itpp_fields as in here: [[(035,a)], [(089,a)], [(191,9), (191,a),  (191,b),  (191,c)]]

for itp_field in sorted(itp_fields):
    if itp_field.split("$")[0] !=f:
        temp_f=[]
        temp_f.append((itp_field.split("$")[0],itp_field.split("$")[1]))
        itpp_fields.insert(len(itpp_fields),temp_f)
    else:
        temp_f.append((itp_field.split("$")[0],itp_field.split("$")[1]))
    f=itp_field.split("$")[0]
    s_f=itp_field.split("$")[1]

# getting the records for A72
bibs=Bib.match_value('191','r', 'A72')
# this is a snapshot
itpp_list=[]

# go over bibs and contrcut dict members of the itpp_list
for bib in bibs:
    bib_dict={}
    bib_dict["record_type"]="bib"
    bib_dict["record_id"]=bib.id
    itpp_dict_list=[]  
    for itpp_subfields in itpp_fields:
        itpp_dict_field={}
        itpp_dict_subfield={}
        for subfield in itpp_subfields:
            itpp_dict_subfield[subfield[1]]=bib.get_value(subfield[0],subfield[1])
        itpp_dict_field[subfield[0]]=itpp_dict_subfield
        itpp_dict_list.insert(len(itpp_dict_list),itpp_dict_field)
    for dict in itpp_dict_list:
        bib_dict.update(dict)
#insert constructed dicts
    itpp_list.insert(len(itpp_list),bib_dict)

with open('A72.json', 'w') as outfile:
        json.dump(itpp_list, outfile)