from app.config import Config
from pymongo import MongoClient

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
