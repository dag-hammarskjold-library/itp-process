#from app.config import Config
from pymongo import MongoClient
import pprint
import re


""" DB.connect(Config.connect_string)
db_client=MongoClient(Config.connect_string)
db=db_client['undlFiles']
rules_coll = db['itpp_rules']
snapshot_coll=db['itpp_snapshot_test3']
itp_bib_fields=[]
"""

myMongoURI=''
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles
inputCollection=myDatabase['itpp_snapshot_test3']
outputCollection=myDatabase['itp_sample_output']

def clear_section(section, bodysession):
    """
    Removes all records from the collection for a certain section

    :Parameters:
        - 'section': Section of documents to delete. 
        - 'bodysession': Bodysession of documents to delete.

    :Returns:
        - number of records deleted
    """

    deleted = outputCollection.delete_many({ "section" : section, "bodysession" : bodysession } )

    print(deleted.deleted_count, "documents deleted.")

 

def execute_itpitsc(bodysession):
    """
    Index to Speeches - Country / Corporate

    Builds the aggregation query and inserts the results into another collection.
    """ 

    pipeline = []

    bs = bodysession.split("/")
    body = bs[0]

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            '035.a': {'$regex': re.compile(r"Q*")}, 
            '$or': [
                {'710.a': {'$ne': ''}, 
                '711.a': {'$ne': ''}}], 
            '700.a': {'$ne': ''}, 
            '791.a': {'$ne': ''}, 
            '991.d': {'$ne': ''}
        }
    }

    project_stage = {
        '$project': {
            '700': 1, 
            '710': 1, 
            '711': 1, 
            '791': {
                '$cond': {
                    'if': {'$isArray': '$791'}, 
                    'then': {
                        '$filter': {
                            'input': '$791', 
                            'as': 'item', 
                            'cond': {'$gt': [{'$indexOfCP': ['$$item.a', body]}, -1]}
                        }
                    }, 
                    'else': '$791'
                }
            }, 
            '991': {
                '$cond': {
                    'if': {'$isArray': '$991'}, 
                    'then': {
                        '$filter': {
                            'input': '$991', 
                            'as': 'item', 
                            'cond': {'$gt': [{'$indexOfCP': ['$$item.a', body]}, -1]}
                        }
                    }, 
                    'else': '$991'
                }
            }, 
            'bodysession': 1
        }
    }

    unwind_stage1 = {'$unwind': '$991'}
    unwind_stage2 = {'$unwind': '$791'}

    transform = {}
    transform['_id'] = 0
    transform['record_id'] = 1
    transform['section'] = "itpitsc"
    transform['bodysession'] = 1
    transform['itshead'] = {
                '$cond': {
                    'if': {'$ne': ['$710', '']}, 
                    'then': '$710.a', 
                    'else': '$711.a'
                }
            }
    
    if body == "S":
        transform['itssubhead'] = '$991.d'
    else:
        transform['itssubhead'] = {
                    '$concat': [
                        '$991.d', 
                        ' (Agenda Item ', 
                        {'$cond': {
                            'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]},
                            'then':'$991.b', 
                            'else': {'$substrCP': ['$991.b', 0, {'$indexOfCP': ['$991.b', '[']}]}}
                        },
                        ')'
                    ]
                }

    transform['itsentry'] = {
                '$cond': {
                    'if': '$700.g', 
                    'then': {'$concat': ['$700.a', ' ', '$700.g']}, 
                    'else': '$700.a'
                }
            }

    transform['docsymbol'] = '$791.a'

    transform_stage = {}
    transform_stage['$project'] = transform

    merge_stage = {
        '$merge': { 'into': "itp_sample_output"}
    }

    pipeline.append(match_stage)
    pipeline.append(project_stage)
    pipeline.append(unwind_stage1)
    pipeline.append(unwind_stage2)
    pipeline.append(transform_stage)
    pipeline.append(merge_stage)
 
    inputCollection.aggregate(pipeline)
    
def execute_itpitsp(bodysession):
    """
    Index to Speeches - Speakers

    Builds the aggregation query and inserts the results into another collection.
    """ 

    pipeline = []

    bs = bodysession.split("/")
    body = bs[0]

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            '035.a': {'$regex': re.compile(r"Q*")}, 
            '$or': [
                {'710.a': {'$ne': ''}, 
                '711.a': {'$ne': ''}}], 
            '700.a': {'$ne': ''}, 
            '791.a': {'$ne': ''}, 
            '991.d': {'$ne': ''}
        }
    }

    project_stage = {
        '$project': {
            '700': 1, 
            '710': 1, 
            '711': 1, 
            '791': {
                '$cond': {
                    'if': {'$isArray': '$791'}, 
                    'then': {
                        '$filter': {
                            'input': '$791', 
                            'as': 'item', 
                            'cond': {'$gt': [{'$indexOfCP': ['$$item.a', body]}, -1]}
                        }
                    }, 
                    'else': '$791'
                }
            }, 
            '991': {
                '$cond': {
                    'if': {'$isArray': '$991'}, 
                    'then': {
                        '$filter': {
                            'input': '$991', 
                            'as': 'item', 
                            'cond': {'$gt': [{'$indexOfCP': ['$$item.a', body]}, -1]}
                        }
                    }, 
                    'else': '$991'
                }
            }, 
            'bodysession': 1
        }
    }

    unwind_stage1 = {'$unwind': '$991'}
    unwind_stage2 = {'$unwind': '$791'}

    transform = {}
    transform['_id'] = 0
    transform['record_id'] = 1
    transform['section'] = "itpitsp"
    transform['bodysession'] = 1

    transform['itshead'] = { 
            '$concat': [        
              {'$cond': {        
                'if': '$700.g',        
                'then': {'$concat': ['$700.a', ' ', '$700.g' ]}, 
                'else': '$700.a'}},          
              ' (',         
              {'$cond': {         
              'if': {'$ne': ["$710", '']},         
              'then': "$710.a",         
              'else': "$711.a"}},         
            ')' ]}
    
    if body == "S":
        transform['itssubhead'] = '$991.d'
    else:
        transform['itssubhead'] = {
                    '$concat': [
                        '$991.d', 
                        ' (Agenda Item ', 
                        {'$cond': {
                            'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]},
                            'then':'$991.b', 
                            'else': {'$substrCP': ['$991.b', 0, {'$indexOfCP': ['$991.b', '[']}]}}
                        },
                        ')'
                    ]
                }


    transform['docsymbol'] = '$791.a'

    transform_stage = {}
    transform_stage['$project'] = transform

    merge_stage = {
        '$merge': { 'into': "itp_sample_output"}
    }

    pipeline.append(match_stage)
    pipeline.append(project_stage)
    pipeline.append(unwind_stage1)
    pipeline.append(unwind_stage2)
    pipeline.append(transform_stage)
    pipeline.append(merge_stage)
 
    inputCollection.aggregate(pipeline)

    
def execute_itpitss(bodysession):
    """
    Index to Speeches - Subjects

    Builds the aggregation query and inserts the results into another collection.
    """ 

    pipeline = []

    bs = bodysession.split("/")
    body = bs[0]

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            '035.a': {'$regex': re.compile(r"Q*")}, 
            '$or': [
                {'710.a': {'$ne': ''}, 
                '711.a': {'$ne': ''}}], 
            '700.a': {'$ne': ''}, 
            '791.a': {'$ne': ''}, 
            '991.d': {'$ne': ''}
        }
    }

    project_stage = {
        '$project': {
            '700': 1, 
            '710': 1, 
            '711': 1, 
            '791': {
                '$cond': {
                    'if': {'$isArray': '$791'}, 
                    'then': {
                        '$filter': {
                            'input': '$791', 
                            'as': 'item', 
                            'cond': {'$gt': [{'$indexOfCP': ['$$item.a', body]}, -1]}
                        }
                    }, 
                    'else': '$791'
                }
            }, 
            '991': {
                '$cond': {
                    'if': {'$isArray': '$991'}, 
                    'then': {
                        '$filter': {
                            'input': '$991', 
                            'as': 'item', 
                            'cond': {'$gt': [{'$indexOfCP': ['$$item.a', body]}, -1]}
                        }
                    }, 
                    'else': '$991'
                }
            }, 
            'bodysession': 1
        }
    }

    unwind_stage1 = {'$unwind': '$991'}
    unwind_stage2 = {'$unwind': '$791'}

    transform = {}
    transform['_id'] = 0
    transform['record_id'] = 1
    transform['section'] = "itpitss"
    transform['bodysession'] = 1

    
    if body == "S":
        transform['itshead'] = '$991.d'
    else:
        transform['ithead'] = {
                    '$concat': [
                        '$991.d', 
                        ' (Agenda Item ', 
                        {'$cond': {
                            'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]},
                            'then':'$991.b', 
                            'else': {'$substrCP': ['$991.b', 0, {'$indexOfCP': ['$991.b', '[']}]}}
                        },
                        ')'
                    ]
                }
    transform['itssubhead'] =  {
                '$cond': {
                    'if': {'$ne': ['$710', '']}, 
                    'then': '$710.a', 
                    'else': '$711.a'
                }
            }
    
    transform['itsentry'] = {
                '$cond': {
                    'if': '$700.g', 
                    'then': {'$concat': ['$700.a', ' ', '$700.g']}, 
                    'else': '$700.a'
                }
            }

    transform['docsymbol'] = '$791.a'

    transform_stage = {}
    transform_stage['$project'] = transform

    merge_stage = {
        '$merge': { 'into': "itp_sample_output"}
    }

    pipeline.append(match_stage)
    pipeline.append(project_stage)
    pipeline.append(unwind_stage1)
    pipeline.append(unwind_stage2)
    pipeline.append(transform_stage)
    pipeline.append(merge_stage)
 
    inputCollection.aggregate(pipeline)

clear_section("itpitsc", "S/72")
execute_itpitsc("S/72")

clear_section("itpitsc", "A/72")
execute_itpitsc("A/72")

clear_section("itpitsc", "E/2018-S")
execute_itpitsc("E/2018-S")

clear_section("itpitsp", "A/72")
execute_itpitsp("A/72")

clear_section("itpitsp", "S/72")
execute_itpitsp("S/72")

clear_section("itpitsp", "E/2018-S")
execute_itpitsp("E/2018-S")

clear_section("itpitss", "A/72")
execute_itpitss("A/72")

clear_section("itpitss", "S/72")
execute_itpitss("S/72")

clear_section("itpitss", "E/2018-S")
execute_itpitss("E/2018-S")

#


""" class Aggregation(object):
    def __init__(self):
        self.bodysession = None
        self.stages = []
        '''
        self.match_stage = None
        self.project_stage = None
        self.unwind_stage = []
        self.transform_stage = None
        self.merge_stage = None
        '''
    
    def exec(self):
        for stage in self.stages:
            stage.exec()
            # Wrap in try ... except and return status.


class Stage(object):
    def __init__(self):
        self.stage_type = None

    def exec(self):
        # do the work
        pass

class MatchStage(Stage):
    # any init data

    def foo(self):
        return 'bar' """