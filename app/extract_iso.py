#!/usr/bin/env python

# from docopt import docopt
from collections import OrderedDict
from pymarc import Record
from app.config import Config
from bson.son import SON
import re
from dlx import DB
from dlx.marc import Bib, Auth, BibSet, AuthSet,Condition,Or, Query
from datetime import datetime
from pymongo import MongoClient
from pymongo.collation import Collation
from app.itp_config import fetch_agenda,fetch_itpcode
import boto3
import os.path
from pathlib import Path
import glob
import os


DB.connect(Config.connect_string)
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles
configCollection=myDatabase["itp_config"]

def extract_iso(param):
    
    body,session = param.split("/")[0] + "/",param.split("/")[1]

    bib_out = re.sub('/','',str(body)) + str(session)
    auth_out = re.sub('/','',str(body)) + str(session) + 'auth'
    a191_out = re.sub('/','',str(body)) + str(session) + '191'
    
    print(auth_out)

    auths = DB.auths
    bibs = DB.bibs

    # Get the authority record for the body/session
    match_criteria=fetch_itpcode(body,session)
    query = Query(
                Condition(
                tag='190',
                subfields={'b':body}
                    ),
                Condition(
                tag='190',
                subfields={'c': session}
                    )
            )
    
    for auth in AuthSet.from_query(query):
        found_auth=auth.get_value("001")
    # print(f"auth id for {body+session} is {found_auth}")

    # Get the bib records for the target body/session authority id

    print("Fetching bib records...")
    with open(bib_out + '-utf8.mrc', 'wb') as f:
        bibs_query = Query(
            Or(
                Condition(
                '191',
                {'b':int(found_auth)}
                    ),
                Condition(
                '791',
                {'b': int(found_auth)}
                    )
                )
            )
        # print(f"query for fetching bibs is {bibs_query.to_json()}")
        bibset = BibSet.from_query(bibs_query, collation=Collation(
            locale='en', 
            strength=1,
            numericOrdering=True)
        )
        list_t=["May.","Jun.","Jul."]
        for bib in bibset:
            v269=bib.get_value('269','a')
            v992=bib.get_value('992','a')
            v992b=bib.get_value('992','b')
            if "00" not in v269 and v269!="":
                try:
                    v269_new=datetime.strptime(v269, '%Y-%m-%d').date().strftime('%Y%m%d')
                    if any(word in v269_new for word in list_t):
                        v269_new=datetime.strptime(v269, '%Y-%m-%d').date().strftime('%Y%m%d')
                    # print (v269_new)
                    
                except ValueError:
                    try:
                        v269_new=datetime.strptime(v269, '%Y').date().strftime('%Y')
                    except ValueError: 
                        v269_new=datetime.strptime(v269, '%Y-%m').date().strftime('%Y%m')
                        if any(word in v269_new for word in list_t):
                            v269_new=datetime.strptime(v269, '%Y-%m').date().strftime('%Y%m')
                        print (v269_new)
                    except:
                        print("can't convert !!!")
                finally:
                    bib.set('269','a',v269_new)
            else:
                print(f"v269 is{v269}")
            if "00" not in v992 and v992!="":
                try:
                    v992_new=datetime.strptime(v992, '%Y-%m-%d').date().strftime('%Y%m%d')
                    if any(word in v992_new for word in list_t):
                        v992_new=datetime.strptime(v992, '%Y-%m-%d').date().strftime('%Y%m%d')
                except ValueError:
                    try:
                        v992_new=datetime.strptime(v992, '%Y').date().strftime('%Y')
                    except ValueError: 
                        v992_new=datetime.strptime(v992, '%Y-%m').date().strftime('%Y%m')
                        if any(word in v992_new for word in list_t):
                            v992_new=datetime.strptime(v992, '%Y-%m').date().strftime('%Y%m')
                    except:
                        print("can't convert !!!")
                finally:
                    bib.set('992','a',v992_new)
            else:
                pass
            if "00" not in v992b and v992b!="":
                try:
                    v992b_new=datetime.strptime(v992b, '%Y-%m-%d').date().strftime('%Y%m%d')
                    if any(word in v992b_new for word in list_t):
                        v992b_new=datetime.strptime(v992b, '%Y-%m-%d').date().strftime('%Y%m%d')
                except ValueError:
                    try:
                        v992b_new=datetime.strptime(v992b, '%Y').date().strftime('%Y')
                    except ValueError: 
                        v992b_new=datetime.strptime(v992b, '%Y-%m').date().strftime('%Y%m')
                        if any(word in v992b_new for word in list_t):
                            v992b_new=datetime.strptime(v992b, '%Y-%m').date().strftime('%Y%m')
                    except:
                        print("can't convert !!!")  
                finally:
                    bib.set('992','b',v992b_new)
                    print (f"992b is {bib.get_value('992','b')}")
            else:
                pass
            
            f.write(bib.to_mrc().encode('utf-8'))
            
        # Instanciate s3 client            
        s3_client = boto3.client('s3')
        
        # Set some variables
        bucket = Config.bucket_name
        cur_path = os.getcwd()
        print(cur_path)
        file = bib_out + '-utf8.mrc'
        filename =  os.path.join(cur_path,file)
        
        # load the data into s3
        response=s3_client.upload_file(filename,bucket,file)


    agenda_id = fetch_agenda(body[0], session)
    print(f"agenda_id is {agenda_id}")
    # Get the agenda authorities for the body/session bib records
    
    # print("Fetching agenda authorities...")
    with open(auth_out + '-utf8.mrc', 'wb') as f:
        agenda_query=Query(Condition(
                '191',
                {'a':agenda_id}
                    ))
        agendas = AuthSet.from_query(agenda_query)
        for agenda in agendas:
            #print (f"agenda auth is {agenda.get_value('191','a')} - {agenda.get_value('191','b')}")
            f.write(agenda.to_mrc().encode('utf-8'))
        
        # upload the file    
        file = auth_out + '-utf8.mrc'
        filename =  os.path.join(cur_path,file)
        # load the data into s3
        response=s3_client.upload_file(filename,bucket,file)
        # os.remove(file)
            
    
    print("Fetching 191 agenda authorities...")
    with open(a191_out + '-utf8.mrc', 'wb') as f:
        agenda_query=Query(Condition(
                '191',
                {'a':agenda_id}
                    ))
        agendas = AuthSet.from_query(agenda_query)
        for agenda in agendas:
            f.write(agenda.to_mrc().encode('utf-8'))
        
        # upload the file    
        file = a191_out + '-utf8.mrc'
        filename =  os.path.join(cur_path,file)
        # load the data into s3
        response=s3_client.upload_file(filename,bucket,file)
        # os.remove(file)    
        
    # cleaning directory removing *.mrc files
    for file in glob.glob("*.mrc"):
        os.remove(file)

    return
    