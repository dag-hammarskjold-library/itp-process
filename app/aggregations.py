from app.config import Config
from pymongo import MongoClient
import pprint
import re
from datetime import datetime

### connection
myMongoURI=Config.connect_string
myClient = MongoClient(myMongoURI)
myDatabase=myClient.undlFiles

## collections used
snapshot = "itpp_snapshot_test3"
editorOutput = "itp_sample_output"
wordOutput = "itp_sample_output_copy"
lookup = "itp_codes"

## establish connections to collections
inputCollection=myDatabase[snapshot]
outputCollection=myDatabase[editorOutput]
copyCollection=myDatabase[wordOutput]
lookupCollection=myDatabase[lookup]


#### Data transformations for each section ####

# Index to Speeches - Country / Corporate #
def itpitsc(bodysession):
    """
    Index to Speeches - Country / Corporate

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try:
        outputCollection.delete_many({ "section" : "itpitsc", "bodysession" : bodysession } )

        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        match_stage1 = {
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

        unwind_stage1 = {'$unwind': '$991'}
        unwind_stage2 = {'$unwind': '$791'}

        if body == "A": 
            match_stage2 = {
                '$match': {
                    '791.b': 'A/', 
                    '991.a': {
                        '$regex': '^A'
                    }
            }
        }

        if body == "S":
            match_stage2 = {
                '$match': {
                    '791.b': 'S/', 
                    '991.a': {
                        '$regex': '^S'
                    }
            }
        }

        if body == "E":    
            match_stage2 = {
                '$match': {
                    '791.b': 'E/', 
                    '991.a': {
                        '$regex': '^E'
                    }
            }
        }

        add_1 = {}
        add_1['section'] = "itpitsc" 
        add_1['itshead'] = {
            '$cond': {
                'if': {'$ne': ['$710', '']}, 
                'then': { 
                    '$cond': { 
                        'if': {'$isArray': '$710' }, 
                        'then': {'$arrayElemAt': [ '$710.a', 0]},
                        'else': "$710.a"}}, 
                'else': '$711.a'
            }
        }
        
        if body == "S":
            add_1['itssubhead'] = '$991.d'
        else:
            add_1['itssubhead'] = {
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

        add_1['itsentry'] = {
            '$cond': {
                'if': '$700.g', 
                'then': {'$concat': ['$700.a', ' ', '$700.g']}, 
                'else': '$700.a'
            }
        }

        add_1['docsymbol'] = '$791.a'

        add_stage = {}
        add_stage['$addFields'] = add_1


        project_stage = {
            '$project': {
                '_id': 0, 
                'record_id': 1, 
                'section': 1, 
                'bodysession': 1, 
                'itshead': 1, 
                'itssubhead': 1, 
                'itsentry': 1, 
                'docsymbol': 1, 
                'sortkey1': {
                    '$concat': [
                        { '$toUpper': '$itshead' }, 
                        "+",
                        '$itssubhead']},
                'sortkey2': '$itsentry', 
                'sortkey3': '$docsymbol'
            }
        }

        sort_stage = {
            '$sort': {
                'sortkey1': 1, 
                'sortkey2': 1, 
                'sortkey3': 1
            }
        }

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage1)
        pipeline.append(unwind_stage1)
        pipeline.append(unwind_stage2)
        pipeline.append(match_stage2)
        pipeline.append(add_stage)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)
    
        pipeline.append(merge_stage)


    
        inputCollection.aggregate(pipeline, collation=collation)

        group_speeches("itpitsc", bodysession)

        return "itpitsc completed successfully"
    
    except Exception as e:
        return e

# Index to Speeches - Speakers #   
def itpitsp(bodysession):
    """
    Index to Speeches - Speakers

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try:
        
        outputCollection.delete_many({ "section" : "itpitsp", "bodysession" : bodysession } )

        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        match_stage1 = {
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

        unwind_stage1 = {'$unwind': '$991'}
        unwind_stage2 = {'$unwind': '$791'}

        if body == "A": 
            match_stage2 = {
                '$match': {
                    '791.b': 'A/', 
                    '991.a': {
                        '$regex': '^A'
                    }
            }
        }

        if body == "S":
            match_stage2 = {
                '$match': {
                    '791.b': 'S/', 
                    '991.a': {
                        '$regex': '^S'
                    }
            }
        }

        if body == "E":    
            match_stage2 = {
                '$match': {
                    '791.b': 'E/', 
                    '991.a': {
                        '$regex': '^E'
                    }
                }
            }
         
        add_1 = {}
        add_1['section'] = "itpitsp"

        add_1['itshead'] = { 
                '$concat': [        
                {'$cond': {        
                    'if': '$700.g',        
                    'then': {'$concat': ['$700.a', ' ', '$700.g' ]}, 
                    'else': '$700.a'}},          
                ' (',         
                {'$cond': {
                    'if': {'$ne': ['$710', '']}, 
                    'then': { 
                        '$cond': { 
                            'if': {'$isArray': '$710' }, 
                            'then': {'$arrayElemAt': [ '$710.a', 0]},
                            'else': "$710.a"}}, 
                    'else': '$711.a'
                }},         
                ')' ]}
        
        if body == "S":
            add_1['itssubhead'] = '$991.d'
        else:
            add_1['itssubhead'] = {
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


        add_1['docsymbol'] = '$791.a'

        add_stage = {}
        add_stage['$addFields'] = add_1

        project_stage = {
            '$project': {
                '_id': 0, 
                'record_id': 1, 
                'section': 1, 
                'bodysession': 1, 
                'itshead': 1, 
                'itssubhead': 1, 
                'itsentry': 1, 
                'docsymbol': 1, 
                'sortkey1': {
                    '$concat': [
                        { '$toUpper': '$itshead' }, 
                        "+",
                        '$itssubhead']},
                'sortkey2': '$itsentry', 
                'sortkey3': '$docsymbol'
            }
        }

        sort_stage = {
            '$sort': {
                'sortkey1': 1, 
                'sortkey2': 1, 
                'sortkey3': 1
            }
        }

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage1)
        pipeline.append(unwind_stage1)
        pipeline.append(unwind_stage2)
        pipeline.append(match_stage2)
        pipeline.append(add_stage)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)
    
        pipeline.append(merge_stage)
    
        #print(pipeline)

        inputCollection.aggregate(pipeline, collation=collation)

        group_speeches("itpitsp", bodysession)

        return "itpitsp completed successfully"
    
    except Exception as e:
        return e
  
# Index to Speeches - Subjects # 
def itpitss(bodysession):
    """
    Index to Speeches - Subjects

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try:
        
        outputCollection.delete_many({ "section" : "itpitss", "bodysession" : bodysession } )

        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]
        
        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        match_stage1 = {
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

        unwind_stage1 = {'$unwind': '$991'}

        unwind_stage2 = {'$unwind': '$791'}

        if body == "A": 
            match_stage2 = {
                '$match': {
                    '791.b': 'A/', 
                    '991.a': {
                        '$regex': '^A'
                    }
            }
        }

        if body == "S":
            match_stage2 = {
                '$match': {
                    '791.b': 'S/', 
                    '991.a': {
                        '$regex': '^S'
                    }
            }
        }

        if body == "E":    
            match_stage2 = {
                '$match': {
                    '791.b': 'E/', 
                    '991.a': {
                        '$regex': '^E'
                    }
            }
        }

        add_1 = {}
        add_1['section'] = "itpitss"
        
        if body == "S":
            add_1['itshead'] = '$991.d'
        else:
            add_1['itshead'] = {
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

        add_1['itssubhead'] =  {
            '$cond': {
                'if': {'$ne': ['$710', '']}, 
                'then': { 
                    '$cond': { 
                        'if': {'$isArray': '$710' }, 
                        'then': {'$arrayElemAt': [ '$710.a', 0]},
                        'else': "$710.a"}}, 
                'else': '$711.a'
            }
        }
        
        add_1['itsentry'] = {
            '$cond': {
                'if': '$700.g', 
                'then': {'$concat': ['$700.a', ' ', '$700.g']}, 
                'else': '$700.a'
            }
        }

        add_1['docsymbol'] = '$791.a'

        add_stage = {}
        add_stage['$addFields'] = add_1

        project_stage = {
            '$project': {
                '_id': 0, 
                'record_id': 1, 
                'section': 1, 
                'bodysession': 1, 
                'itshead': 1, 
                'itssubhead': 1, 
                'itsentry': 1, 
                'docsymbol': 1, 
                'sortkey1': {
                    '$concat': [
                        { '$toUpper': '$itshead' }, 
                        "+",
                        '$itssubhead']},
                'sortkey2': '$itsentry', 
                'sortkey3': '$docsymbol'
            }
        }

        sort_stage = {
            '$sort': {
                'sortkey1': 1, 
                'sortkey2': 1, 
                'sortkey3': 1
            }
        }

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage1)
        pipeline.append(unwind_stage1)
        pipeline.append(unwind_stage2)
        pipeline.append(match_stage2)
        pipeline.append(add_stage)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)
    
        pipeline.append(merge_stage)

        inputCollection.aggregate(pipeline, collation=collation)

        group_speeches("itpitss", bodysession)

        return "itpitss completed successfully"

    except Exception as e:
        return e

# Index to Speeches - Subjects #
def itpres(bodysession):
    """
    List of Resolutions

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try:
        
        outputCollection.delete_many({ "section" : "itpres", "bodysession" : bodysession } )

        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]
        session = bs[1]

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

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
                '191.c': session, 
                '991.z': "I"
            }
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
            transform['ainumber'] = {
                '$cond': {
                    'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]}, 
                    'then': '$991.b', 
                    'else': {'$substrCP': ['$991.b', 1, {'$subtract': [{'$indexOfCP': ['$991.b', ']']}, 1]}]}
                }
            }

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
                        'testDate': { '$ltrim': { 'input': {'$arrayElemAt': ['$votedate', 2]},  'chars': '0' } }
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
                '$concat': [
                    '$191.b', 
                    {'$substrCP': ['$191.c', 0, 4]}, 
                    '/PV.', 
                    {'$let': {
                        'vars': {
                            'e': {'$arrayElemAt': [
                                {'$split': ['$996.a', ' ']}, 
                                {'$subtract': [{'$indexOfArray': [{'$split': ['$996.a', ' ']}, 'meeting']}, 1]}]}
                        }, 
                        'in': {
                            '$substrCP': ['$$e', 0, {'$subtract': [{'$strLenCP': '$$e'}, 2]}]
                        }}
                    }
                ]
            }
                    
        else:
            transform['ainumber'] = {
                '$cond': {
                    'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]},
                    'then':'$991.b', 
                    'else': {'$substrCP': [ '$991.b', 0, {'$indexOfCP': [ '$991.b', '['] }]}  
                }
            }

            transform['title'] = { 
                '$cond': { 
                    'if': '$245.a', 
                    'then': {
                        '$cond': {
                            'if': {'$eq': [{'$indexOfCP': ['$245.a', ' :']}, -1]},
                            'then': '$245.a',
                            'else': {'$substrCP': ['$245.a', 0, {'$indexOfCP': ['$245.a', ' :']}]}}}, 
                    'else': '' 
                } 
            }
                            
            transform['votedate'] = {    
                '$let': {
                    'vars': {   
                        'testMonth': {'$arrayElemAt': ['$votedate', 1 ] },   
                        'testDate': { '$ltrim': { 'input': {'$arrayElemAt': ['$votedate', 2]},  'chars': '0' } },   
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
                '$concat': [
                    '$191.b', 
                    {'$substrCP': ['$191.c', 0, 4]}, 
                    '/PV.', 
                    {'$let': {
                        'vars': {
                            'e': {'$arrayElemAt': [
                                {'$split': ['$996.a', ' ']}, 
                                {'$subtract': [{'$indexOfArray': [{'$split': ['$996.a', ' ']}, 'plenary']}, 1]}]}
                        }, 
                        'in': {
                            '$substrCP': ['$$e', 0, {'$subtract': [{'$strLenCP': '$$e'}, 2]}]
                        }}
                    }
                ]
            }

        transform['sortkey1'] = '$191.a'

        transform_stage = {}
        transform_stage['$project'] = transform
                        
        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage1)
        pipeline.append(unwind_stage1)
        pipeline.append(unwind_stage2)
        pipeline.append(match_stage2)
        pipeline.append(addfields_stage)
        pipeline.append(transform_stage)
        pipeline.append(merge_stage)

        #print(pipeline)

        inputCollection.aggregate(pipeline, collation=collation)

        copyPipeline = []

        copyMatch_stage = {
            '$match': {
                'bodysession': bodysession, 
                'section': "itpres"
            }
        }

        copyMerge_stage = {
            '$merge': { 'into': wordOutput}
        }
        
        clear_section("itpres", bodysession)

        copyPipeline.append(copyMatch_stage)
        copyPipeline.append(copyMerge_stage)

        outputCollection.aggregate(copyPipeline)

        return "itpres completed successfully"
    
    except Exception as e:
        return e    

# Subject Index #
def itpsubj(bodysession):
    """
    Subject Index

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 

        #clear the previous records if they exist
        outputCollection.delete_many({ "section" : "itpsubj", "bodysession" : bodysession } )

        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]
        fullbody = body + "/"
        session = bs[1]

        empty_string = ''

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        match_stage = {
            '$match': {
                'bodysession': bodysession, 
                'record_type': "BIB"
            }
        }

        unwind_stage = {'$unwind': '$991'}
        
        if body == "S":
            match_stage2 = {
                '$match': {
                    '991.z': "I",
                    '991.a' : {'$regex': "^S"}
                }
            }

        if body == "A":
            match_stage2 = {
                '$match': {
                    '991.z': "I",
                    '991.a' : {'$regex': "^A"}
                }
            }

        if body == "E":
            match_stage2 = {
                '$match': {
                    '991.z': "I",
                    '991.a' : {'$regex': "^E"}
                }
            }

        add_1 = {}

        #body == A
        if body == "A":
            add_1['title_case1'] = {
            '$cond': { 
                'if': {'$and': [
                    {'$gt': [{ '$indexOfCP': ['$245.b', 'report of the' ]}, -1]}, 
                    {'$and': [
                        { '$gt': [{'$indexOfCP': ['$245.b', 'Committee']}, -1 ]}, 
                        { '$gt': [{'$indexOfCP': ['$245.b', 'General']}, -1 ]}]}, 
                        {'$or': [
                            { '$eq': ['$191.9', 'G11' ]}, 
                            { '$eq': ['$191.9', 'G22' ]}, 
                            { '$eq': ['$191.9', 'G33' ]}, 
                            { '$eq': ['$191.9', 'G14' ]}, 
                            { '$eq': ['$191.9', 'G55' ]}, 
                            { '$eq': ['$191.9', 'G66' ]}, 
                            { '$eq': ['$191.9', 'G1A' ]}]}] }, 
                'then': {'$concat': [{'$toUpper': {'$substr': [ '$245.b', 0, 1]}}, {'$substr': ['$245.b', 1, { '$add': [{'$indexOfCP': ['$245.b', 'Committee']}, 8 ]}]}, '.'] }, 
                'else': ''}
            }

            #body == A
            add_1['title_case2'] = {
                '$cond': { 
                    'if': {'$eq': ['$191.9', 'G99'] }, 
                    'then': {'$concat': [
                        { '$trim': { 'input': '$245.a',  'chars': ' :' } },
                        '.'] }, 
                    'else': ''}
            }
        else:
            add_1['title_case1'] = empty_string
            add_1['title_case2'] = empty_string
        
        #body == A, E, S
        add_1['title_case3'] = {
            '$cond': { 
                'if': {'$and': [
                    {'$or': [
                        { '$eq': ['$191.9', 'C10' ]}, 
                        { '$eq': ['$191.9', 'G10' ]}, 
                        { '$eq': ['$191.9', 'X10' ]}]}, 
                        {'$gt': [{ '$indexOfCP': ['$191.a', '/Add.' ]}, -1]}] }, 
                'then': {'$concat': ['$245.a', ' ', {'$trim': {'input': '$245.b','chars': '/ '}}, '. '] }, 
                'else': ''}
        }
                
        add_1['title_default'] = {
            '$concat': [ 
                '$245.a', 
                { '$cond': {                 
                    'if': '$245.b', 
                    'then': {'$concat': [' ',{ '$trim': { 'input': '$245.b',  'chars': " " } }]}, 
                    'else': '' } }, 
                {'$cond': {
                    'if': '$245.c',
                    'then': {'$concat': [' ', '$245.c']},
                    'else': ''} }, 
                    '.']
        }

        #body == S
        add_1['unique_case1'] = {
            '$cond': { 
                'if': {'$eq': ['$191.9', 'X99'] }, 
                'then': {'$let': {
                    'vars': {
                        'a': {'$indexOfCP': [ '$239.a', '[']},
                        'b': {'$indexOfCP': [ '$239.a', ']']}},
                        'in': {'$concat': [
                            '[', 
                            { '$toUpper': {'$substrCP': ['$239.a', {'$add': ['$$a', 4]}, 1] }}, 
                            { '$substrCP': ['$239.a', {'$add': ['$$a', 5]}, '$$b' ]}, 
                            '.']}} }, 
                'else': ''}
        }

        #body == A, E, S
        add_1['unique_case2'] = {
            '$cond': { 
                'if': {'$and': [
                    {'$or': [
                        { '$eq': ['$191.9', 'C10' ]}, 
                        { '$eq': ['$191.9', 'G10' ]}, 
                        { '$eq': ['$191.9', 'X10' ]}]}, 
                        {'$gt': [{ '$indexOfCP': ['$191.a', '/Add.' ]}, -1]},
                        {'$ne': ['$239', ""]}
                        ] }, 
                'then': '$239.a', 
                'else': ''}
        }
        
        add_1['unique_default'] = {
            '$cond': {
                'if': '$239.a', 
                'then': {
                    '$concat': [
                        '$239.a', 
                        {'$cond': {
                            'if': '$245.c', 
                            'then': {'$concat': [' / ', '$245.c']}, 
                            'else': ''}}, 
                        '.'
                        ]
                    }, 
                'else': ''
            }
        }

        add_1['summarynote'] = {
            '$cond': {
                'if': '$520.a',
                'then': '$520.a',
                'else': '' } 
        }
        
        add_stage1 = {}
        add_stage1['$addFields'] = add_1

        add_2 = {}

        add_2['publicationdate'] = { 
            '$let': {'vars': {
                'testMonth': {'$arrayElemAt': [{'$split': ['$269.a', '-']}, 1]},
                'testDate': {'$arrayElemAt': [{'$split': ['$269.a', '-']}, 2]},
                'testYear': {'$arrayElemAt': [{'$split': ['$269.a', '-']}, 0]}},
                'in': {
                    '$switch': {
                        'branches': [
                            {'case': {'$eq': ['$$testMonth', '01']},'then': {'$concat': ['$$testDate', ' ', 'Jan.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '02']},'then': {'$concat': ['$$testDate', ' ', 'Feb.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '03']},'then': {'$concat': ['$$testDate', ' ', 'Mar.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '04']},'then': {'$concat': ['$$testDate', ' ', 'Apr.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '05']},'then': {'$concat': ['$$testDate', ' ', 'May', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '06']},'then': {'$concat': ['$$testDate', ' ', 'June', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '07']},'then': {'$concat': ['$$testDate', ' ', 'July', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '08']},'then': {'$concat': ['$$testDate', ' ', 'Aug.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '09']},'then': {'$concat': ['$$testDate', ' ', 'Sept.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '10']},'then': {'$concat': ['$$testDate', ' ', 'Oct.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '11']},'then': {'$concat': ['$$testDate', ' ', 'Nov.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '12']},'then': {'$concat': ['$$testDate', ' ', 'Dec.', ' ', '$$testYear']}}],
                            'default': '$269.a'}
                    } 
                } 
        }
                            
        add_2['votenote'] = { 
            '$cond': {
                'if': '$996.a',
                'then': '$996.a',
                'else': '' } 
        }
        
        add_2['numberingnote'] = { 
            '$cond':{
                'if': '$515.a',
                'then': { 
                    '$cond': { 
                        'if': {'$isArray': '$515.a'}, 
                        'then': {
                            '$concat': [
                                {'$arrayElemAt': ['$515.a', 0]},
                                ' - ',
                                {'$arrayElemAt': ['$515.a', 1]},]}, 
                        'else': '$515.a' } },
                'else': ""
            }
        } 


        add_2['votedate'] = {
            '$let': {
                'vars': {
                    'testMonth': {'$arrayElemAt': [{'$split': ['$992.a', '-']}, 1]},
                    'testDate': {'$arrayElemAt': [{'$split': ['$992.a', '-']}, 2]},
                    'testYear': {'$arrayElemAt': [{'$split': ['$992.a', '-']}, 0]}},
                'in': {
                    '$switch': {
                        'branches': [
                            {'case': {'$eq': ['$$testMonth', '01']},'then': {'$concat': ['$$testDate', ' ', 'Jan.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '02']},'then': {'$concat': ['$$testDate', ' ', 'Feb.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '03']},'then': {'$concat': ['$$testDate', ' ', 'Mar.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '04']},'then': {'$concat': ['$$testDate', ' ', 'Apr.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '05']},'then': {'$concat': ['$$testDate', ' ', 'May', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '06']},'then': {'$concat': ['$$testDate', ' ', 'June', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '07']},'then': {'$concat': ['$$testDate', ' ', 'July', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '08']},'then': {'$concat': ['$$testDate', ' ', 'Aug.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '09']},'then': {'$concat': ['$$testDate', ' ', 'Sept.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '10']},'then': {'$concat': ['$$testDate', ' ', 'Oct.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '11']},'then': {'$concat': ['$$testDate', ' ', 'Nov.', ' ', '$$testYear']}}, 
                            {'case': {'$eq': ['$$testMonth', '12']},'then': {'$concat': ['$$testDate', ' ', 'Dec.', ' ', '$$testYear']}}],
                            'default': '$992.a'}
                } 
            } 
        }

        add_2['recorddesignator'] = {
            '$cond': {
                'if': '$495.a',
                'then': {'$concat': [' (', '$495.a', ') ']},
                'else': '' } 
        }

        #body == E
        add_2['ECOSOCdesignator'] = {
            '$cond': {
                'if': '$599.a',
                'then': {'$concat': [' (', '$599.a', ') ']},
                'else': '' } 
        } 

        add_2['letter'] = {
            '$cond': {
                'if': {'$and': [
                    {'$ne': ['$249', '']}, 
                    {'$gt': [{'$add': [{'$indexOfCP': ['$249.a', 'Letter']}, {'$indexOfCP': ['$249.a', 'Identical letters']}, {'$indexOfCP': ['$249.a', 'Note verbale']}, {'$indexOfCP': ['$249.a', 'Notes verbales']}]}, -4]}]},
                'then': {'$concat': ['$249.a', '.', ' ', '$summarynote']},
                'else': '' }
        } 

        add_2['uniquetitle'] = {
            '$switch': {
                'branches': [
                    {'case': {'$ne': ['$unique_case1', '']},'then': '$unique_case1'}, 
                    {'case': {'$ne': ['$unique_case2', '']},'then': '$unique_case2'}],
                    'default': '$unique_default' }
        }

        add_2['titlestatement'] = {
            '$switch': {
                'branches': [
                    {'case': {'$ne': ['$title_case1', '']},'then': '$title_case1'}, 
                    {'case': {'$ne': ['$title_case2', '']},'then': '$title_case2'}, 
                    {'case': {'$ne': ['$title_case3', '']},'then': '$title_case3'}],
                    'default': '$title_default' }
        } 

        add_2['agendanote'] = {
            '$cond': {
                'if': '$991.e',
                'then': {'$concat': ['$991.e', '.']},
                'else': '' }
        } 

        add_2['docsymbol'] = {
            '$cond': { 
                'if': {'$isArray': '$191' }, 
                'then': {
                    '$let': {  
                        'vars': {
                            'a': {'$arrayElemAt': [ '$191.b', 0]},
                            'b': {'$arrayElemAt': [ '$191.c', 0]},
                            'x': {'$arrayElemAt': [ '$191.b', 1]},
                            'y': {'$arrayElemAt': [ '$191.c', 1]},
                            'first': {'$arrayElemAt': [ '$191.a', 0]},
                            'second': {'$arrayElemAt': [ '$191.a', 1]}  },  
                    'in': {
                        '$cond': {
                            'if': { 
                                '$and': [
                                    {  '$eq': ['$$a', fullbody  ]}, 
                                    {  '$eq': ['$$b', session  ]}, 
                                    '$$second' ]},
                            'then': { 
                                '$concat': [
                                    '$$first', 
                                    ' (', 
                                    '$$second', 
                                    ')' ]},
                            'else': {
                                '$cond': {
                                    'if': {
                                        '$and': [
                                            {'$eq': ['$$x', fullbody]}, 
                                            {'$eq': ['$$y', session]}, 
                                            '$$second']
                                    }, 
                                    'then': {
                                        '$concat': [
                                            '$$second', 
                                            ' (', 
                                            '$$first', ')'
                                        ]
                                    }, 
                                    'else': '$$first'
                                }
                            }
                        }  
                    }
                } 
            }, 
                'else': '$191.a'}}
         
        add_2['agendanum'] = {
            '$cond': {
                'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]},
                'then':'$991.b', 
                'else': {'$substrCP': [ '$991.b', 0, {'$indexOfCP': [ '$991.b', '['] }]}  
            }
        }

        add_2['code'] = {
            '$cond': {
                'if': {'$isArray': '$191'},
                'then': {
                    '$let': {
                        'vars': {
                            'a': {'$arrayElemAt': ['$191.b', 0]},
                            'b': {'$arrayElemAt': ['$191.c', 0]},
                            'first': {'$trim': {'input': {'$arrayElemAt': ['$191.9', 0]},'chars': ' '}},
                            'second': {'$trim': {'input': {'$arrayElemAt': ['$191.9', 1]},'chars': ' '}}},
                        'in': {'$cond': {
                            'if': {'$and': [
                                {'$eq': [{'$arrayElemAt': ['$191.b', 0  ]  }, fullbody]}, 
                                {'$eq': [  {  '$arrayElemAt': [  '$191.c', 0  ]  }, session]}]},
                            'then': '$$first','else': '$$second'}}}},
                'else': {'$trim': {'input': '$191.9','chars': ' '}}} 
        }

        add_stage2 = {}
        add_stage2['$addFields'] = add_2

        transform = {}

        transform['section'] = "itpsubj"

        if body == "S":
            
            transform['head'] = '$991.d'

            transform['subhead'] = {
	            '$switch': {
		            'branches': [
                        {'case': {'$eq': ['$code', 'X00']},'then': 'Reports'}, 
                        {'case': {'$eq': ['$code', 'X01']},'then': 'General documents'}, 
                        {'case': {'$eq': ['$code', 'X02']},'then': 'Documents from previous sessions'}, 
                        {'case': {'$eq': ['$code', 'X03']},'then': 'Decisions of the UN Compensation Commission'}, 
                        {'case': {'$eq': ['$code', 'X10']},'then': 'Draft resolutions'}, 
                        {'case': {'$eq': ['$code', 'X15']},'then': 'Statements by the President of the Security Council'}, 
                        {'case': {'$eq': ['$code', 'X27']},'then': 'Participation by non-Council members (without the right to vote)'}, 
                        {'case': {'$eq': ['$code', 'X30']},'then': 'Discussion in Committee on the Admission of New Members'}, 
                        {'case': {'$eq': ['$code', 'X32']},'then': 'Discussion in Committee Established by Resolution 661 (1990)'}, 
                        {'case': {'$eq': ['$code', 'X33']},'then': 'Discussion in Committee Established by Resolution 421 (1977)'}, 
                        {'case': {'$eq': ['$code', 'X44']},'then': 'Discussion in Committee of Experts'}, 
                        {'case': {'$eq': ['$code', 'X88']},'then': 'Discussion in plenary'}, 
                        {'case': {'$eq': ['$code', 'X99']},'then': 'Resolutions'}],
                        'default': 'Not found'} 
            } 
        
        if body == "A":
            transform['head'] = {
                '$cond': { 
                    'if': {'$eq': ['$agendanum', ""]}, 
                    'then':  '$991.d', 
                    'else': {
                        '$concat': [
                        '$991.d',
                        ' (Agenda item ',
                        '$agendanum',
                        ')']
                    } 
                } 
            }

            transform['subhead'] = {
				'$switch': {
					'branches': [
						{'case': {'$eq': ['$code', 'G0A']},'then': 'Authority for agenda item'}, 
						{'case': {'$eq': ['$code', 'G00']},'then': 'Reports'}, 
						{'case': {'$eq': ['$code', 'G01']},'then': 'General documents'}, 
						{'case': {'$eq': ['$code', 'G02']},'then': 'Documents from previous sessions'}, 
						{'case': {'$eq': ['$code', 'G03']},'then': 'Hearings requested'}, 
						{'case': {'$eq': ['$code', 'G04']},'then': 'Hearings granted'}, 
						{'case': {'$eq': ['$code', 'G05']},'then': 'Petitioners heard'}, 
						{'case': {'$eq': ['$code', 'G06']},'then': 'Statements in general debate (Heads of State/Government)'}, 
						{'case': {'$eq': ['$code', 'G07']},'then': 'Statements in general debate (Countries)'}, 
						{'case': {'$eq': ['$code', 'G08']},'then': 'Statements in general debate (Right of reply)'}, 
						{'case': {'$eq': ['$code', 'G09']},'then': 'Discussion in the Credentials Committee'}, 
						{'case': {'$eq': ['$code', 'G1A']},'then': 'Discussion in the General Committee'}, 
						{'case': {'$eq': ['$code', 'G10']},'then': "Draft resolutions/decisions"}, 
						{'case': {'$eq': ['$code', 'G11']},'then': 'Discussion in the International Security Committee (1st Committee)'}, 
						{'case': {'$eq': ['$code', 'G14']},'then': 'Discussion in the Special Political and Decolonization Committee (4th Committee)'}, 
						{'case': {'$eq': ['$code', 'G17']},'then': 'Discussion in the Special Political Committee'}, 
						{'case': {'$eq': ['$code', 'G22']},'then': 'Discussion in the Economic and Financial Committee (2nd Committee)'}, 
						{'case': {'$eq': ['$code', 'G33']},'then': 'Discussion in the Social, Humanitarian and Cultural Committee (3rd Committee)'}, 
						{'case': {'$eq': ['$code', 'G44']},'then': 'Discussion in the 4th Committee'}, 
						{'case': {'$eq': ['$code', 'G55']},'then': 'Discussion in the Administrative and Budgetary Committee (5th Committee)'}, 
						{'case': {'$eq': ['$code', 'G66']},'then': 'Discussion in the Legal Committee (6th Committee)'}, 
						{'case': {'$eq': ['$code', 'G67']},'then': 'Discussion in the Ad Hoc Committee of the Whole'}, 
						{'case': {'$eq': ['$code', 'G68']},'then': 'Discussion in Committee (Right of reply)'}, 
						{'case': {'$eq': ['$code', 'G88']},'then': 'Discussion in plenary'}, 
						{'case': {'$eq': ['$code', 'G99']},'then': 'Resolutions'}],
                        'default': 'Not found'}
            } 
        
        if body == "E": 
            transform['head'] = {
                '$cond': { 
                    'if': {'$eq': ['$agendanum', ""]}, 
                    'then':  '$991.d', 
                    'else': {
                        '$concat': [
                        '$991.d',
                        ' (Agenda item ',
                        '$agendanum',
                        ')']
                    } 
                } 
            }

            transform['subhead'] = {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$code', 'C0A']},'then': 'Authority for agenda item'}, 
                        {'case': {'$eq': ['$code', 'C00']},'then': 'Reports'}, 
                        {'case': {'$eq': ['$code', 'C01']},'then': 'General documents'}, 
                        {'case': {'$eq': ['$code', 'C02']},'then': 'Documents from previous sessions'}, 
                        {'case': {'$eq': ['$code', 'C10']},'then': 'Draft resolutions/decisions'}, 
                        {'case': {'$eq': ['$code', 'C11']},'then': 'Discussion in Economic Committee'}, 
                        {'case': {'$eq': ['$code', 'C22']},'then': 'Discussion in Social Committee'}, 
                        {'case': {'$eq': ['$code', 'C33']},'then': 'Discussion in Third (Programme and Coordination) Committee'}, 
                        {'case': {'$eq': ['$code', 'C44']},'then': 'Discussion in Committee on Economic, Social and Cultural Rights'}, 
                        {'case': {'$eq': ['$code', 'C88']},'then': 'Discussion in plenary'}, {'case': {'$eq': ['$code', 'C99']},'then': 'Resolutions'}],
                        'default': 'Not found'} 
            } 
            
        transform['entry'] = {
            '$cond': {
                'if': {'$or': [
                        {'$gt': [{'$indexOfCP': ['$docsymbol', '/PV.']}, -1]}, 
                        {'$gt': [{'$indexOfCP': ['$docsymbol', '/SR.']}, -1]}]
                    }, 
                'then': {'$concat': [
                        '(', 
                        '$votedate', 
                        ').'
                        ]}, 
                'else': {'$concat': [
                            '$recorddesignator', 
                            '$ECOSOCdesignator', 
                            {'$switch': {
                                'branches': [
                                    {'case': {'$ne': ['$letter', '']}, 
                                        'then': '$letter'}, 
                                    {'case': {'$ne': ['$uniquetitle', '']}, 
                                        'then': '$uniquetitle'}
                                    ], 
                                    'default': '$titlestatement'
                                }
                            }, 
                            {'$cond': {
                                'if': {'$eq': ['$191.9', 'X27']}, 
                                'then': '$agendanote', 
                                'else': ''
                            }}
                        ]
                }
            }
        }

        transform['note'] = {
            '$switch': {
                'branches': [
                    {'case': {'$and': [{'$or': [{'$eq': ['$191.9', 'C00']}, {'$eq': ['$191.9', 'G00']}, {'$eq': ['$191.9', 'X00']}]}, 
                                {'$eq': ['$letter', '']}]}, 
                        'then': {'$concat': [
                                    'Issued: ', 
                                    '$publicationdate', {
                                        '$cond': {
                                            'if': {'$ne': ['$summarynote', '']}, 
                                            'then': {
                                                '$concat': [
                                                    '. – ', 
                                                    '$summarynote'
                                                ]}, 
                                            'else': '.'
                                        }
                                    }
                                ]
                            }
                        }, 
                    {'case': {'$ne': ['$votenote', '']}, 
                        'then': {'$concat': [
                                '(', 
                                '$votenote', 
                                ', ', 
                                '$votedate', 
                                ')'
                            ]}}, 
                    {'case': {'$ne': ['$numberingnote', '']}, 
                        'then': '$numberingnote'
                        }, 
                    {'case': {'$and': [
                                {'$ne': ['$summarynote','']},
                                {'$eq': ['$letter','']}]},
                        'then': '$summarynote'
                    },
                    {'case': {'$ne': ['$191.9', 'X27']}, 
                        'then': '$agendanote'}
                    ], 
                    'default': ''
                }
            
        } 

        transform_stage = {}
        transform_stage['$addFields'] = transform

        project_stage = {
            '$project': {
                '_id': 0, 
                'record_id': 1, 
                'section': 1, 
                'bodysession': 1, 
                'head': 1, 
                'subhead': 1,
                'docsymbol': 1, 
                'entry': 1, 
                'note': 1, 
                'sortkey1': '$head',
                'sortkey2': '$code',
                'sortkey3': '$docsymbol'
            }
        }
            
        sort_stage = {
            '$sort': {
                'sortkey1': 1, 
                'sortkey2': 1, 
                'sortkey3': 1
            }
        }

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage)
        pipeline.append(unwind_stage)
        pipeline.append(match_stage2)
        pipeline.append(add_stage1)
        pipeline.append(add_stage2)
        pipeline.append(transform_stage)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)
        pipeline.append(merge_stage)

       #print(pipeline)
        
        inputCollection.aggregate(pipeline, collation=collation)

        group_itpsubj("itpsubj", bodysession)
 
        return "itpsubj completed successfully"
               
    except Exception as e:
        return e

# Agenda #
def itpage(bodysession):
    """
    Agenda

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 
        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]

        match_stage = {}
        unwind_stage = {}
        
        transform = {}
        transform['_id'] = 0
        transform['record_id'] = 1
        transform['section'] = "itpage"
        transform['bodysession'] = 1


        transform_stage = {}
        transform_stage['$project'] = transform

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage)
        pipeline.append(unwind_stage)
        pipeline.append(transform_stage)
        pipeline.append(merge_stage)

        inputCollection.aggregate(pipeline)

        return list(outputCollection.find({"bodysession": bodysession, "section": 'itpsubj'}))

    except Exception as e:    
        return e

# List of Documents #
def itpdsl(bodysession):
    """
    List of Documents

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 
        pipeline = []

        bs = bodysession.split("/")
        session = bs[1]

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        match_stage = {
            '$match': {
                'record_type': 'BIB', 
                'bodysession': bodysession
            }
        }

        add_1 = {}

        add_1['actualsession'] = {
            '$let': {
                'vars': {
                    'sesh': {
                        '$cond': {
                            'if': {'$isArray': '$191'}, 
                            'then': {'$split': [{'$arrayElemAt': ['$191.c', 0]}, '/']}, 
                            'else': {'$split': ['$191.c', '/']}
                        }
                    }
                }, 
                'in': {
                    '$cond': {
                        'if': {'$in': [session, '$$sesh']}, 
                        'then': 'current', 
                        'else': 'other'
                    }
                }
            }
        }
        
        add_1['section'] = "itpdsl"

        add_stage1 = {}

        add_stage1['$addFields'] = add_1

        add_2 = {}

        add_2['docsymbol'] = {
			'$concat': [
				{
					'$cond': {
						'if': {'$isArray': '$191'}, 
						'then': {
							'$concat': [
								{'$arrayElemAt': ['$191.a', 0]}, 
								' (', 
								{'$arrayElemAt': ['$191.a', 1]}, 
								')'
							]
						}, 
						'else': '$191.a'
					}
				}, {
					'$cond': {
						'if': {'$eq': ['$495', '']}, 
						'then': '', 
						'else': {'$concat': [' (', '$495.a', ')']}
					}
				}
			]
		}

        add_2['committee'] = {
			'$switch': {
				'branches': [
					{'case': {'$eq': ['$actualsession', 'other']}, 
						'then': 'OTHER DOCUMENTS CONSIDERED BY THE MAIN COMMITTEES'}, 
					{'case': {'$eq': ['$793.a', '01']}, 
						'then': 'DISARMAMENT AND INTERNATIONAL SECURITY COMMITTEE (FIRST COMMITTEE)'}, 
					{'case': {'$eq': ['$793.a', '02']}, 
						'then': 'ECONOMIC AND FINANCIAL COMMITTEE (SECOND COMMITTEE)'}, 
					{'case': {'$eq': ['$793.a', '03']}, 
						'then': 'SOCIAL, HUMANITARIAN AND CULTURAL COMMITTEE (THIRD COMMITTEE)'}, 
					{'case': {'$eq': ['$793.a', '04']}, 
						'then': 'SPECIAL POLITICAL AND DECOLONIZATION COMMITTEE (FOURTH COMMITTEE)'}, 
					{'case': {'$eq': ['$793.a', '05']}, 
						'then': 'ADMINISTRATIVE AND BUDGETARY COMMITTEE (FIFTH COMMITTEE)'}, 
					{'case': {'$eq': ['$793.a', '06']}, 
						'then': 'LEGAL COMMITTEE (SIXTH COMMITTEE)'}, 
					{'case': {'$eq': ['$793.a', 'PL']}, 
						'then': 'PLENARY'}, 
					{'case': {'$eq': ['$793.a', 'GL']}, 
						'then': 'GENERAL COMMITTEE'}
				], 
				'default': 'PLENARY'
			}
		}

        add_2['series'] = {
			'$let': {
				'vars': {
					'a': {
						'$cond': {
							'if': {'$isArray': '$191'}, 
							'then': {'$arrayElemAt': ['$191.a', 0]}, 
							'else': '$191.a'
						}
					}
				}, 
				'in': {
					'$switch': {
						'branches': [
							{'case': {'$gt': [{'$indexOfCP': ['$$a', '/L.']}, -1]}, 
								'then': 'Limited series'}, 
							{'case': {'$gt': [{'$indexOfCP': ['$$a', '/INF/']}, -1]}, 
								'then': 'Information series'}, 
							{'case': {'$gt': [{'$indexOfCP': ['$$a', '/PV.']}, -1]}, 
								'then': 'Verbatim records'}, 
							{'case': {'$gt': [{'$indexOfCP': ['$$a', '/RES/']}, -1]}, 
								'then': 'Resolutions'}, 
							{'case': {'$gt': [{'$indexOfCP': ['$$a', '/SR.']}, -1]}, 
								'then': 'Summary records'}, 
							{'case': {'$gt': [{'$indexOfCP': ['$$a', '/PRST/']}, -1]}, 
								'then': 'Statements of the President of the Security Council'}, 
							{'case': {'$gt': [{'$indexOfCP': ['$$a', '/Agenda/']}, -1]}, 
								'then': 'Agenda Series'}, 
							{'case': {'$gt': [{'$indexOfCP': ['$$a', '/NGO/']}, -1]}, 
								'then': 'Non-governmental organizations series'}
						], 
						'default': 'General series'
					}
				}
			}
		}

        add_stage2 = {}
        add_stage2['$addFields'] = add_2

        project_stage = {
            '$project': {
                '_id': 0, 
                'bodysession': 1, 
                'section': 1, 
                'record_id': 1, 
                'committee': 1, 
                'series': 1, 
                'docsymbol': 1, 
                'sortkey1': {
                    '$let': {
                        'vars': {
                            'x': {'$substr': ['$committee', 0, 2]}
                        }, 
                        'in': {
                            '$switch': {
                                'branches': [
                                    {'case': {'$eq': ['$$x', 'PL']}, 
                                        'then': '01'}, 
                                    {'case': {'$eq': ['$$x', 'GE']}, 
                                        'then': '02'}, 
                                    {'case': {'$eq': ['$$x', 'DI']}, 
                                        'then': '03'}, 
                                    {'case': {'$eq': ['$$x', 'SP']}, 
                                        'then': '04'}, 
                                    {'case': {'$eq': ['$$x', 'EC']}, 
                                        'then': '05'}, 
                                    {'case': {'$eq': ['$$x', 'SO']}, 
                                        'then': '06'}, 
                                    {'case': {'$eq': ['$$x', 'AD']}, 
                                        'then': '07'}, 
                                    {'case': {'$eq': ['$$x', 'LE']}, 
                                        'then': '08'}, 
                                    {'case': {'$eq': ['$$x', 'OT']}, 
                                        'then': '09'}
                                ], 
                                'default': '99'
                            }
                        }
                    }
                }, 
                'sortkey2': '$series', 
                'sortkey3': '$docsymbol'
            }
        }

        sort_stage = {
            '$sort': {
                'sortkey1': 1, 
                'sortkey2': 1, 
                'sortkey3': 1
            }
        }

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage)
        pipeline.append(add_stage1)
        pipeline.append(add_stage2)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)
        pipeline.append(merge_stage)

        inputCollection.aggregate(pipeline, collation=collation)

        copyPipeline = []

        copyMatch_stage = {
            '$match': {
                'bodysession': bodysession, 
                'section': "itpdsl"
            }
        }

        copyMerge_stage = {
            '$merge': { 'into': wordOutput}
        }
        
        clear_section("itpdsl", bodysession)

        copyPipeline.append(copyMatch_stage)
        copyPipeline.append(copyMerge_stage)

        outputCollection.aggregate(copyPipeline)

    except Exception as e:
        return e

# Check List of Meetings #
def itpmeet(bodysession):
    """
    Check List of Meetings

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 
        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]

        match_stage = {}
        unwind_stage = {}
        
        transform = {}
        transform['_id'] = 0
        transform['record_id'] = 1
        transform['section'] = "itpmeet"
        transform['bodysession'] = 1

        transform_stage = {}
        transform_stage['$project'] = transform

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage)
        pipeline.append(unwind_stage)
        pipeline.append(transform_stage)
        pipeline.append(merge_stage)

        inputCollection.aggregate(pipeline)

    except Exception as e:
        return e

# Reports of the main and procedural committees #
def itpreps(bodysession):
    """
    Reports of the main and procedural committees

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 
        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]

        match_stage = {}
        unwind_stage = {}
        
        transform = {}
        transform['_id'] = 0
        transform['record_id'] = 1
        transform['section'] = "itpreps"
        transform['bodysession'] = 1

        transform_stage = {}
        transform_stage['$project'] = transform

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage)
        pipeline.append(unwind_stage)
        pipeline.append(transform_stage)
        pipeline.append(merge_stage)

        inputCollection.aggregate(pipeline)

    except Exception as e:
        return e

# Vote Chart #
def itpvot(bodysession): 
    """
    Vote Chart

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 
        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]

        match_stage = {}
        unwind_stage = {}
        
        transform = {}
        transform['_id'] = 0
        transform['record_id'] = 1
        transform['section'] = "itpvot"
        transform['bodysession'] = 1

        transform_stage = {}
        transform_stage['$project'] = transform

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage)
        pipeline.append(unwind_stage)
        pipeline.append(transform_stage)
        pipeline.append(merge_stage)

        inputCollection.aggregate(pipeline)

    except Exception as e:
        return e

# Suppliments to Official Records #
def itpsor(bodysession): 
    """
    Suppliments to Official Records

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try:
        print("I made it in")
        return list(inputCollection.find({"bodysession": bodysession}, {"record_id": 1, "_id": 0}))

    except Exception as e:
        return e

#### END Data transformations for each section ####

## Main function / switch ##
def process_section(bodysession, section):
    """
    Executes sections based on input.

    """ 
    

    if section == "itpsubj" : 
        s = itpsubj(bodysession) #subject index 
    elif section == "itpitsp" : 
        s = itpitsp(bodysession) #speaker
    elif section == "itpitsc" : 
        s = itpitsc(bodysession) #country
    elif section == "itpitss" : 
        s = itpitss(bodysession) #subject speaker
    elif section == "itpage" : 
        s = itpage(bodysession) #agenda
    elif section == "itpdsl" : 
        s = itpdsl(bodysession) #doc symbol list
    elif section == "itpmeet" : 
        s = itpmeet(bodysession) #meeting
    elif section == "itpres" : 
        s = itpres(bodysession) #list of resolutions
    elif section == "itpvot" : 
        s = itpvot(bodysession) #vote
    elif section == "itpsor" : 
        s = itpsor(bodysession) #suppliments to official records
    elif section == "itpreps": 
        s = itpreps(bodysession) #reports
    else: 
        s = "No Section Selected"

    return s

## END main function / switch #



def group_speeches(section, bodysession):

    clear_section(section, bodysession)

    pipeline = []

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            'section': section
        }
    }
    
    sort_stage1 = {
        '$sort': {
            'sortkey1': 1, 
            'sortkey2': 1, 
            'sortkey3': 1
        }
    }
    
    group_stage1 = {
        '$group': {
            '_id': {
                'itshead': '$itshead', 
                'itsubhead': '$itssubhead', 
                'itsentry': '$itsentry', 
                'sortkey1': '$sortkey1', 
                'sortkey2': '$sortkey2'
            }, 
            'docsymbols': {
                '$push': '$docsymbol'
            }
        }
    }
        
    sort_stage2 = {
        '$sort': {
            '_id.sortkey1': 1, 
            '_id.sortkey2': 1
        }
    }

    group_stage2 = {
        '$group': {
            '_id': {
                'itshead': '$_id.itshead', 
                'itsubhead': '$_id.itsubhead', 
                'sortkey1': '$_id.sortkey1'
            }, 
            'itsentries': {
                '$push': {
                    'itsentry': '$_id.itsentry', 
                    'docsymbols': '$docsymbols'
                }
            }
        }
    }
    
    sort_stage3 = {
        '$sort': {
            '_id.sortkey1': 1
        }
    }

    group_stage3 = {
        '$group': {
            '_id': {
                'itshead': '$_id.itshead',
                'sort': {'$toUpper': '$_id.itshead'}
            }, 
            'subheading': {
                '$push': {
                    'itssubhead': '$_id.itsubhead', 
                    'itsentries': '$itsentries'
                }
            }
        }
    }
    
    sort_stage4 = {
        '$sort': {
            '_id.sort': 1
        }
    }

    project_stage = {
        '$project': {
            '_id': 0,
            'itshead': '$_id.itshead',
            'bodysession': bodysession, 
            'section': section, 
            'subheading': 1,
            'sort': '$_id.sort'
        }
    }

    merge_stage = {
        '$merge': { 'into': wordOutput}
    }

    pipeline.append(match_stage)
    pipeline.append(sort_stage1)
    pipeline.append(group_stage1)
    pipeline.append(sort_stage2)
    pipeline.append(group_stage2)
    pipeline.append(sort_stage3)
    pipeline.append(group_stage3)
    pipeline.append(sort_stage4)
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    #print(pipeline)

    outputCollection.aggregate(pipeline, collation={
            'locale': 'en', 
            'numericOrdering': True,
            'strength': 1,
            'alternate': 'shifted'
        })


def group_itpsubj(section, bodysession):

    clear_section(section, bodysession)

    pipeline = []

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            'section': section
        }
    }

    sort_stage1 = {
        '$sort': {
            'sortkey1': 1, 
            'sortkey2': 1, 
            'sortkey3': 1
        }
    }

    group_stage1 = {
        '$group': {
            '_id': {
                'itp_head': '$head', 
                'itp_subhead': '$subhead', 
                'sortkey1': '$sortkey1', 
                'sortkey2': '$sortkey2'
            }, 
            'entries': {
                '$push': {
                    'docsymbol': '$docsymbol', 
                    'entry': '$entry', 
                    'note': '$note'
                }
            }
        }
    }
    
    sort_stage2 = {
        '$sort': {
            '_id.sortkey1': 1, 
            '_id.sortkey2': 1
        }
    }

    group_stage2 = {
        '$group': {
            '_id': {
                'itp_head': '$_id.itp_head'
            }, 
            'subheading': {
                '$push': {
                    'subhead': '$_id.itp_subhead', 
                    'entries': '$entries'
                }
            }
        }
    }  
 
    sort_stage3 = {
        '$sort': {
            '_id': 1
        }
    }

    project_stage = {
        '$project': {
            '_id': 0,
            'head': '$_id.itp_head',
            'bodysession': bodysession, 
            'section': section, 
            'subheading': 1
        }
    }

    merge_stage = {
        '$merge': { 'into': wordOutput}
    }

    pipeline.append(match_stage)
    pipeline.append(sort_stage1)
    pipeline.append(group_stage1)
    pipeline.append(sort_stage2)
    pipeline.append(group_stage2)
    #pipeline.append(group_stage3)
    pipeline.append(sort_stage3)
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    #print(pipeline)

    outputCollection.aggregate(pipeline, collation={
            'locale': 'en', 
            'numericOrdering': True,
            'strength': 1
        })



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

def lookup_code(lookup_field):
    """
    Returns code from lookup table
    """
    return lookupCollection.find({'lookup_field': lookup_field, 'implemented': "Y"}, {'_id': 0, 'code': 1})

def lookup_snapshots():
    """
    Returns list of available snapshots
    """
    return inputCollection.find({}, {'bodysession': 1}).distinct('bodysession')

def section_summary():
    pipeline = []

    group_stage = {
        '$group': {
            '_id': {
                'b': '$bodysession', 
                's': '$section'
            }, 
            'count': {
                '$sum': 1
            },
            'time': {'$max':{'$toDate': "$_id"}}
        }
    }
    sort_stage = {
        '$sort': {
            'time': -1
        }
    } 
    project_stage = {
        '$project': {
            '_id': 0, 
            'bodysession': '$_id.b', 
            'section': '$_id.s', 
            'count': 1,
            'ts': {
                '$dateToString': {
                    'format': '%Y-%m-%d %H:%M', 
                    'date': '$time', 
                    'timezone': 'America/New_York'
                }
            }
        }
    }

    pipeline.append(group_stage)
    pipeline.append(sort_stage)
    pipeline.append(project_stage)   

    return list(outputCollection.aggregate(pipeline))
