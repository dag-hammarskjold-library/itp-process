from app.config import Config
from pymongo import MongoClient
from pymongo.collation import Collation
from bson.objectid import ObjectId
import re


### connection
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles

## establish connections to collection
configCollection=myDatabase["itp_config"]
snapshotCollection=myDatabase["itpp_snapshot_test3"]
devSnaphotCollection=myDatabase["dev_Itpp_snapshot"]

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
    return list(configCollection.find( { "type": "snapshot" } ).sort("bodysession").collation(Collation(locale='en', numericOrdering=True)))

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

def snapshot_summary(body):
    """
    """
    pipeline = []
    collation={
            'locale': 'en', 
            'numericOrdering': True
        }

    if body == "A": 
        match_stage = {
            '$match': {
                'bodysession': re.compile(r"^A")
            }
        }
    elif body == "S":
        match_stage = {
            '$match': {
                'bodysession': re.compile(r"^S")
            }
        }
    elif body == "T":
        match_stage = {
            '$match': {
                'bodysession': re.compile(r"^T")
            }
        }
    else:
        match_stage = {
            '$match': {
                'bodysession': re.compile(r"^E")
            }
        }

    group_stage1 = {
        '$group': {
            '_id': {
                'bodysession': '$bodysession', 
                'record_type': '$record_type'
            }, 
            'count': {
                '$sum': 1
            }
        }
    }

    sort_stage1 = {
        '$sort': {
            '_id.record_type': 1
        }
    }

    group_stage2 = {
        '$group': {
            '_id': '$_id.bodysession', 
            'breakdown': {
                '$push': {
                    'type': '$_id.record_type', 
                    'total': {'$sum': '$count'}
                }
            }, 
            'total': {'$sum': '$count'}
        }
    }

    add_stage = {
        '$addFields': {
            'snap': {
                '$reduce': {
                    'input': {
                        '$split': ['$_id', '/']
                    }, 
                    'initialValue': '', 
                    'in': {
                        '$concat': ['$$value', '$$this']
                    }
                }
            }
        }
    }

    lookup_stage = {
        '$lookup': {
            'from': 'dev_Itpp_snapshot', 
            'localField': 'snap', 
            'foreignField': 'snapshot_name', 
            'as': 'snapshot'
        }
    }

    project_stage = {
        '$project': {
            '_id': 0, 
            'bodysession': '$_id', 
            'run_date': {
                '$dateToParts': {
                    'date': {'$arrayElemAt': ['$snapshot.started', 0]}, 
                    'timezone': 'America/New_York'
                }
            }, 
            'status': {
                '$cond': {
                    'if': {'$arrayElemAt': ['$snapshot.currently_running', 0]}, 
                    'then': 'Running', 
                    'else': 'Completed'
                }
            }, 
            'duration': {
                '$round': [
                    {'$divide': [
                        {'$subtract': [
                            {'$cond': {
                                'if': {'$arrayElemAt': ['$snapshot.finished', 0]}, 
                                'then': {'$arrayElemAt': ['$snapshot.finished', 0]}, 
                                'else': '$$NOW'
                                }
                            }, 
                            {'$arrayElemAt': ['$snapshot.started', 0]}
                            ]
                        }, 60000
                        ]
                    }, 1
                ]
            }, 
            'total_num': '$total', 
            'breakdown': 1,
            'snapshot_name': {'$arrayElemAt': ['$snapshot.snapshot_name', 0]}
        }
    }

    sort_stage2 = {
        '$sort': {
            'bodysession': -1
        }
    }

    pipeline.append(match_stage)
    pipeline.append(group_stage1)
    pipeline.append(sort_stage1)
    pipeline.append(group_stage2)
    pipeline.append(add_stage)
    pipeline.append(lookup_stage)
    pipeline.append(project_stage)
    pipeline.append(sort_stage2)

    return list(snapshotCollection.aggregate(pipeline=pipeline, collation=collation))

def deleteSnapshot(bodysession):
    try:
        bs = bodysession.split("/")
        body = bs[0]
        session = bs[1]
        snapshot_name = body + session
        
        snapshotCollection.delete_many({'bodysession': bodysession})
        devSnaphotCollection.delete_one({'snapshot_name': snapshot_name})

        msg = "Deleted " + bodysession

        return msg

    except Exception as e:
        return e

def snapshotDropdown():
    try:
        pipeline = []

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        group_stage = {
            '$group': {
                '_id': {
                    'bs': '$bodysession', 
                    'sort_order': {
                        '$let': {
                            'vars': {
                                'letter': {'$substrCP': ['$bodysession', 0, 1]}
                            }, 
                            'in': {
                                '$switch': {
                                    'branches': [
                                        {'case': {'$eq': ['$$letter', 'E']}, 'then': '01'},
                                        {'case': {'$eq': ['$$letter', 'A']}, 'then': '02'},
                                        {'case': {'$eq': ['$$letter', 'S']}, 'then': '03'},
                                        {'case': {'$eq': ['$$letter', 'T']}, 'then': '04'},
                                    ], 
                                    'default': 'XX'
                                }
                            }
                        }
                    }
                }
            }
        }
    
        

        sort_stage = {
            '$sort': {
                '_id.sort_order': 1, 
                '_id.bs': -1
            }
        }

        project_stage = {
            '$project': {
                '_id': 0, 
                'bodysession': '$_id.bs'
            }
        }

        pipeline.append(group_stage)
        pipeline.append(sort_stage)
        pipeline.append(project_stage)

        results = list(snapshotCollection.aggregate(pipeline, collation=collation))

        dropdown = []

        for r in results:
            dropdown.append(r['bodysession'])

        return dropdown

    except Exception as e:
        return e