from app.config import Config
from pymongo import MongoClient
import pprint
import re
from datetime import datetime
import json

### connection
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles

## collections used
snapshot = "itpp_snapshot_test3"

## establish connections to collections
snapshotCollection=myDatabase[snapshot]

def snapshotSummary():
    try:
        pipeline = []

        group_stage = {
            '$group': {
                '_id': {
                    'bodysession': '$bodysession', 
                    'record_date': {'$substrCP': ['$snapshottime', 0, 10]}, 
                    'record_type': '$record_type'
                }, 
                'count': {'$sum': 1}
            }
        }

        project_stage = {
            '$project': {
                '_id': 0, 
                'bodysession': '$_id.bodysession', 
                'snapshot_date': '$_id.record_date', 
                'record_type': '$_id.record_type',
                'count': 1
            }
        }

        sort_stage = {
            '$sort': {
                'bodysession': 1, 
                'snapshot_date': 1,
                'record_type': 1
            }
        }

        pipeline.append(group_stage)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)

        summary = list(snapshotCollection.aggregate(pipeline))

        return summary

    except Exception as e:
        return e

def deleteSnapshot(bodysession):
    try:
        results = snapshotCollection.delete_many({'bodysession': bodysession})

        msg = "Deleted " + str(results.deleted_count) + "from " + bodysession

        return msg

    except Exception as e:
        return e

def snapshotDropdown():
    try:
        pipeline = []

        group_stage = {
            '$group': {
                '_id': '$bodysession'
            }
        }
    
        project_stage = {
            '$project': {
                '_id': 0, 
                'bodysession': '$_id'
            }
        }

        sort_stage = {
            '$sort': {
                'bodysession': 1
            }
        }

        pipeline.append(group_stage)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)

        dropdown = list(snapshotCollection.aggregate(pipeline))

        return dropdown

    except Exception as e:
        return e