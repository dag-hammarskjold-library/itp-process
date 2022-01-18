from app.config import Config
from pymongo import MongoClient
from bson.objectid import ObjectId
import re

### connection
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles

## establish connections to collection
configCollection=myDatabase["itp_config"]

def update_snapshot_config(id, bodysession, agenda_symbol, product_code):
    """
    Updates the snapshot config based on record id
    """
    try:
        response = configCollection.update_one(
            { "_id": ObjectId(id) },
            { "$set": { "bodysession": bodysession,
                        "agenda_symbol": agenda_symbol,
                        "product_code": product_code } 
            }
        )

        return response
    except Exception as e:
        return e

def create_snapshot_config(bodysession, agenda_symbol, product_code):
    """
    Creates the snapshot config
    """
    try:
        new_entry = {
            "bodysession": bodysession,
            "agenda_symbol": agenda_symbol,
            "product_code": product_code,
            "type": "snapshot"
        }
        response = configCollection.insert_one(new_entry)
        return response
        
    except Exception as e:
        return e

def delete_snapshot_config(id):
    """
    Deletes the agenda symbol of a body and session.
    """
    response = configCollection.delete_one( { "_id": ObjectId(id)} )
    return response

def get_snapshot_configs():
    """
    Returns list of all configuration elements related to a snapshot.
    Bodysession, Agenda Document Symbol, & Product Code
    """
    return list(configCollection.find( { "type": "snapshot" } ).sort("bodysession"))

####Votedec
def insert_votedec(code, expansion, display, note):
    """
    Deletes votedec entry
    """
    new_entry = {
        "country_code": code,
        "country_expansion": expansion,
        "itp_display": display,
        "type": "votedec",
        "note": note
    }
    response = configCollection.insert_one(new_entry)
    return response

def update_votedec(id, code, expansion, display, note):
    """
    Updates the votedec
    """
    response = configCollection.update_one(
        { "_id": ObjectId(id) },
        { "$set": { "country_code": code,
                    "country_expansion": expansion,
                    "itp_display": display,
                    "note": note } }
    )

    return response

def delete_votedec(id):
    """
    Deletes votedec entry
    """
    response = configCollection.delete_one( { "_id": ObjectId(id)} )
    return response

def get_all_votedec():
    """
    Returns list of Member States names and codes
    """
    return list(configCollection.find( { "type": "votedec" } ).sort("country_expansion"))

def fetch_agenda(body, session):
    """
    Return the agenda for a particular body and session
    """
    result = configCollection.find_one( { "type": "snapshot", "bodysession": body + '/' + session }, {"_id": 0, "agenda_symbol": 1} )
    
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

        if body == "E" :
            itpcode = 'ITP' + body + session[2:4] + session[-1]

        if body == "A":
            sp = re.search("sp", session)
            em = re.search("em", session)

            if em:
                itpcode = 'ITP' + body + session[0:2] + "E"
            elif sp:
                itpcode = 'ITP' + body + session[0:2] + "S"
    else:
        itpcode = result['product_code']

    return itpcode
