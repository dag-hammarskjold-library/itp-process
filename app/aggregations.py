from app.config import Config
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
###
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles
inputCollection=myDatabase['itpp_snapshot_test3']
outputCollection=myDatabase['itp_sample_output']
copyCollection=myDatabase['itp_sample_output_copy']

def clear_section(section, bodysession):
    """
    Removes all records from the collection for a certain section

    :Parameters:
        - 'section': Section of documents to delete. 
        - 'bodysession': Bodysession of documents to delete.

    :Returns:
        - number of records deleted
    """

    deleted = copyCollection.delete_many({ "section" : section, "bodysession" : bodysession } )

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
            #'035.a': {'$regex': re.compile(r"Q*")}, 
            'record_type': "ITS",
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
            'bodysession': 1,
            'record_id': 1
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
                        ' (Agenda item ', 
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
            #'035.a': {'$regex': re.compile(r"Q*")}, 
            'record_type': "ITS",
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
            'bodysession': 1,
            'record_id': 1
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
                        ' (Agenda item ', 
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
            #'035.a': {'$regex': re.compile(r"Q*")}, 
            'record_type': "ITS",
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
            'bodysession': 1,
            'record_id': 1
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
        transform['itshead'] = {
                    '$concat': [
                        '$991.d', 
                        ' (Agenda item ', 
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

def group_speeches(section, bodysession):
    pipeline = []

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            'section': section
        }
    }
    
    sort_stage = {
        '$sort': {
            'itshead': 1, 
            'itssubhead': 1, 
            'itsentry': 1, 
            'docsymbol': 1
        }
    }
    
    group_stage1 = {
        '$group': {
            '_id': {
                'itshead': '$itshead', 
                'itsubhead': '$itssubhead', 
                'itsentry': '$itsentry', 
                'docsymbol': '$docsymbol'
            }
        }
    }
    
    group_stage2 = {
        '$group': {
            '_id': {
                'itshead': '$_id.itshead', 
                'itsubhead': '$_id.itsubhead', 
                'itsentry': '$_id.itsentry'
            }, 
            'docsymbols': {
                '$push': '$_id.docsymbol'
            }
        }
    }
    
    group_stage3 = {
        '$group': {
            '_id': {
                'itshead': '$_id.itshead', 
                'itsubhead': '$_id.itsubhead'
            }, 
            'itsentries': {
                '$push': {
                    'itsentry': '$_id.itsentry', 
                    'docsymbols': '$docsymbols'
                }
            }
        }
    }
    
    group_stage4 = {
        '$group': {
            '_id': {
                'itshead': '$_id.itshead'
            }, 
            'subheading': {
                '$push': {
                    'itssubhead': '$_id.itsubhead', 
                    'itsentries': '$itsentries'
                }
            }
        }
    }
    
    project_stage = {
        '$project': {
            '_id': 0,
            'itshead': '$_id.itshead',
            'bodysession': bodysession, 
            'section': section, 
            'subheading': 1
        }
    }

    merge_stage = {
        '$merge': { 'into': "itp_sample_output_copy"}
    }

    pipeline.append(match_stage)
    pipeline.append(sort_stage)
    pipeline.append(group_stage1)
    pipeline.append(group_stage2)
    pipeline.append(group_stage3)
    pipeline.append(group_stage4)
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    outputCollection.aggregate(pipeline)

def execute_itpres(section, bodysession):
    pipeline = []

    bs = bodysession.split("/")
    body = bs[0]
    session = bs[1]

    match_stage1 = {
        '$match': {
            'record_type': 'BIB',
            '$or': [{'191.9': 'G99'}, {'191.9': 'X99'}, {'191.9': 'C99'}]}
            }

    unwind_stage1 = {'$unwind': '$191'}
    unwind_stage2 = {'$unwind': '$991'}

    match_stage2 = {
        '$match': {
            '191.b': body + "/",
            '191.c': session}
            }

    addfields_stage = {
        '$addFields': {
            'decision': '$996.a',
            'votedate': {'$split': ['$992.a', '-']}}}

    transform = {}
    transform['_id'] = 0
    transform['record_id'] = 1
    transform['section'] = "itpres"
    transform['bodysession'] = 1
    transform['docsymbol'] = '$191.a'
    transform['ainumber'] = { 
        '$cond': {
            'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]},
            'then': '$991.b',
            'else': {'$substrCP': ['$991.b', 1, {'$subtract': [{'$indexOfCP': ['$991.b', ']']}, 1]}]}}
    }
    transform['vote'] = {
        '$let': {
            'vars': {   
                'decision': 1,   
                'w': {'$indexOfCP': ['$decision', 'without' ]},   
                'u': {'$indexOfCP': ['$decision', 'unanimously' ]},   
                'x': {'$indexOfCP': ['$decision', '(' ]},   
                'y': {'$indexOfCP': ['$decision', ')' ]},   
                'a': {'$indexOfCP': ['$decision', ' ' ]},   
                'b': {'$indexOfCP': ['$decision', ',' ]}},
        'in': {   
            '$switch': {   
                'branches': [
                    {'case': {'$gt': ['$$w', -1]}, 'then': 'without vote'}, 
                    {'case': {'$gt': ['$$u', -1]}, 'then': 'Unanimous'}, 
                    {'case': {'$gt': ['$$x', -1]}, 'then': {'$substrCP': ['$decision', {'$add': ['$$x', 1 ]}, {'$subtract': [{'$subtract': ['$$y', '$$x'] }, 1 ]}]}}],   
                'default': {'$substrCP': ['$decision', {'$add': ['$$a', 1]}, {'$subtract': [{'$subtract': ['$$b', '$$a']}, 1]}]}
                }
            }
        }
    }
               

    if body == "S":
        transform['subject'] = {
        '$cond': {
            'if': {'$eq': ['$991.z', 'I']},
            'then': '$991.d', 
            'else': ''}
        }
    
        transform['subjectsubtitle'] = {
            '$let': {
                'vars': {
                    'a': {'$indexOfCP': ['$239.a', '[']}, 
                    'b': {'$indexOfCP': ['$239.a', ']']}
                }, 
            'in': {
                '$concat': [
                    '[', 
                    {'$toUpper': {'$substrCP': ['$239.a', {'$add': ['$$a', 4]}, 1]}}, 
                    {'$substrCP': ['$239.a', {'$add': ['$$a', 5]}, '$$b']}
                    ]
            }
            }
        }

        transform['votedate']= {
            '$let': {
                'vars': {
                    'testMonth': {'$arrayElemAt': ['$votedate', 1]},   
                    'testDate': {'$arrayElemAt': ['$votedate', 2]}
                    },
                'in': {   
                    '$switch': {   
                        'branches': [
                            {'case': {'$eq': ['$$testMonth', '01']}, 'then': {'$concat': ['$$testDate', ' ', 'Jan.']}}, 
                            {'case': {'$eq': ['$$testMonth', '02']}, 'then': {'$concat': ['$$testDate', ' ', 'Feb.']}}, 
                            {'case': {'$eq': ['$$testMonth', '03']}, 'then': {'$concat': ['$$testDate', ' ', 'Mar.']}}, 
                            {'case': {'$eq': ['$$testMonth', '04']}, 'then': {'$concat': ['$$testDate', ' ', 'Apr.']}}, 
                            {'case': {'$eq': ['$$testMonth', '05']}, 'then': {'$concat': ['$$testDate', ' ', 'May']}}, 
                            {'case': {'$eq': ['$$testMonth', '06']}, 'then': {'$concat': ['$$testDate', ' ', 'June']}}, 
                            {'case': {'$eq': ['$$testMonth', '07']}, 'then': {'$concat': ['$$testDate', ' ', 'July']}}, 
                            {'case': {'$eq': ['$$testMonth', '08']}, 'then': {'$concat': ['$$testDate', ' ', 'Aug.']}}, 
                            {'case': {'$eq': ['$$testMonth', '09']}, 'then': {'$concat': ['$$testDate', ' ', 'Sept.']}}, 
                            {'case': {'$eq': ['$$testMonth', '10']}, 'then': {'$concat': ['$$testDate', ' ', 'Oct.']}}, 
                            {'case': {'$eq': ['$$testMonth', '11']}, 'then': {'$concat': ['$$testDate', ' ', 'Nov.']}}, 
                            {'case': {'$eq': ['$$testMonth', '12']}, 'then': {'$concat': ['$$testDate', ' ', 'Dec.']}}],   
                        'default': 'Did not match'}}}
        }
        
        transform['meeting'] = {
            '$concat': ['$191.b', 
                        '$191.c', 
                        '/PV.', 
                        {'$substr': [{'$arrayElemAt': [{'$split': ['$996.a', ' '] }, 2]}, 0, {'$subtract': [{'$strLenCP': {'$arrayElemAt': [{'$split': ['$996.a', ' ']}, 2]} }, 2]}]}]   
        }   
        
                
    else:
        transform['title'] = {
            '$cond': {
                'if': {'$eq': [{'$indexOfCP': ['$245.a', ' :']}, -1]},
                'then': '',
                'else': {'$substrCP': ['$245.a', 0, {'$indexOfCP': ['$245.a', ' :']}]}}}
                        
        transform['votedate'] = {    
            '$let': {
                'vars': {   
                    'testMonth': {'$arrayElemAt': ['$votedate', 1 ] },   
                    'testDate': {'$arrayElemAt': ['$votedate', 2 ] },   
                    'testYear': {'$arrayElemAt': ['$votedate', 0 ] }},
                'in': {   
                    '$switch': {   
                        'branches': [
                            {'case': {'$eq': ['$$testMonth', '01']},  'then': {'$concat': ['$$testDate', ' ', 'Jan.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '02']},  'then': {'$concat': ['$$testDate', ' ', 'Feb.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '03']},  'then': {'$concat': ['$$testDate', ' ', 'Mar.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '04']},  'then': {'$concat': ['$$testDate', ' ', 'Apr.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '05']},  'then': {'$concat': ['$$testDate', ' ', 'May', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '06']},  'then': {'$concat': ['$$testDate', ' ', 'June', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '07']},  'then': {'$concat': ['$$testDate', ' ', 'July', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '08']},  'then': {'$concat': ['$$testDate', ' ', 'Aug.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '09']},  'then': {'$concat': ['$$testDate', ' ', 'Sept.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '10']},  'then': {'$concat': ['$$testDate', ' ', 'Oct.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '11']},  'then': {'$concat': ['$$testDate', ' ', 'Nov.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}, 
                            {'case': {'$eq': ['$$testMonth', '12']},  'then': {'$concat': ['$$testDate', ' ', 'Dec.', ' ', {'$substrCP': ['$$testYear', 2, 2 ] }]}}],   
                        'default': 'Did not match'}}
            }
        }
 
        transform['meeting'] = { 
            '$switch': {
                'branches': [   
                    {'case': {'$eq': ['$191.b', 'E/']}, 'then': {'$concat': ['$191.b', {'$substrCP': ['$191.c', 0, 4]}, '/PV.', {'$substr': [ { '$arrayElemAt': [ {'$split': ['$996.a', ' '] }, 3 ] }, 0, { '$subtract': [ {'$strLenCP': {'$arrayElemAt': [{'$split': ['$996.a', ' ']}, 3]} }, 2 ] }]}]}}, 
                    {'case': {'$eq': ['$191.b', 'A/']}, 'then': {'$concat': ['$191.b', '$191.c', '/PV.', {'$substr': [ { '$arrayElemAt': [ {'$split': ['$996.a', ' '] }, 3 ] }, 0, { '$subtract': [ {'$strLenCP': {'$arrayElemAt': [{'$split': ['$996.a', ' ']}, 3]} }, 2 ] }]}]}}]
            }
        }
                              
    transform_stage = {}
    transform_stage['$project'] = transform
                    
    merge_stage = {
        '$merge': { 'into': "itp_sample_output_copy"}
    }

    pipeline.append(match_stage1)
    pipeline.append(unwind_stage1)
    pipeline.append(unwind_stage2)
    pipeline.append(match_stage2)
    pipeline.append(addfields_stage)
    pipeline.append(transform_stage)
    pipeline.append(merge_stage)
 
 
    inputCollection.aggregate(pipeline)

""" clear_section("itpres", "S/72")
clear_section("itpres", "A/72")
clear_section("itpres", "E/2018-S")

execute_itpres("itpres", "S/72")
execute_itpres("itpres", "A/72")
execute_itpres("itpres", "E/2018-S") """

""" group_speeches("itpitss", "A/72")
group_speeches("itpitss", "S/72")
group_speeches("itpitss","E/2018-S")

group_speeches("itpitsc", "S/72")
group_speeches("itpitsc","E/2018-S")
group_speeches("itpitsc", "A/72") 

group_speeches("itpitsp", "S/72")
group_speeches("itpitsp","E/2018-S")
group_speeches("itpitsp", "A/72") """

""" clear_section("itpitsc", "S/72")
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
execute_itpitss("E/2018-S") """