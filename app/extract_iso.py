#!/usr/bin/env python

from app.config import Config
import re
from dlx import DB
from dlx.marc import BibSet, AuthSet,Condition,Or, Query
from datetime import datetime
from pymongo import MongoClient
from pymongo.collation import Collation
import boto3
import os.path
import glob
import os
from zipfile import ZIP_LZMA, ZipFile

DB.connect(Config.connect_string)
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles
configCollection=myDatabase["itp_config"]


def fetch_agenda(body, session):
    """
    Return the agenda for a particular body and session
    """
    #result = configCollection.find_one( { "type": "snapshot", "bodysession": body + '/' + session }, {"_id": 0, "agenda_symbol": 1} )
    result=None
    match_criteria = ""

    if result == None:

        if body == "A":
            sp = re.search("sp", session)
            em = re.search("em", session)

            if em:
                match_criteria = "A/ES-" + session[:-4] + "/2"
            elif sp:
                match_criteria = "A/S-" + session[:-2] + "/1"
            else:
                match_criteria = "A/" + session + "/251"
        
        if body == "S":
            match_criteria = body + "/" +session

        if body == "E":
            year = session.split("-")
            
            if year[1] == "0":
                match_criteria = "E/" + year[0] + "/2"
            else:
                match_criteria = "E/" + year[0] + "/100"

    else:
        match_criteria = result['agenda_symbol']

    return match_criteria


def fetch_itpcode(body, session):

    result = configCollection.find_one( { "type": "snapshot", "bodysession": body + '/' + session }, {"_id": 0, "product_code": 1} )
    
    itpcode= ""

    if result == None:

        itpcode = 'ITP' + body + session

        sp = re.search("sp", session)
        em = re.search("em", session)

        if body == "E" :
            itpcode = 'ITP' + body + session[2:4] + session[-1]

        if body == "A":
            if em:
                itpcode = 'ITP' + body + session[0:2] + "E"
            elif sp:
                itpcode = 'ITP' + body + session[0:2] + "S"
        if body == "T":
            if sp:
                itpcode = 'ITP' + body + session[0:2] + "S"
    else:
        itpcode = result['product_code']

    return itpcode

def extract_iso(param):
    
    body,session = param.split("/")[0] + "/",param.split("/")[1]

    bib_out = re.sub('/','',str(body)) + str(session)
    auth_out = re.sub('/','',str(body)) + str(session) + 'auth'
    a191_out = re.sub('/','',str(body)) + str(session) + '191'
    
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
    print(f"auth id for {body+session} is {found_auth}")

    # Get the bib records for the target body/session authority id

    print("Fetching bib records...")
    with open(bib_out + '-utf8.iso', 'wb') as f:
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
            if "-00" not in v269 and v269!="":
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
                        #print (v269_new)
                    except:
                        print("can't convert !!!")
                finally:
                    bib.set('269','a',v269_new)
            else:
                print(f"v269 is{v269}")
            if "-00" not in v992 and v992!="":
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
            if "-00" not in v992b and v992b!="":
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
        
        # more fine-grained control over ZIP files
        with ZipFile(bib_out + ".zip", "w",compression=ZIP_LZMA,allowZip64=True) as newzip:
            newzip.write(bib_out + '-utf8.iso')
            
        # Instanciate s3 client            
        s3_client = boto3.client('s3')
        
        # Set some variables
        bucket = Config.bucket_name
        cur_path = os.getcwd()
        file = bib_out + ".zip"
        filename =  os.path.join(cur_path,file)
        
        # load the data into s3
        response=s3_client.upload_file(filename,bucket,file)


    agenda_id = fetch_agenda(body[0], session)
    print(f"agenda_id is {agenda_id}")
    # Get the agenda authorities for the body/session bib records
    
    ##################################################################################################
    print("Fetching agenda authorities...")
    with open(auth_out + '-utf8.iso', 'wb') as f:
        agenda_query=Query(Condition(
                '191',
                {'a':agenda_id}
                    ))
        agendas = AuthSet.from_query(agenda_query)
        for agenda in agendas:
            #print (f"agenda auth is {agenda.get_value('191','a')} - {agenda.get_value('191','b')}")
            f.write(agenda.to_mrc().encode('utf-8'))
                        
        # more fine-grained control over ZIP files
        with ZipFile(auth_out + ".zip", "w",compression=ZIP_LZMA,allowZip64=True) as newzip:
            newzip.write(auth_out + '-utf8.iso')
        
        # upload the file    
        file = auth_out + ".zip"
        filename =  os.path.join(cur_path,file)
        # load the data into s3
        response=s3_client.upload_file(filename,bucket,file)

            
    ##################################################################################################
    print("Fetching 191 agenda authorities...")
    with open(a191_out + '-utf8.iso', 'wb') as f:
        agenda_query=Query(Condition(
                '191',
                {'a':agenda_id}
                    ))
        agendas = AuthSet.from_query(agenda_query)
        for agenda in agendas:
            f.write(agenda.to_mrc().encode('utf-8'))
            
        # more fine-grained control over ZIP files
        with ZipFile(a191_out + ".zip", "w",compression=ZIP_LZMA,allowZip64=True) as newzip:
            newzip.write(a191_out + '-utf8.iso')
        
        # upload the file    
        file = a191_out + ".zip"
        filename =  os.path.join(cur_path,file)
        # load the data into s3
        response=s3_client.upload_file(filename,bucket,file)

        
    # cleaning directory removing *.mrc files
    for file in glob.glob("*.iso"):
        os.remove(file)
        
    for file in glob.glob("*.zip"):
        os.remove(file)

    return
    