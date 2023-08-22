import itertools
import re
from app.config import Config
from pymongo import MongoClient
from itertools import zip_longest, groupby
from unidecode import unidecode

import certifi

### connection
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles


client_dev_atlas=MongoClient(Config.connect_string_dev_atlas, tlsCAFile=certifi.where())
db_dev_atlas=client_dev_atlas['itpp']
## establish connections to collection
wordCollection=db_dev_atlas["itp_sample_output_copy"]
outputCollection=db_dev_atlas["itp_sample_output"]

def get_heading_comparison(bodysession, section, file_text):
    if section == 'itpsubj':
        heading = "head"
 
    else:
        heading = "itshead"
 
   #retrieve the list from the database
    results = list(wordCollection.find({
        'bodysession': bodysession,
        'section': section
    },
    {'_id': 0, heading: 1}))
 
    new_script = []
 
    for r in results:
        new_script.append(r[heading])
 
    new_set = set(new_script)
    old_set = set(file_text)
 
    old_dif = old_set.difference(new_set) #in old but not in new
    new_dif = new_set.difference(old_set) #in new but not in old
    new_dif1=[]
    for i in new_dif:
        if i is None:
            i=""#None breaks the code in the app
        new_dif1.append(i)  
    new_dif_s=set(new_dif1)
    #sort the set results
    old_dif_sort = sorted(old_dif)
    new_dif_sort = sorted(new_dif_s)
   
 
    zipped = zip_longest(old_dif_sort, new_dif_sort, fillvalue='')
    set_dif = (list(zipped))
 
    zipped_full = zip_longest(file_text, new_script, fillvalue='')
    full_list = (list(zipped_full))
 
    summary = {}
    summary['o_total_headings'] = len(file_text)
    summary['n_total_headings'] = len(new_script)
 
    summary['o_total_dif'] = len(old_dif)
    summary['n_total_dif'] = len(new_dif)
 
    summary['o_only'] = old_dif #in old but not in new
    summary['n_only'] = new_dif #in new but not in old
 
    summary['differences'] = set_dif
 
    summary['full_list'] = full_list
     
    return summary
 
def get_sorting_comparison(bodysession, section, file_text):
    
    if section == 'itpsubj':
        heading = "$head"
 
    else:
        heading = "$itshead"
 
    pipeline = [
        {
            '$match': {
                'bodysession': bodysession,
                'section': section
            }
        }, {
            '$group': {
                '_id': {'$substrCP': [heading, 0, 1]},
                'head': {'$push': heading}
            }
        }, {
            '$sort': {
                '_id': 1
            }
        }
    ]
 
    collation={
            'locale': 'en',
            'strength': 1,
            'numericOrdering': True
        }
 
    new_script = wordCollection.aggregate(pipeline, collation=collation)

    an_iterator = itertools.groupby(file_text, lambda x : unidecode(x[0][0]))
 
    old_script = []
    record = {}
 
    for key, group in an_iterator:
 
        record['_id'] =  key

        record['head'] = list(group)
 

        old_script.append(record)
        record = {}
 
    differences = []
    dif = {}
   
    for x, y in zip(old_script, new_script):
        if x != y:
            #dif = (x, y)
            dif['letter'] = x['_id']
            zipped = zip_longest(x['head'], y['head'], fillvalue='')
            dif['set_dif'] = (list(zipped))
           
            differences.append(dif)
            dif = {}
 
    return differences
 
def get_detail_comparison(bodysession, section, file_text):
 
    if section == 'itpsubj':
        head_txt = "head"
        subhead_txt = "subhead"
        entries_txt = "entries"
        entry_txt = "entry"
        docsymbol_txt = "docsymbol"
 
    else:
        head_txt = "itshead"
        subhead_txt = "itssubhead"
        entries_txt = "itsentries"
        entry_txt = "itsentry"
        docsymbol_txt = "docsymbols"
 
    pipeline = [
        {
            '$match': {
                'bodysession': bodysession,
                'section': section
            }
        }
    ]
 
    new_script = wordCollection.aggregate(pipeline)
   
    new_details = []
 
    num = 1
    for n in new_script:
        record = {}
 
        record['num'] = num
        record['head'] = n[head_txt]
 
        table_group = []
 
        subheading = {}
 
        for s in n['subheading']:
            subheading['subhead'] = s[subhead_txt]
 
            entries = []
            for e in s[entries_txt]:
 
                if section == "itpitsc" or section == "itpitss":
                    full_entry = e[entry_txt]
 
                    for i in range(len(e[docsymbol_txt])):
                        if i == 0:
                            full_entry = full_entry + ' — ' +  e[docsymbol_txt][i]
                        else:
                            full_entry = full_entry + "; " + e[docsymbol_txt][i]
 
                    entries.append(full_entry)
                    full_entry = ""
 
                if section == "itpitsp":
                    for i in range(len(e[docsymbol_txt])):
                        if i == 0:
                            full_entry = e[docsymbol_txt][i]
                        else:
                            full_entry = full_entry + "; " + e[docsymbol_txt][i]
 
                    entries.append(full_entry)
                    full_entry = ""
 
                if section == "itpsubj":
                    full_entry = {
                        "entry": e[docsymbol_txt] + " " + e[entry_txt],
                        "note": e['note']
                    }
 
                    entries.append(full_entry)
                    full_entry = ""
               
            subheading['entries'] = entries
 
            table_group.append(subheading)
            subheading = {}
           
        record['table_group'] = table_group
 
        num = num + 1
        new_details.append(record)
   
    ###################################################################################################
    
    if section == 'itpsubj':
        for new_detail in new_details:
    
            # Mettre a jour n et n+1
            for nd in new_detail["table_group"]:
    
                recup = nd["entries"]
                for nd_01 in recup:
                
                    for entry in nd["entries"]:
                
                        if nd_01["entry"] == entry["entry"]:
                            
                            if nd_01["note"] !="" and entry["note"] =="":
                                entry["note"] = nd_01["note"]              
    
    
    
            # Remove duplicate
            for nd in new_detail["table_group"]:
                without_duplicate=[]
                for entry in (nd["entries"]):
                    if entry not in without_duplicate:
                        without_duplicate.append(entry)
                nd["entries"]=without_duplicate
            
            # cleaning doble periods issues
            for nd in new_detail["table_group"]:    
                for data in (nd["entries"]):
                    data1=data
                    if (data1["entry"][len(data1["entry"])-1]==data1["entry"][len(data1["entry"])-2]) and (data1["entry"][len(data1["entry"])-1]=="."):
                        data["entry"]=data1["entry"][:-1]

       
    details = []
 
    for x, y in zip(file_text, new_details):
        if x != y:
            #print(x, y)
            detail = {}
 
            detail['num'] = x['num']
            detail['head'] = x['head']
 
            zipped = zip_longest(x['table_group'], y['table_group'], fillvalue='')
 
            #use the tuple() function to display a readable version of the result:
            l = list(zipped)
 
            table_group = []
            subheading = {}
            entries = []
 
 
            for old, new in l:
                if old == '':
                    old = {}
                    old['subhead'] = ''
                    old['entries'] = []
               
                if new == '':
                    new = {}
                    new['subhead'] = ''
                    new['entries'] = []
 
                subheading['subhead'] = (old['subhead'],new['subhead'])
 
                for o, n in list(zip_longest(old['entries'], new['entries'], fillvalue='')): #zip longest
                    entry = (o, n)
                    entries.append(entry)
               
                subheading['entries'] = entries
                entries = []
                table_group.append(subheading)
                subheading = {}
           
            detail['table_group'] = table_group
 
            details.append(detail)
 
    return details
 
def get_dslist_comparison(bodysession, file_text):
    
 
  #retrieve the list from the database
    results = list(outputCollection.find({
        'bodysession': bodysession,
        'section': "itpdsl"
    },
    {'_id': 0, 'docsymbol': 1}))
 
    new_script = []
 
    for r in results:
        new_script.append(r['docsymbol'])
 
    new_set = set(new_script)
    old_set = set(file_text) #set(filter(None, file_text))
 
    old_set.discard(None)
    new_set.discard(None)
 
    old_dif = old_set.difference(new_set) #in old but not in new
    new_dif = new_set.difference(old_set) #in new but not in old
 
    #sort the set results
    old_dif_sort = sorted(old_dif)
    new_dif_sort = sorted(new_dif)
   
 
    zipped = zip_longest(old_dif_sort, new_dif_sort, fillvalue='')
    set_dif = (list(zipped))
 
    zipped_full = zip_longest(file_text, new_script, fillvalue='')
    full_list = (list(zipped_full))
 
    summary = {}
    summary['o_total_docsymbols'] = len(file_text)
    summary['n_total_docsymbols'] = len(new_script)
 
    summary['o_total_dif'] = len(old_dif)
    summary['n_total_dif'] = len(new_dif)
 
    summary['o_only'] = old_dif #in old but not in new
    summary['n_only'] = new_dif #in new but not in old
 
    summary['differences'] = set_dif
 
    summary['full_list'] = full_list
     
    return summary