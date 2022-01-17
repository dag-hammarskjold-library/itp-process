import re
from app.config import Config
from pymongo import MongoClient
from itertools import zip_longest

### connection
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles

## establish connections to collection
wordCollection=myDatabase["itp_sample_output_copy"]

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

    #sort the set results
    old_dif_sort = sorted(old_dif)
    new_dif_sort = sorted(new_dif)
    

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
