from app.config import Config
from pymongo import MongoClient
from bson.objectid import ObjectId

### connection
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles

## establish connections to collection
configCollection=myDatabase["itp_config"]

def upsert_agenda(bodysession, agenda_symbol):
    """
    Updates or inserts the agenda symbol of a body and session.
    """

    print(bodysession, agenda_symbol)

    response = configCollection.update_one(
        { "bodysession": bodysession },
        { "$set": { "agenda_symbol": agenda_symbol,
                    "type": "agenda" } },
        upsert=True 
    )

    return response

def delete_agenda(bodysession):
    """
    Deletes the agenda symbol of a body and session.
    """
    response = configCollection.delete_one( { "bodysession": bodysession, "type": "agenda"} )
    return response

def get_all_agendas():
    return list(configCollection.find( { "type": "agenda" }, {"_id": 0, "bodysession": 1, "agenda_symbol": 1} ))

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
