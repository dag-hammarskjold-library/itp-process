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
        
        add_1['agendanum'] = {
            '$cond': {
                'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]}, 
                'then': '$991.b', 
                'else': {'$substrCP': ['$991.b', 0, {'$indexOfCP': ['$991.b', '[']}]}
            }
        }

        add_1['agendasubject'] = {
            '$trim': {
                'input': {
                    '$replaceAll': {
                        'input': '$991.d', 
                        'find': '--', 
                        'replacement': '—'
                    }
                }, 
                'chars': ' '
            }
        }

        add_stage1 = {}
        add_stage1['$addFields'] = add_1

        add_2 = {}
        add_2['section'] = "itpitsc" 
        add_2['itshead'] = {
            '$cond': {
                'if': {'$ne': ['$710', '']}, 
                'then': { 
                    '$cond': { 
                        'if': {'$isArray': '$710' }, 
                        'then': {'$arrayElemAt': [ '$710.a', 0]},
                        'else': {'$trim': { 'input': '$710.a',  'chars': ' ' }}}}, 
                'else': {'$trim': { 'input': '$711.a',  'chars': ' ' }}
            }
        }
        
        if body == "S":
            add_2['itssubhead'] = '$agendasubject' #'$991.d'
        else:
            add_2['itssubhead'] = {
                '$cond': { 
                    'if': {'$eq': ['$agendanum', ""]}, 
                    'then':  '$agendasubject', #'$991.d', 
                    'else': {
                        '$concat': [
                        '$agendasubject', #'$991.d',
                        ' (Agenda item ',
                        '$agendanum',
                        ')']
                    } 
                } 
            }

        add_2['itsentry'] = {
            '$cond': {
                'if': '$700.g', 
                'then': {'$concat': [{'$trim': { 'input': '$700.a',  'chars': ' ' }}, ' ', {'$trim': { 'input': '$700.g',  'chars': ' ' }}]}, 
                'else': {'$trim': { 'input': '$700.a',  'chars': ' ' }}
            }
        }

        add_2['docsymbol'] = '$791.a'

        add_stage2 = {}
        add_stage2['$addFields'] = add_2


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
                        {
                            '$replaceAll': {
                                'input': {
                                    '$replaceAll': {
                                        'input': {'$toUpper': '$itshead'}, #corporate
                                        'find': '. ', 
                                        'replacement': ' .'
                                    }
                                }, 
                                'find': '—', 
                                'replacement': ' —'
                            }
                        },
                        '+',
                        {
                            '$replaceAll': {
                                'input': {
                                    '$replaceAll': {
                                        'input': {'$toUpper':'$itssubhead'}, #subject
                                        'find': '. ', 
                                        'replacement': ' .'
                                    }
                                }, 
                                'find': '—', 
                                'replacement': ' —'
                            }
                        },
                ]},
                'sortkey2': {
                    '$replaceAll': {
                        'input': {
                            '$replaceAll': {
                                'input': {
                                    '$replaceAll': {
                                        'input': {'$toUpper': '$itsentry'}, #speaker
                                        'find': ' ', 
                                        'replacement': '!'
                                    }
                                }, 
                                'find': ',', 
                                'replacement': ' '
                            }
                        }, 
                    'find': '-', 
                    'replacement': '^'
                    }
                },
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
        pipeline.append(add_stage1)
        pipeline.append(add_stage2)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)
    
        pipeline.append(merge_stage)

        #print(pipeline)
    
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
        
        add_1['agendanum'] = {
            '$cond': {
                'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]}, 
                'then': '$991.b', 
                'else': {'$substrCP': ['$991.b', 0, {'$indexOfCP': ['$991.b', '[']}]}
            }
        }

        add_1['agendasubject'] = {
            '$trim': {
                'input': {
                    '$replaceAll': {
                        'input': '$991.d', 
                        'find': '--', 
                        'replacement': '—'
                    }
                }, 
                'chars': ' '
            }
        }

        add_stage1 = {}
        add_stage1['$addFields'] = add_1

        add_2 = {}
        add_2['section'] = "itpitsp"

        add_2['itshead'] = { 
                '$concat': [        
                {'$cond': {        
                    'if': '$700.g',        
                    'then': {'$concat': [{'$trim': { 'input': '$700.a',  'chars': ' ' }}, ' ', {'$trim': { 'input': '$700.g',  'chars': ' ' }} ]}, 
                    'else': {'$trim': { 'input': '$700.a',  'chars': ' ' }}}},          
                ' (',         
                {'$cond': {
                    'if': {'$ne': ['$710', '']}, 
                    'then': { 
                        '$cond': { 
                            'if': {'$isArray': '$710' }, 
                            'then': {'$arrayElemAt': [ '$710.a', 0]},
                            'else': {'$trim': { 'input': '$710.a',  'chars': ' ' }}}}, 
                    'else': {'$trim': { 'input': '$711.a',  'chars': ' ' }}
                }},         
                ')' ]}
        
        if body == "S":
            add_2['itssubhead'] = '$agendasubject' #'$991.d'
        else:
            add_2['itssubhead'] = {
                '$cond': { 
                    'if': {'$eq': ['$agendanum', ""]}, 
                    'then':  '$agendasubject', #'$991.d', 
                    'else': {
                        '$concat': [
                        '$agendasubject', #'$991.d',
                        ' (Agenda item ',
                        '$agendanum',
                        ')']
                    } 
                } 
            }


        add_2['docsymbol'] = '$791.a'

        add_stage2 = {}
        add_stage2['$addFields'] = add_2

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
                '$replaceAll': {
                    'input': {
                        '$replaceAll': {
                            'input': {
                                '$replaceAll': {
                                    'input': {'$concat': [{'$toUpper': '$itshead'}, '+']}, 
                                    'find': ' ', 
                                    'replacement': '!'
                                }
                            }, 
                            'find': ',', 
                            'replacement': ' '
                        }
                    }, 
                    'find': '-', 
                    'replacement': '^'
                    }
                },
                'sortkey2': {
                    '$replaceAll': {
                        'input': {
                            '$replaceAll': {
                                'input': {'$toUpper': '$itssubhead'}, #subject 
                                'find': '. ', 
                                'replacement': ' .'
                            }
                        }, 
                        'find': '—', 
                        'replacement': ' —'
                    }
                }, 
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
        pipeline.append(add_stage1)
        pipeline.append(add_stage2)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)
    
        pipeline.append(merge_stage)
    
        #print(pipeline)

        inputCollection.aggregate(pipeline, collation=collation)

        group_itpitsp("itpitsp", bodysession)

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
        
        add_1['agendanum'] = {
            '$cond': {
                'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]}, 
                'then': '$991.b', 
                'else': {'$substrCP': ['$991.b', 0, {'$indexOfCP': ['$991.b', '[']}]}
            }
        }

        add_1['agendasubject'] = {
            '$trim': {
                'input': {
                    '$replaceAll': {
                        'input': '$991.d', 
                        'find': '--', 
                        'replacement': '—'
                    }
                }, 
                'chars': ' '
            }
        }

        add_stage1 = {}
        add_stage1['$addFields'] = add_1

        add_2 = {}
        add_2['section'] = "itpitss"
        
        if body == "S":
            add_2['itshead'] = '$agendasubject' #'$991.d'
        else:
            add_2['itshead'] = {
                '$cond': { 
                    'if': {'$eq': ['$agendanum', ""]}, 
                    'then':  '$agendasubject', #'$991.d', 
                    'else': {
                        '$concat': [
                        '$agendasubject', #'$991.d',
                        ' (Agenda item ',
                        '$agendanum',
                        ')']
                    } 
                } 
            }

        add_2['itssubhead'] =  {
            '$cond': {
                'if': {'$ne': ['$710', '']}, 
                'then': { 
                    '$cond': { 
                        'if': {'$isArray': '$710' }, 
                        'then': {'$arrayElemAt': [ '$710.a', 0]},
                        'else': {'$trim': { 'input': '$710.a',  'chars': ' ' }}}}, 
                'else': {'$trim': { 'input': '$711.a',  'chars': ' ' }}
            }
        }
        
        add_2['itsentry'] = {
            '$cond': {
                'if': '$700.g', 
                'then': {'$concat': [{'$trim': { 'input': '$700.a',  'chars': ' ' }}, ' ', {'$trim': { 'input': '$700.g',  'chars': ' ' }}]}, 
                'else': {'$trim': { 'input': '$700.a',  'chars': ' ' }}
            }
        }

        add_2['docsymbol'] = '$791.a'

        add_stage2 = {}
        add_stage2['$addFields'] = add_2

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
                        {'$replaceAll': {
                            'input': {
                                '$replaceAll': {
                                    'input': {'$toUpper': '$agendasubject'}, #subject
                                    'find': '. ', 
                                    'replacement': ' .'
                                }
                            }, 
                            'find': '—', 
                            'replacement': ' —'} # $
                        },
                        '+',
                        {'$replaceAll': {
                            'input': {
                                '$replaceAll': {
                                    'input': {'$toUpper':'$itssubhead'}, #corporate
                                    'find': '. ', 
                                    'replacement': ' .'
                                }
                            }, 
                            'find': '—', 
                            'replacement': ' —'} # $
                        },
                    ]
                },
                'sortkey2': {
                    '$replaceAll': {
                        'input': {
                            '$replaceAll': {
                                'input': {
                                    '$replaceAll': {
                                        'input': {'$toUpper': '$itsentry'},  #speaker
                                        'find': ' ', 
                                        'replacement': '!'
                                    }
                                }, 
                                'find': ',', 
                                'replacement': ' '
                            }
                        }, 
                        'find': '-', 
                        'replacement': '^'
                        }
                },
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
        pipeline.append(add_stage1)
        pipeline.append(add_stage2)
        pipeline.append(project_stage)
        pipeline.append(sort_stage)
    
        pipeline.append(merge_stage)

        #print(pipeline)

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
        #unwind_stage2 = {'$unwind': '$991'}

        match_stage2 = {
            '$match': {
                '191.b': body + "/",
                '191.c': session, 
                '991.z': "I"
            }
        }

        add_1 = {}

        add_1['decision'] = '$996.a'

        add_1['votedate'] = {'$split': ['$992.a', '-']}

        add_1['agendas'] = {
            '$cond': {
                'if': {'$isArray': ['$991']}, 
                'then': {
                    '$filter': {
                        'input': '$991', 
                        'as': 'fields', 
                        'cond': {'$eq': ['$$fields.z', 'I']}
                    }
                }, 
                'else': {
                    '$cond': {
                        'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]}, 
                        'then': '$991.b', 
                        'else': {'$substrCP': ['$991.b', 0, {'$indexOfCP': ['$991.b', '[']}]}}}
            }
        }

        add_1['subjects'] = {
            '$cond': {
                'if': {'$isArray': ['$991']}, 
                'then': {
                    '$filter': {
                        'input': '$991', 
                        'as': 'fields', 
                        'cond': {
                            '$eq': [
                                '$$fields.z', 'I'
                            ]
                        }
                    }
                }, 
                'else': '$991.d'
            }
        }


        add_stage1 = {}
        add_stage1['$addFields'] = add_1

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
                    'str_len': {'$strLenCP': '$decision'},  
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
                    'default': {
                        '$cond': {
                            'if': {'$gt': ['$$b', -1]}, 
                            'then': {'$substrCP': ['$decision', {'$add': ['$$a', 1]}, {'$subtract': [{'$subtract': ['$$b', '$$a']}, 1]}]}, 
                            'else': {'$substrCP': ['$decision', {'$add': ['$$a', 1]}, {'$subtract': [{'$subtract': ['$$str_len', '$$a']}, 1]}]}
                            }
                        }
                    }
                }
            }
        }
                

        if body == "S":
            transform['ainumber'] = ''

            transform['subject'] = {
                '$cond': {
                    'if': {'$isArray': '$subjects'}, 
                    'then': {'$arrayElemAt': ['$subjects.d', 0]}, 
                    'else': '$subjects'
                }
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
                '$cond': {
                    'if': {'$gt': [{'$indexOfCP': ['$decision', 'meeting']}, -1]}, 
                    'then': {
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
                    }, 
                    'else': ''
                }
            }

            transform['voteyear'] = {'$arrayElemAt': ['$votedate', 0]}
                    
        else:
            transform['ainumber'] = {
                '$switch': {
                    'branches': [
                        {'case': {'$and': [{'$isArray': ['$agendas']}, {'$gt': [{'$size': '$agendas'}, 1]}]},
                            'then': {
                                '$let': {
                                    'vars': {
                                        'element1': {'$cond': {'if': {'$eq': [{'$indexOfCP': [{ '$arrayElemAt': [ '$agendas.b', 0 ]}, '[']}, -1]},'then': {'$arrayElemAt': ['$agendas.b', 0]},'else': {'$substrCP': [{'$arrayElemAt': ['$agendas.b', 0]}, 0, {'$indexOfCP': [{ '$arrayElemAt': [ '$agendas.b', 0 ]}, '[']}]}}},
                                        'element2': {'$cond': {'if': {'$eq': [{'$indexOfCP': [{ '$arrayElemAt': [ '$agendas.b', 1 ]}, '[']}, -1]},'then': {'$arrayElemAt': ['$agendas.b', 1]},'else': {'$substrCP': [{'$arrayElemAt': ['$agendas.b', 1]}, 0, {'$indexOfCP': [{ '$arrayElemAt': [ '$agendas.b', 1 ]}, '[']}]}}}},
                                    'in': {
                                        '$cond': {
                                            'if': {'$eq': ['$$element1', '$$element2']},
                                            'then': '$$element1',
                                            'else': {'$concat': ['$$element1', ' ', '$$element2']}}}}
                            }
                        }, 
                        {'case': {'$and': [{'$isArray': ['$agendas']}, {'$eq': [{'$size': '$agendas'}, 1]}]},
                            'then': {
                                '$cond': {
                                    'if': {'$eq': [{'$indexOfCP': [{'$arrayElemAt': ['$agendas.b', 0]}, '[']}, -1]},
                                    'then': {'$arrayElemAt': ['$agendas.b', 0]},
                                    'else': {'$substrCP': [{'$arrayElemAt': ['$agendas.b', 0]}, 0, {'$indexOfCP': [{'$arrayElemAt': ['$agendas.b', 0]}, '[']}]}
                                }
                            }
                        }
                    ],
                    'default': '$agendas'
                } 
            }
               

            transform['title'] = { 
                '$cond': { 
                    'if': '$245.a', 
                    'then': {
                        '$cond': {
                            'if': {'$eq': [{'$indexOfCP': ['$245.a', ' :']}, -1]},
                            'then': '$245.a',
                            'else': { '$rtrim': { 'input': '$245.a',  'chars': " :" } }}}, 
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
    
        if body == "A":
            transform['meeting'] = {
                '$cond': {
                    'if': {'$gt': [{'$indexOfCP': ['$decision', 'plenary']}, -1]}, 
                    'then': {
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
                    }, 
                    'else': ''
                }
            }    

        if body == "E":
            transform['meeting'] = {
                '$cond': {
                    'if': {'$gt': [{'$indexOfCP': ['$decision', 'plenary']}, -1]}, 
                    'then': {
                        '$concat': [
                            '$191.b', 
                            {'$substrCP': ['$191.c', 0, 4]}, 
                            '/SR.', 
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
                    }, 
                    'else': ''
                }
            }    

        transform['sortkey1'] = '$191.a'

        transform_stage = {}
        transform_stage['$project'] = transform
                        
        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage1)
        pipeline.append(unwind_stage1)
        #pipeline.append(unwind_stage2)
        pipeline.append(match_stage2)
        pipeline.append(add_stage1)
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
        itpcode = 'ITP' + body + session

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
                    '$or': [
                        {'$and': [
                            {'991.z': 'I'},
                            {'991.a': {'$regex': '^S'}},
                            {'930.a': {'$ne': itpcode}},
                            {'991.m': {'$ne': fullbody}},
                            {'991.s': {'$ne': session}}]}, 
                        {'$and': [
                            {'991.z': 'I'}, 
                            {'991.a': {'$regex': '^S'}}, 
                            {'930.a': itpcode}, 
                            {'991.m': fullbody}, 
                            {'991.s': session}]}
                    ]
                }
            }

        if body == "A":
            match_stage2 = {
                '$match': {
                    '$or': [
                        {'$and': [
                            {'991.z': 'I'},
                            {'991.a': {'$regex': '^A'}},
                            {'930.a': {'$ne': itpcode}},
                            {'991.m': {'$ne': fullbody}},
                            {'991.s': {'$ne': session}}]}, 
                        {'$and': [
                            {'991.z': 'I'}, 
                            {'991.a': {'$regex': '^A'}}, 
                            {'930.a': itpcode}, 
                            {'991.m': fullbody}, 
                            {'991.s': session}]}
                    ]
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
                {'$cond': {
                    'if': {'$and': [{'$isArray': '$245.n'}, {'$isArray': '$245.p'}]}, 
                    'then': {
                        '$concat': [
                            {'$cond': {'if': {'$arrayElemAt': ['$245.n', 0]},'then': {'$concat': [' ', {'$trim': {'input': {'$arrayElemAt': ['$245.n', 0]},'chars': ' '}}]},'else': ''}}, 
                            {'$cond': {'if': {'$arrayElemAt': ['$245.p', 0]},'then': {'$concat': [' ', {'$trim': {'input': {'$arrayElemAt': ['$245.p', 0]},'chars': ' '}}]},'else': ''}}, 
                            {'$cond': {'if': {'$arrayElemAt': ['$245.n', 1]},'then': {'$concat': [' ', {'$trim': {'input': {'$arrayElemAt': ['$245.n', 1]},'chars': ' '}}]},'else': ''}}, 
                            {'$cond': {'if': {'$arrayElemAt': ['$245.p', 1]},'then': {'$concat': [' ', {'$trim': {'input': {'$arrayElemAt': ['$245.p', 1]},'chars': ' '}}]},'else': ''}}, 
                            {'$cond': {'if': {'$arrayElemAt': ['$245.n', 2]},'then': {'$concat': [' ', {'$trim': {'input': {'$arrayElemAt': ['$245.n', 2]},'chars': ' '}}]},'else': ''}}, 
                            {'$cond': {'if': {'$arrayElemAt': ['$245.p', 2]},'then': {'$concat': [' ', {'$trim': {'input': {'$arrayElemAt': ['$245.p', 2]},'chars': ' '}}]},'else': ''}}, 
                            {'$cond': {'if': {'$arrayElemAt': ['$245.n', 3]},'then': {'$concat': [' ', {'$trim': {'input': {'$arrayElemAt': ['$245.n', 3]},'chars': ' '}}]},'else': ''}}, 
                            {'$cond': {'if': {'$arrayElemAt': ['$245.p', 3]},'then': {'$concat': [' ', {'$trim': {'input': {'$arrayElemAt': ['$245.p', 3]},'chars': ' '}}]},'else': ''}}] 
                        }, 
                    'else': {
                        '$concat': [
                            {
                                '$cond': {
                                    'if': '$245.n', 
                                    'then': {'$concat': [' ', {'$trim': {'input': '$245.n', 'chars': ' '}}]}, 
                                    'else': ''
                                }
                            }, 
                            {
                                '$cond': {
                                    'if': '$245.p', 
                                    'then': {'$concat': [' ', {'$trim': {'input': '$245.p', 'chars': ' '}}]}, 
                                    'else': ''
                                }
                            }
                        ]
                    }
                }
            },
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
        
        add_1['agendasubject'] = {
            '$trim': {
                'input': {
                    '$replaceAll': {
                        'input': '$991.d', 
                        'find': '--', 
                        'replacement': '—'
                    }
                }, 
                'chars': ' '
            }
        }

        add_1['startDD'] = {'$ltrim': {'input': {'$arrayElemAt': [{'$split': ['$992.a', '-']}, 2]},'chars': '0'}}

        add_1['endDD'] = {
            '$cond': { 
                'if': '$992.b', 
                'then': { '$ltrim': { 'input': {'$arrayElemAt': [{'$split': ['$992.b', '-']}, 2] }, 'chars': '0' } }, 
                'else': 'N/A'
            }
        }

        add_1['startMM'] = {
            '$let': {
                'vars': { 'startMM': { '$arrayElemAt': [{'$split': ['$992.a', '-']}, 1 ] }
                }, 
                'in': {
                    '$switch': {
                        'branches': [
                            {'case': {'$eq': ['$$startMM', '01']},'then': 'Jan.'}, 
                            {'case': {'$eq': ['$$startMM', '02']},'then': 'Feb.'},
                            {'case': {'$eq': ['$$startMM', '03']},'then': 'Mar.'}, 
                            {'case': {'$eq': ['$$startMM', '04']},'then': 'Apr.'},
                            {'case': {'$eq': ['$$startMM', '05']},'then': 'May'},
                            {'case': {'$eq': ['$$startMM', '06']},'then': 'June'}, 
                            {'case': {'$eq': ['$$startMM', '07']},'then': 'July'},
                            {'case': {'$eq': ['$$startMM', '08']},'then': 'Aug.'},
                            {'case': {'$eq': ['$$startMM', '09']},'then': 'Sept.'},
                            {'case': {'$eq': ['$$startMM', '10']},'then': 'Oct.'}, 
                            {'case': {'$eq': ['$$startMM', '11']},'then': 'Nov.'},
                            {'case': {'$eq': ['$$startMM', '12']},'then': 'Dec.'}
                        ], 
                    'default': 'N/A'
                    }
                }
            }
        }

        add_1['endMM'] = {
            '$let': { 
                'vars': { 'startMM': { '$arrayElemAt': [   {   '$split': [ '$992.b', '-'   ]   }, 1 ] } }, 
                'in': {
                    '$switch': {
                        'branches': [
                            {'case': {'$eq': ['$$startMM', '01']},'then': 'Jan.'}, 
                            {'case': {'$eq': ['$$startMM', '02']},'then': 'Feb.'}, 
                            {'case': {'$eq': ['$$startMM', '03']},'then': 'Mar.'}, 
                            {'case': {'$eq': ['$$startMM', '04']},'then': 'Apr.'}, 
                            {'case': {'$eq': ['$$startMM', '05']},'then': 'May'}, 
                            {'case': {'$eq': ['$$startMM', '06']},'then': 'June'}, 
                            {'case': {'$eq': ['$$startMM', '07']},'then': 'July'}, 
                            {'case': {'$eq': ['$$startMM', '08']},'then': 'Aug.'}, 
                            {'case': {'$eq': ['$$startMM', '09']},'then': 'Sept.'}, 
                            {'case': {'$eq': ['$$startMM', '10']},'then': 'Oct.'}, 
                            {'case': {'$eq': ['$$startMM', '11']},'then': 'Nov.'}, 
                            {'case': {'$eq': ['$$startMM', '12']},'then': 'Dec.'} 
                            ], 
                        'default': 'N/A' 
                    } 
                }
            }
        }

        add_1['startYY'] = {'$ltrim': {'input': {'$arrayElemAt': [{'$split': ['$992.a', '-']}, 0]},'chars': '0'}}

        add_1['endYY'] = {
            '$cond': { 
                'if': '$992.b', 
                'then': { '$ltrim': { 'input': {'$arrayElemAt': [{'$split': ['$992.b', '-']}, 0] }, 'chars': '0' } }, 
                'else': 'N/A'
            }
        }

        add_stage1 = {}
        add_stage1['$addFields'] = add_1

        add_2 = {}

        add_2['publicationdate'] = { 
            '$let': {'vars': {
                'testMonth': {'$arrayElemAt': [{'$split': ['$269.a', '-']}, 1]},
                'testDate': {'$ltrim': { 'input': {'$arrayElemAt': [{'$split': [ '$269.a', '-']}, 2]}, 'chars': '0' }},
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
            '$switch': { 
                'branches': [ 
                    { 'case': {'$eq': ['$endDD', 'N/A'] }, 'then': {'$concat': ['$startDD', ' ', '$startMM', ' ', '$startYY'] } }, 
                    { 'case': {'$eq': ['$startMM', '$endMM'] }, 'then': {'$concat': ['$startDD', '-', '$endDD', ' ', '$startMM', ' ', '$startYY'] } }, 
                    { 'case': {'$ne': ['$startMM', '$endMM'] }, 'then': {'$concat': ['$startDD', ' ', '$startMM', '-', '$endDD', ' ', '$endMM', ' ', '$endYY'] } }
                ], 
                'default': 'N/A'
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
            
            transform['head'] = '$agendasubject' #'$991.d'

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
                    'then':  '$agendasubject', #'$991.d', 
                    'else': {
                        '$concat': [
                        '$agendasubject', #'$991.d',
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
                    'then':  '$agendasubject', #'$991.d', 
                    'else': {
                        '$concat': [
                        '$agendasubject', #'$991.d',
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
                    {'case': {'$and': [{'$or': [{'$eq': ['$code', 'C00']}, {'$eq': ['$code', 'G00']}, {'$eq': ['$code', 'X00']}]}, 
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
                                            'else': {
                                                '$cond': {
                                                    'if': {'$ne': ['$numberingnote', '']}, 
                                                    'then': {
                                                        '$concat': [
                                                            '. – ', 
                                                            '$numberingnote'
                                                        ]
                                                    }, 
                                                    'else': '.'
                                                }
                                            }
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
                'sortkey1': {
                    '$replaceAll': {
                        'input': {
                            '$replaceAll': {
                                'input': '$agendasubject', #'$head'
                                'find': '. ', 
                                'replacement': ' .'
                            }
                        }, 
                        'find': '—', 
                        'replacement': ' $'
                    }
                },#'$head',
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
        #clear the previous records if they exist
        outputCollection.delete_many({ "section" : "itpage", "bodysession" : bodysession } )
        
        pipeline = []
        pipeline2 = []

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        bs = bodysession.split("/")
        body = bs[0]
        session = bs[1]

        if body == "A":
            match_criteria = "A/" + session + "/251"
        
        if body == "E":
            year = session.split("-")
            match_criteria = "E/" + year[0] + "/100"
        
        if body == "S":
            match_stage1 = {
                '$match': {
                    'bodysession': bodysession, 
                    'record_type': 'BIB', 
                    '$or': [
                        {'191.9': 'X00'}, 
                        {'191.9': 'X01'}, 
                        {'191.9': 'X88'}
                    ]
                }
            }

            unwind_stage1 = {'$unwind': '$991'}

            unwind_stage2 = {'$unwind': '$191'}

            match_stage2 = {
                '$match': {
                    '991.a': bodysession, 
                    '191.b': body + '/'
                }
            }

            group_stage =  {
                '$group': {
                    '_id': {
                        '$replaceAll': {
                            'input': '$991.d', 
                            'find': '--', 
                            'replacement': '–'
                        }
                    }, 
                    'type': {
                        '$push': {
                            '$cond': {
                                'if': {'$gt': [{'$indexOfCP': ['$191.a', '/PV.']}, -1]}, 
                                'then': 'PV', 
                                'else': 'non-PV'
                            }
                        }
                    }
                }
            }

            add_stage = {
                '$addFields': {
                    'heading': {
                        '$cond': {
                            'if': {'$in': ['PV', '$type']}, 
                            'then': 'LIST OF MATTERS CONSIDERED BY THE SECURITY COUNCIL DURING XXXX', 
                            'else': 'OTHER MATTERS BROUGHT TO THE ATTENTION OF THE SECURITY COUNCIL DURING XXXX'
                        }
                    }
                }
            }   


            transform = {}
            transform['_id'] = 0
            transform['section'] = "itpage"
            transform['bodysession'] = bodysession
            transform['agendanum'] = ''
            transform['agendatitle'] = ''
            transform['agendasubject'] = '$_id'
            transform['heading'] = 1
            transform['sortkey1'] = '$heading'
            transform['sortkey2'] = '$_id'

            transform_stage = {}
            transform_stage['$project'] = transform

            sort_stage = {
                '$sort': {
                    'sortkey1': 1, 
                    'sortkey2': 1
                }
            }

            merge_stage = {
                '$merge': { 'into': editorOutput}
            }

            pipeline.append(match_stage1)
            pipeline.append(unwind_stage1)
            pipeline.append(unwind_stage2)
            pipeline.append(match_stage2)
            pipeline.append(group_stage)
            pipeline.append(add_stage)
            pipeline.append(transform_stage)
            pipeline.append(sort_stage)
            pipeline.append(merge_stage)

            inputCollection.aggregate(pipeline, collation=collation)
            group_itpage_S("itpage", bodysession)

        else: #A or E
            #### Insert Agenda records from AUTHs for records without []
            match_stage1 = {
                '$match': {
                    'bodysession': bodysession, 
                    'record_type': 'AUTH',
                    '191.b': {'$not': {'$regex': '\\['}}
                    }     
            }

            add_1 = {}

            add_1['agendaitem'] = {
                '$cond': {
                    'if': {'$eq': [{'$indexOfCP': ['$191.b', '[']}, -1]}, 
                    'then': '$191.b', 
                    'else': {'$substrCP': ['$191.b', 0, {'$indexOfCP': ['$191.b', '[']}]}
                }
            }

            add_1['agendatitle'] = {
                '$cond': {
                    'if': '$191.c', 
                    'then': '$191.c', 
                    'else': ''
                }
            }

            add_1['agendasubject'] = {
                '$cond': {
                    'if': '$191.d', 
                    'then': {
                        '$trim': {
                            'input': {
                                '$replaceAll': {
                                    'input': '$191.d', 
                                    'find': '--', 
                                    'replacement': '—'
                                }
                            }, 
                            'chars': ' '
                        }
                    },
                    'else': ''
                }
            }

            add_stage1 = {}

            add_stage1['$addFields'] = add_1

            add_2 = {}

            add_2['subagenda'] = {
                '$cond': {
                    'if': {
                        '$regexMatch': {
                            'input': '$agendaitem', 
                            'regex': '[a-z]'
                        }
                    }, 
                    'then': {
                        '$substrCP': [
                            '$agendaitem', 
                            {'$subtract': [{'$strLenCP': '$agendaitem'}, 1]}, 
                            1
                        ]
                    }, 
                    'else': ''
                }
            }

            add_stage2 = {}

            add_stage2['$addFields'] = add_2

            add_3 = {}

            add_3['agendanum'] = {
                '$cond': {
                    'if': {'$ne': ['$subagenda', '']}, 
                    'then': {
                        '$substrCP': [
                            '$agendaitem', 
                            0, 
                            {'$indexOfCP': ['$agendaitem', '$subagenda']}
                        ]
                    }, 
                    'else': '$agendaitem'
                }
            }

            add_stage3 = {}

            add_stage3['$addFields'] = add_3

            group_stage =  {
                '$group': {
                    '_id': {
                        'a': '$agendanum', 
                        'b': '$subagenda', 
                        'c': '$agendatitle', 
                        'd': '$agendasubject'
                    }
                }
            }

            transform = {}
            transform['_id'] = 0
            transform['section'] = "itpage"
            transform['bodysession'] = bodysession
            transform['agendanum'] = '$_id.a'
            transform['subagenda'] = '$_id.b'
            transform['agendatitle'] = '$_id.c'
            transform['agendasubject'] = '$_id.d'
            transform['heading'] = {
                '$cond': {
                    'if': {'$eq': ['$_id.a', '']}, 
                    'then': 'OTHER MATTERS INCLUDED IN THE INDEX', 
                    'else': 'AGENDA'
                }
            }
            transform['sortkey1'] = '$_id.a'
            
            transform['sortkey2'] = '$_id.b'

            transform['sortkey3'] = {
                '$replaceAll': {
                    'input': {
                        '$replaceAll': {
                            'input': '$_id.d', 
                            'find': '. ', 
                            'replacement': ' .'
                        }
                    }, 
                    'find': '—', 
                    'replacement': ' $'
                }
            }

            transform_stage = {}
            transform_stage['$project'] = transform

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
            pipeline.append(add_stage1)
            pipeline.append(add_stage2)
            pipeline.append(add_stage3)
            pipeline.append(group_stage)
            pipeline.append(transform_stage)
            pipeline.append(sort_stage)
            pipeline.append(merge_stage)
            
            #print(pipeline)
            inputCollection.aggregate(pipeline, collation=collation)

            #### Insert Agenda records from BIBSs for records with []

            match_stage1 = {
                '$match': {
                    'bodysession': bodysession, 
                    'record_type': 'BIB'
                    }     
            }

            unwind_stage = {'$unwind': '$991'}

            match_stage2 = {
                '$match': {
                    '991.a': match_criteria,
                    '991.b': {'$regex': '\\['}
                }
            }

            add_1 = {}

            add_1['agendaitem'] = {
                '$cond': {
                    'if': {'$eq': [{'$indexOfCP': ['$991.b', '[']}, -1]}, 
                    'then': '$191.b', 
                    'else': {'$substrCP': ['$991.b', 0, {'$indexOfCP': ['$991.b', '[']}]}
                }
            }

            add_1['agendatitle'] = {
                '$cond': {
                    'if': '$991.c', 
                    'then': '$991.c', 
                    'else': ''
                }
            }

            add_1['agendasubject'] = {
                '$cond': {
                    'if': '$991.d', 
                    'then': {
                        '$trim': {
                            'input': {
                                '$replaceAll': {
                                    'input': '$991.d', 
                                    'find': '--', 
                                    'replacement': '—'
                                }
                            }, 
                            'chars': ' '
                        }
                    }, 
                    'else': ''
                }
            }

            add_stage1 = {}

            add_stage1['$addFields'] = add_1

            pipeline2.append(match_stage1)
            pipeline2.append(unwind_stage)
            pipeline2.append(match_stage2)
            pipeline2.append(add_stage1)
            pipeline2.append(add_stage2)
            pipeline2.append(add_stage3)
            pipeline2.append(group_stage)
            pipeline2.append(transform_stage)
            pipeline2.append(sort_stage)
            pipeline2.append(merge_stage)

            #print(pipeline2)
            inputCollection.aggregate(pipeline2, collation=collation)
            group_itpage_AE("itpage", bodysession)

            #print(pipeline)

        return "itpage completed successfully"

    except Exception as e:    
        return e

# List of Documents #
def itpdsl(bodysession):
    """
    List of Documents. Executed for the follownig bodies: A/, E/ and S/.

    Builds the aggregation query based on business logic and inserts the results into another collection.
    """ 
    try: 
        # clear the previous records if they exist
        outputCollection.delete_many({ "section" : "itpdsl", "bodysession" : bodysession } )
        
        pipeline = []

        # set variables
        bs = bodysession.split("/")
        body = bs[0]
        session = bs[1]
        fullbody = body + "/"

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        # filter by bodysession and record type
        match_stage = {
            '$match': {
                'record_type': 'BIB', 
                'bodysession': bodysession
            }
        }

        # add fields to determine the order of the document symbols
        add_0 = {}

        add_0['primary'] = {
            '$cond': {
                'if': {'$isArray': '$191'}, 
                'then': {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$eq': [{'$arrayElemAt': ['$191.b', 0]}, fullbody]}, 
                                {'$eq': [{'$arrayElemAt': ['$191.c', 0]}, session]}
                            ]
                        }, 
                        'then': 0, 
                        'else': 1
                    }
                }, 
                'else': 'not an array'
            }
        }

        add_0['secondary'] = {
            '$cond': {
                'if': {'$isArray': '$191'}, 
                'then': {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$eq': [{'$arrayElemAt': ['$191.b', 1]}, fullbody]}, 
                                {'$eq': [{'$arrayElemAt': ['$191.c', 1]}, session]}
                            ]
                        }, 
                        'then': 0, 
                        'else': 1
                    }
                }, 
                'else': 'not an array'
            }
        }

        add_stage0 = {}

        add_stage0['$addFields'] = add_0

        # add fields to determine if the primary document symbol belongs to the actual session
        #   being run
        add_1 = {}

        add_1['actualsession'] = {
            '$let': {
                'vars': {
                    'sesh': {
                        '$cond': {
                            'if': {'$isArray': '$191'}, 
                            'then': {'$split': [{'$arrayElemAt': ['$191.c', '$primary']}, '/']}, 
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

        # add a field to concatenate all of the elements of the document symbol string
        add_2['docsymbol'] = {
            '$concat': [
                {'$cond': {
                    'if': {'$isArray': '$191'}, 
                    'then': {
                        '$concat': [
                            {'$arrayElemAt': ['$191.a', '$primary']}, 
                            {'$cond': {
                                'if': {'$eq': ['$primary', '$secondary']},
                                'then': {'$concat': [' (', {'$arrayElemAt': ['$191.a', 1]}, ')']}, 
                                'else': {'$concat': [' (', {'$arrayElemAt': ['$191.a', '$secondary']}, ')']},
                                }
                            }
                        ]
                    }, 
                    'else': '$191.a'
                    }
                }, 
                {'$cond': {
                    'if': {'$eq': ['$495', '']}, 
                    'then': '', 
                    'else': {'$concat': [' (', '$495.a', ')']}
                }}
            ]
        }

        # set the committee and series based on body
        if body == "A":

            add_2['committee'] = {
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
                                {'case': {'$eq': ['$actualsession', 'other']}, 
                                    'then': 'OTHER DOCUMENTS CONSIDERED BY THE MAIN COMMITTEES'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/C.1/']}, -1]}, 
                                    'then': 'DISARMAMENT AND INTERNATIONAL SECURITY COMMITTEE (FIRST COMMITTEE)'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/C.2/']}, -1]}, 
                                    'then': 'ECONOMIC AND FINANCIAL COMMITTEE (SECOND COMMITTEE)'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/C.3/']}, -1]}, 
                                    'then': 'SOCIAL, HUMANITARIAN AND CULTURAL COMMITTEE (THIRD COMMITTEE)'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/C.4/']}, -1]}, 
                                    'then': 'SPECIAL POLITICAL AND DECOLONIZATION COMMITTEE (FOURTH COMMITTEE)'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/C.5/']}, -1]}, 
                                    'then': 'ADMINISTRATIVE AND BUDGETARY COMMITTEE (FIFTH COMMITTEE)'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/C.6/']}, -1]}, 
                                    'then': 'LEGAL COMMITTEE (SIXTH COMMITTEE)'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/BUR/']}, -1]}, 
                                    'then': 'GENERAL COMMITTEE'}
                            ], 
                            'default': 'PLENARY'
                        }
                    }
                }
            }

            add_2['series'] = {
                '$let': {
                    'vars': {
                        'a': {
                            '$cond': {
                                'if': {'$isArray': '$191'}, 
                                'then': {'$arrayElemAt': ['$191.a', '$primary']}, 
                                'else': '$191.a'
                            }
                        }
                    }, 
                    'in': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$actualsession', 'other']}, 
                                    'then': ''},
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/L.']}, -1]}, 
                                    'then': 'Limited series'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/INF/']}, -1]}, 
                                    'then': 'Information series'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/PV.']}, -1]}, 
                                    'then': 'Verbatim records'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/RES/']}, -1]}, 
                                    'then': 'Resolutions and decisions'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/DEC/']}, -1]}, 
                                    'then': 'Resolutions and decisions'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/SR.']}, -1]}, 
                                    'then': 'Summary records'}, 
                            ], 
                            'default': 'General series'
                        }
                    }
                }
            }

        if body == "E": 
            
            add_2['committee'] = ""

            add_2['series'] = {
                '$let': {
                    'vars': {
                        'a': {
                            '$cond': {
                                'if': {'$isArray': '$191'}, 
                                'then': {'$arrayElemAt': ['$191.a', '$primary']}, 
                                'else': '$191.a'
                            }
                        }
                    }, 
                    'in': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$actualsession', 'other']}, 
                                    'then': 'Miscellaneous documents'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/HLS/']}, -1]}, 
                                    'then': 'Miscellaneous documents'},
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/L.']}, -1]}, 
                                    'then': 'Limited series'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/INF/']}, -1]}, 
                                    'then': 'Information series'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/RES/']}, -1]}, 
                                    'then': 'Resolutions and decisions'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/DEC/']}, -1]}, 
                                    'then': 'Resolutions and decisions'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/SR.']}, -1]}, 
                                    'then': 'Summary records'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/NGO/']}, -1]}, 
                                    'then': 'Non-governmental organizations series'}
                            ], 
                            'default': 'General series'
                        }
                    }
                }
            }

        if body == "S":

            add_2['committee'] = ""

            add_2['series'] = {
                '$let': {
                    'vars': {
                        'a': {
                            '$cond': {
                                'if': {'$isArray': '$191'}, 
                                'then': {'$arrayElemAt': ['$191.a', '$primary']}, 
                                'else': '$191.a'
                            }
                        }
                    }, 
                    'in': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$actualsession', 'other']}, 
                                    'then': 'Other documents'},
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/INF/']}, -1]}, 
                                    'then': 'Information series'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/PV.']}, -1]}, 
                                    'then': 'Verbatim records'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/RES/']}, -1]}, 
                                    'then': 'Resolutions'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/DEC/']}, -1]}, 
                                    'then': 'Resolutions'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/PRST/']}, -1]}, 
                                    'then': 'Statements of the President of the Security Council'}, 
                                {'case': {'$gt': [{'$indexOfCP': ['$$a', '/Agenda/']}, -1]}, 
                                    'then': 'Agenda series'}, 
                            ], 
                            'default': 'General series'
                        }
                    }
                }
            }

        add_stage2 = {}
        add_stage2['$addFields'] = add_2

        # set up the final project stage and create sortkeys based on the committees and series
        transform = {}

        transform['_id'] = 0
        transform['bodysession'] = 1
        transform['section'] = 1
        transform['record_id'] = 1
        transform['committee'] = 1
        transform['series'] = 1
        transform['docsymbol'] = 1

        if body == "A":
            transform['sortkey1'] = {
                '$let': {
                    'vars': {
                        'x': {'$substr': ['$committee', 0, 2]}
                    }, 
                    'in': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$$x', 'PL']}, 'then': '01'}, 
                                {'case': {'$eq': ['$$x', 'GE']}, 'then': '02'}, 
                                {'case': {'$eq': ['$$x', 'DI']}, 'then': '03'}, 
                                {'case': {'$eq': ['$$x', 'SP']}, 'then': '04'}, 
                                {'case': {'$eq': ['$$x', 'EC']}, 'then': '05'}, 
                                {'case': {'$eq': ['$$x', 'SO']}, 'then': '06'}, 
                                {'case': {'$eq': ['$$x', 'AD']}, 'then': '07'}, 
                                {'case': {'$eq': ['$$x', 'LE']}, 'then': '08'}, 
                                {'case': {'$eq': ['$$x', 'OT']}, 'then': '09'}
                            ], 
                            'default': '99'
                        }
                    }
                }
            }
            
            transform['sortkey2'] = {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$series', 'General series']}, 'then': '01'}, 
                        {'case': {'$eq': ['$series', 'Information series']}, 'then': '02'}, 
                        {'case': {'$eq': ['$series', 'Limited series']}, 'then': '03'}, 
                        {'case': {'$eq': ['$series', 'Verbatim records']}, 'then': '04'}, 
                        {'case': {'$eq': ['$series', 'Resolutions and decisions']}, 'then': '05'}, 
                        {'case': {'$eq': ['$series', 'Summary records']}, 'then': '06'}
                    ], 
                    'default': '99'
                }
            }
           
        
        if body == "E":
            transform['sortkey1'] = "01"
            
            transform['sortkey2'] =  {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$series', 'General series']}, 'then': '01'}, 
                        {'case': {'$eq': ['$series', 'Information series']}, 'then': '02'}, 
                        {'case': {'$eq': ['$series', 'Limited series']}, 'then': '03'}, 
                        {'case': {'$eq': ['$series', 'Non-governmental organizations series']}, 'then': '04'}, 
                        {'case': {'$eq': ['$series', 'Summary records']}, 'then': '05'},
                        {'case': {'$eq': ['$series', 'Miscellaneous documents']}, 'then': '06'},
                        {'case': {'$eq': ['$series', 'Resolutions and decisions']}, 'then': '07'}
                    ], 
                    'default': '99'
                }
            }
            
        if body == "S":
            transform['sortkey1'] = "01"

            transform['sortkey2'] =  {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$series', 'General series']}, 'then': '01'}, 
                        {'case': {'$eq': ['$series', 'Agenda series']}, 'then': '02'},
                        {'case': {'$eq': ['$series', 'Verbatim records']}, 'then': '03'},
                        {'case': {'$eq': ['$series', 'Resolutions']}, 'then': '04'},
                        {'case': {'$eq': ['$series', 'Statements of the President of the Security Council']}, 'then': '05'},
                        {'case': {'$eq': ['$series', 'Information series']}, 'then': '06'},
                        {'case': {'$eq': ['$series', 'Other documents']}, 'then': '07'},                        
                    ], 
                    'default': '99'
                }
            }

        transform['sortkey3'] = '$docsymbol'

        transform_stage = {}
        transform_stage['$project'] = transform

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

        # add all stages to the pipeline
        pipeline.append(match_stage)
        pipeline.append(add_stage0)
        pipeline.append(add_stage1)
        pipeline.append(add_stage2)
        pipeline.append(transform_stage)
        pipeline.append(sort_stage)
        pipeline.append(merge_stage)

        # execute pipeline
        inputCollection.aggregate(pipeline, collation=collation)

        # further process results by grouping them for display
        group_itpdsl("itpdsl", bodysession)

        return "itpdsl completed successfully"

    except Exception as e:
        return e

# Check List of Meetings #
def itpmeet(bodysession):
    """
    Check List of Meetings

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 

        outputCollection.delete_many({ "section" : "itpmeet", "bodysession" : bodysession } )

        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]
        session = bs[1]

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }
        
        add_1 = {}

        if body == "A":
            match_stage1 = {
                '$match': {
                    'bodysession': bodysession, 
                    '$or': [
                        {'191.a': {'$regex': '/SR.'}}, 
                        {'191.a': {'$regex': '/PV.'}}
                    ]
                }
            }

            unwind_stage = {'$unwind': '$191'}

            match_stage2 = {
                '$match': {
                    '191.b': body + "/",
                    '191.c': session, 
                }
            }
        
            add_1['code'] = {'$substrCP': ['$191.9', 2, 1]}

            add_1['meetingnum'] = {
                '$substrCP': [
                    '$191.a', 
                    {'$add': [{'$indexOfCP': ['$191.a', '.', 5]}, 1]}, 
                    {'$strLenCP': '$191.a'}
                ]
            }


        if body == "E":
            match_stage1 = {
                '$match': {
                    'bodysession': bodysession, 
                    '191.a': {
                        '$regex': '/SR.'
                    }
                }
            }

            unwind_stage = {'$unwind': '$191'}

            match_stage2 = {
                '$match': {
                    '191.b': body + "/",
                    '191.c': session, 
                }
            }

            add_1['meetingnum'] = {
                '$arrayElemAt': [{'$split': ['$191.a', '.']}, 1]
            }

        
        if body == "S":
            match_stage1 = {
                '$match': {
                    'bodysession': bodysession, 
                    '191.a': {
                        '$regex': '/PV.'
                    }
                }
            }

            add_1['meetingnum'] = {
                '$arrayElemAt': [{'$split': ['$191.a', '.']}, 1]
            }
        
        
        add_1['meetingyear'] = {
            '$trim': {
                'input': {'$arrayElemAt': [{'$split': ['$992.a', '-']}, 0]}, 
                'chars': ' '
            }
        }

        add_1['startDD'] = {'$ltrim': {'input': {'$arrayElemAt': [{'$split': ['$992.a', '-']}, 2]},'chars': '0'}}

        add_1['endDD'] = {
            '$cond': { 
                'if': '$992.b', 
                'then': { '$ltrim': { 'input': {'$arrayElemAt': [{'$split': ['$992.b', '-']}, 2] }, 'chars': '0' } }, 
                'else': 'N/A'
            }
        }

        add_1['startMM'] = {
            '$let': {
                'vars': { 'startMM': { '$arrayElemAt': [{'$split': ['$992.a', '-']}, 1 ] }
                }, 
                'in': {
                    '$switch': {
                        'branches': [
                            {'case': {'$eq': ['$$startMM', '01']},'then': 'Jan.'}, 
                            {'case': {'$eq': ['$$startMM', '02']},'then': 'Feb.'},
                            {'case': {'$eq': ['$$startMM', '03']},'then': 'Mar.'}, 
                            {'case': {'$eq': ['$$startMM', '04']},'then': 'Apr.'},
                            {'case': {'$eq': ['$$startMM', '05']},'then': 'May'},
                            {'case': {'$eq': ['$$startMM', '06']},'then': 'June'}, 
                            {'case': {'$eq': ['$$startMM', '07']},'then': 'July'},
                            {'case': {'$eq': ['$$startMM', '08']},'then': 'Aug.'},
                            {'case': {'$eq': ['$$startMM', '09']},'then': 'Sept.'},
                            {'case': {'$eq': ['$$startMM', '10']},'then': 'Oct.'}, 
                            {'case': {'$eq': ['$$startMM', '11']},'then': 'Nov.'},
                            {'case': {'$eq': ['$$startMM', '12']},'then': 'Dec.'}
                        ], 
                    'default': 'N/A'
                    }
                }
            }
        }

        add_1['endMM'] = {
            '$let': { 
                'vars': { 'startMM': { '$arrayElemAt': [   {   '$split': [ '$992.b', '-'   ]   }, 1 ] } }, 
                'in': {
                    '$switch': {
                        'branches': [
                            {'case': {'$eq': ['$$startMM', '01']},'then': 'Jan.'}, 
                            {'case': {'$eq': ['$$startMM', '02']},'then': 'Feb.'}, 
                            {'case': {'$eq': ['$$startMM', '03']},'then': 'Mar.'}, 
                            {'case': {'$eq': ['$$startMM', '04']},'then': 'Apr.'}, 
                            {'case': {'$eq': ['$$startMM', '05']},'then': 'May'}, 
                            {'case': {'$eq': ['$$startMM', '06']},'then': 'June'}, 
                            {'case': {'$eq': ['$$startMM', '07']},'then': 'July'}, 
                            {'case': {'$eq': ['$$startMM', '08']},'then': 'Aug.'}, 
                            {'case': {'$eq': ['$$startMM', '09']},'then': 'Sept.'}, 
                            {'case': {'$eq': ['$$startMM', '10']},'then': 'Oct.'}, 
                            {'case': {'$eq': ['$$startMM', '11']},'then': 'Nov.'}, 
                            {'case': {'$eq': ['$$startMM', '12']},'then': 'Dec.'} 
                            ], 
                        'default': 'N/A' 
                    } 
                }
            }
        }
                    
        add_stage = {}
        add_stage['$addFields'] = add_1
        
        transform = {}
        transform['_id'] = 0
        transform['record_id'] = 1
        transform['section'] = "itpmeet"
        transform['bodysession'] = 1

        transform['docsymbol'] = '$191.a'

        if body == "A":
            transform['symbol'] = {
                '$concat': [
                    {'$substrCP': ['$191.a', 0, {'$indexOfCP': ['$191.a', '.', 5]}]}, 
                    '.-'
                ]
            }

            transform['committee1'] = {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$code', 'A']},'then': 'General Committee' }, 
                        {'case': {'$eq': ['$code', '1']},'then': 'Disarmament and International Security Committee' }, 
                        {'case': {'$eq': ['$code', '2']},'then': 'Economic and Financial Committee' }, 
                        {'case': {'$eq': ['$code', '3']},'then': 'Social, Humanitarian and Cultural Committee' }, 
                        {'case': {'$eq': ['$code', '4']},'then': 'Special Political and Decolonization Committee' }, 
                        {'case': {'$eq': ['$code', '5']},'then': 'Administrative and Budgetary Committee' }, 
                        {'case': {'$eq': ['$code', '6']},'then': 'Legal Committee' }, 
                        {'case': {'$eq': ['$code', '8']},'then': 'Plenary' }, 
                        {'case': {'$eq': ['$code', '9']},'then': 'Credentials Committee' }
                    ], 
                'default': ''
                }
            }

            transform['committee2'] = {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$code', '1'] }, 'then': '(First Committee)' }, 
                        {'case': {'$eq': ['$code', '2'] }, 'then': '(Second Committee)' }, 
                        {'case': {'$eq': ['$code', '3'] }, 'then': '(Third Committee)' }, 
                        {'case': {'$eq': ['$code', '4'] }, 'then': '(Fourth Committee)' }, 
                        {'case': {'$eq': ['$code', '5'] }, 'then': '(Fifth Committee)' }, 
                        {'case': {'$eq': ['$code', '6'] }, 'then': '(Sixth Committee)' }
                    ], 
                    'default': ''
                }
            }

            transform['sortkey1'] = {
                '$switch': {
                    'branches': [
                        {'case': {'$eq': ['$code', 'A']}, 'then': '03'}, 
                        {'case': {'$eq': ['$code', '1']}, 'then': '04'}, 
                        {'case': {'$eq': ['$code', '2']}, 'then': '06'}, 
                        {'case': {'$eq': ['$code', '3']}, 'then': '07'}, 
                        {'case': {'$eq': ['$code', '4']}, 'then': '05'}, 
                        {'case': {'$eq': ['$code', '5']}, 'then': '08'}, 
                        {'case': {'$eq': ['$code', '6']}, 'then': '09'}, 
                        {'case': {'$eq': ['$code', '8']}, 'then': '01'}, 
                        {'case': {'$eq': ['$code', '9']}, 'then': '02'}
                    ], 
                    'default': ''
                }
            }

        else:
            transform['symbol'] = {
                '$concat': [
                    {'$arrayElemAt': [{'$split': ['$191.a', '.']}, 0]}, 
                    '.-'
                ]
            }

            transform['committee1'] = ''

            transform['committee2'] = ''

            transform['sortkey1'] = 1

        transform['meetingnum'] = 1

        transform['meetingdate'] = {
            '$switch': { 
                'branches': [ 
                    { 'case': {'$eq': ['$endDD', 'N/A'] }, 'then': {'$concat': ['$startDD', ' ', '$startMM'] } }, 
                    { 'case': {'$eq': ['$startMM', '$endMM'] }, 'then': {'$concat': ['$startDD', '-', '$endDD', ' ', '$startMM'] } }, 
                    { 'case': {'$ne': ['$startMM', '$endMM'] }, 'then': {'$concat': ['$startDD', ' ', '$startMM', '-', '$endDD', ' ', '$endMM'] } }
                ], 
                'default': 'N/A'
            }
        }

        transform['meetingyear'] = 1
        transform['sortkey2'] = '$meetingyear'
        transform['sortkey3'] = '$meetingnum'

        transform_stage = {}
        transform_stage['$project'] = transform

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

        
        if body != "S":
            pipeline.append(unwind_stage)
            pipeline.append(match_stage2)
        
        pipeline.append(add_stage)
        pipeline.append(transform_stage)
        pipeline.append(sort_stage)
        pipeline.append(merge_stage)

        #print(pipeline)
        
        inputCollection.aggregate(pipeline, collation=collation)

        group_itpmeet("itpmeet", bodysession)

        return "itpmeet completed successfully"

    except Exception as e:
        return e

# Reports of the main and procedural committees #
def itpreps(bodysession):
    """
    Reports of the main and procedural committees

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 
        outputCollection.delete_many({ "section" : "itpreps", "bodysession" : bodysession } )
        
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
                'bodysession': bodysession, 
                'record_type': 'BIB', 
                '089.b': 'B04'
                }
        }
        
        unwind_stage1 = {'$unwind': '$191'}

        unwind_stage2 = {'$unwind': '$991'}
        
        match_stage2 = {
            '$match': {
                '191.b': body + '/', 
                '191.c': session, 
                '$or': [
                    {'191.9': 'G09'}, 
                    {'191.9': 'G1A'}, 
                    {'191.9': 'G11'}, 
                    {'191.9': 'G14'}, 
                    {'191.9': 'G22'}, 
                    {'191.9': 'G33'}, 
                    {'191.9': 'G55'}, 
                    {'191.9': 'G66'}
                ],
                '991.b': {'$not': {'$regex': '\\['}},
                '991.d': {'$exists': True}
            }
        }

        transform = {}
        transform['_id'] = 0
        transform['record_id'] = 1
        transform['section'] = "itpreps"
        transform['bodysession'] = 1

        transform['docsymbol'] = '$191.a'
        
        transform['subject'] = {
            '$replaceAll': {
                'input': '$991.d', 
                'find': '--', 
                'replacement': '–'
            }
        }

        transform['committee'] = {
            '$switch': {
                'branches': [
                    {'case': {'$eq': ['$191.9', 'G09']}, 
                        'then': 'CREDENTIALS COMMITTEE'}, 
                    {'case': {'$eq': ['$191.9', 'G1A']}, 
                        'then': 'GENERAL COMMITTEE'}, 
                    {'case': {'$eq': ['$191.9', 'G11']}, 
                        'then': 'DISARMAMENT AND INTERNATIONAL SECURITY COMMITTEE (FIRST COMMITTEE)'}, 
                    {'case': {'$eq': ['$191.9', 'G14']}, 
                        'then': 'SPECIAL POLITICAL AND DECOLONIZATION COMMITTEE (FOURTH COMMITTEE)'}, 
                    {'case': {'$eq': ['$191.9', 'G22']}, 
                        'then': 'ECONOMIC AND FINANCIAL COMMITTEE (SECOND COMMITTEE)'}, 
                    {'case': {'$eq': ['$191.9', 'G33']}, 
                        'then': 'SOCIAL, HUMANITARIAN AND CULTURAL COMMITTEE (THIRD COMMITTEE)'}, 
                    {'case': {'$eq': ['$191.9', 'G55']}, 
                        'then': 'ADMINISTRATIVE AND BUDGETARY COMMITTEE (FIFTH COMMITTEE)'}, 
                    {'case': {'$eq': ['$191.9', 'G66']}, 
                        'then': 'LEGAL COMMITTEE (SIXTH COMMITTEE)'}
                ], 
                'default': 'Not found'
            }
        }

        transform['sortkey1'] = {
            '$switch': {
                'branches': [
                    {'case': {'$eq': ['$191.9', 'G09']}, 'then': '01'}, 
                    {'case': {'$eq': ['$191.9', 'G1A']}, 'then': '02'}, 
                    {'case': {'$eq': ['$191.9', 'G11']}, 'then': '03'}, 
                    {'case': {'$eq': ['$191.9', 'G14']}, 'then': '04'}, 
                    {'case': {'$eq': ['$191.9', 'G22']}, 'then': '05'}, 
                    {'case': {'$eq': ['$191.9', 'G33']}, 'then': '06'}, 
                    {'case': {'$eq': ['$191.9', 'G55']}, 'then': '07'}, 
                    {'case': {'$eq': ['$191.9', 'G66']}, 'then': '08'}
                ], 
                'default': 'Not found'
            }
        }

        transform['sortkey2'] = {
            '$replaceAll': {
                'input': {
                    '$replaceAll': {
                        'input': '$991.d', 
                        'find': '. ', 
                        'replacement': ' $'
                    }
                }, 
                'find': '--', 
                'replacement': ' .'
            }
        }

        transform['sortkey3'] = '$191.a'

        transform_stage = {}
        transform_stage['$project'] = transform

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
        pipeline.append(transform_stage)
        pipeline.append(sort_stage)
        pipeline.append(merge_stage)

        inputCollection.aggregate(pipeline, collation=collation)

        group_itpreps("itpreps", bodysession)

        return "itpreps completed successfully"

    except Exception as e:
        return e

# Vote Chart #
def itpvot(bodysession): 
    """
    Vote Chart

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try: 
        outputCollection.delete_many({ "section" : "itpvot", "bodysession" : bodysession } )
        
        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]
        session = bs[1]

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }

        if body == "S":
            match_stage = {
                '$match': {
                    'bodysession': bodysession, 
                    'record_type': 'VOT', 
                    '591.a': {
                        '$ne': 'ADOPTED WITHOUT VOTE'
                    }, 
                    '791.a': {
                        '$regex': re.compile(r"RES")
                    }, 
                    '791.b': body + "/", 
                    '791.c': session
                }
            }

            lookup_stage = {
                '$lookup': {
                    'from': 'itp_codes', 
                    'localField': '967.c', 
                    'foreignField': 'code', 
                    'as': 'country_info'
                }
            }
        
            transform = {}
            transform['_id'] = 0
            transform['record_id'] = 1
            transform['section'] = "itpvot"
            transform['bodysession'] = 1
            
            transform['docsymbol'] = '$791.a'

            transform['resnum'] = {
                '$substrCP': [
                    '$791.a', 
                    {'$add': [1, {'$indexOfCP': ['$791.a', '/', 2]}]}, 
                    4
                ]
            }

            transform['votelist'] = {
                '$map': {
                    'input': {
                        '$zip': {
                            'inputs': [
                                '$country_info.text', 
                                '$967.d'
                            ]
                        }
                    }, 
                    'as': 'list', 
                    'in': {
                        'memberstate': {'$arrayElemAt': ['$$list', 0]}, 
                        'vote': {'$arrayElemAt': ['$$list', 1]
                        }
                    }
                }
            }

            transform['sortkey1'] = '$791.a'

            transform_stage = {}
            transform_stage['$project'] = transform

            sort_stage = {
                '$sort': {
                    'sortkey1': 1
                }
            }

            merge_stage = {
                '$merge': { 'into': editorOutput}
            }

            pipeline.append(match_stage)
            pipeline.append(lookup_stage)
            pipeline.append(transform_stage)
            pipeline.append(sort_stage)
            pipeline.append(merge_stage)

            inputCollection.aggregate(pipeline)

        if body == 'A':
            match_stage = {
                '$match': {
                    'bodysession': bodysession, 
                    'record_type': 'VOT', 
                    '591.a': {
                        '$ne': 'ADOPTED WITHOUT VOTE'
                    }, 
                    '791.a': {
                        '$regex': re.compile(r"RES")
                    }, 
                    '791.b': body + "/", 
                    '791.c': session
                }
            }

            unwind_stage = { '$unwind': '$967'}

            lookup_stage = {
                '$lookup': {
                    'from': 'itp_codes', 
                    'localField': '967.c', 
                    'foreignField': 'code', 
                    'as': 'country_info'
                }
            }

            add_1 = {}

            add_1['order'] = '$967.a'
            add_1['memberstate'] = {'$arrayElemAt': ['$country_info.text', 0]}
            add_1['vote'] = {
                '$cond': {
                    'if': '$967.d', 
                    'then': '$967.d', 
                    'else': ''
                }
            }

            add_stage1 = {}

            add_stage1['$addFields'] = add_1

            group_stage =  {
                '$group': {
                    '_id': {
                        'r': '$record_id', 
                        'docsymbol': '$791.a', 
                        'resnum': {
                            '$substrCP': [
                                '$791.a', 
                                {'$add': [4, {'$indexOfCP': ['$791.a', '/', 2]}]}, 
                                4
                            ]
                        }
                    }, 
                    'votelist': {
                        '$push': {
                            'order': '$order', 
                            'memberstate': '$memberstate', 
                            'vote': '$vote'
                        }
                    }
                }
            }

            transform = {}

            transform['_id'] = 0
            transform['record_id'] = '$_id.r'
            transform['section'] = "itpvot"
            transform['bodysession'] = bodysession
            
            transform['docsymbol'] = '$_id.docsymbol'
            transform['resnum'] = '$_id.resnum'
            transform['votelist'] = 1
            transform['sortkey1'] = '$_id.resnum'

            transform_stage = {}
            transform_stage['$project'] = transform

            sort_stage = {
                '$sort': {
                    'sortkey1': 1
                }
            }

            merge_stage = {
                '$merge': { 'into': editorOutput}
            }

            pipeline.append(match_stage)
            pipeline.append(unwind_stage)
            pipeline.append(lookup_stage)
            pipeline.append(add_stage1)
            pipeline.append(group_stage)
            pipeline.append(transform_stage)
            pipeline.append(sort_stage)
            pipeline.append(merge_stage)

            inputCollection.aggregate(pipeline, collation=collation )


        #for the word collection
        copyPipeline = []

        copyMatch_stage = {
            '$match': {
                'bodysession': bodysession, 
                'section': "itpvot"
            }
        }

        copyMerge_stage = {
            '$merge': { 'into': wordOutput}
        }
        
        clear_section("itpvot", bodysession)

        copyPipeline.append(copyMatch_stage)
        copyPipeline.append(copyMerge_stage)

        outputCollection.aggregate(copyPipeline)

        return "itpvot completed successfully"

    except Exception as e:
        return e

# Suppliments to Official Records #
def itpsor(bodysession): 
    """
    Suppliments to Official Records

    Builds the aggregation query and inserts the results into another collection.
    """ 
    try:
         
        #clear the previous records if they exist
        outputCollection.delete_many({ "section" : "itpsor", "bodysession" : bodysession } )
        
        pipeline = []

        bs = bodysession.split("/")
        body = bs[0]
        session = bs[1]
        fullbody = body + "/"

        collation={
            'locale': 'en', 
            'numericOrdering': True
        }
      
        if body == 'A':
            match_stage = {
                '$match': {
                    'bodysession': bodysession, 
                    'record_type': 'BIB', 
                    '$and': [
                    {
                        '191.a': {
                            '$not': {
                                '$regex': re.compile(r"RES")
                            }
                        }
                    }, {
                        '191.a': {
                            '$not': {
                                '$regex': re.compile(r"DEC")
                            }
                        }
                    }, {
                        '191.a': {
                            '$not': {
                                '$regex': re.compile(r"PV")
                            }
                        }
                    }, {
                        '191.a': {
                            '$not': {
                                '$regex': re.compile(r"SR")
                            }
                        }
                    }
                ], 
                    '495.a': {
                        '$regex': re.compile(r"GAOR")
                    }, 
                }
            }
        
        if body == 'E':
            match_stage = {
                '$match': {
                    'bodysession': bodysession, 
                    'record_type': 'BIB', 
                    '$and': [
                        {
                            '191.a': {
                                '$not': {
                                    '$regex': re.compile(r"RES")
                                }
                            }
                        }, {
                            '191.a': {
                                '$not': {
                                    '$regex': re.compile(r"DEC")
                                }
                            }
                        }, {
                            '191.a': {
                                '$not': {
                                    '$regex': re.compile(r"PV")
                                }
                            }
                        }, {
                            '191.a': {
                                '$not': {
                                    '$regex': re.compile(r"SR")
                                }
                            }
                        }
                    ], 
                    '495.a': {
                        '$regex': re.compile(r"ESCOR")
                    }, 
                }
            }

        add_1 = {}

        add_1['supplno'] = {
            '$let': {
                'vars': {
                    'a': {'$add': [{'$indexOfCP': ['$495.a', 'no.']}, 4]}, 
                    'b': {'$strLenCP': '$495.a'}
                }, 
                'in': {
                    '$substrCP': ['$495.a', '$$a', {'$subtract': ['$$b', '$$a']}]
                }
            }
        }

        add_1['title'] = {
            '$concat': [
                '$245.a', 
                {'$cond': {
                    'if': '$245.b', 
                    'then': {
                        '$concat': [
                            ' ', 
                            {'$trim': {'input': '$245.b', 'chars': ' '}}
                        ]
                    }, 
                    'else': ''
                }}, 
                {'$cond': {
                    'if': '$245.c', 
                    'then': {
                        '$concat': [
                            ' ', 
                            '$245.c'
                        ]
                    }, 
                    'else': ''
                }},
                {
				'$cond': {
					'if': '$245.n',
					'then': {
						'$concat': [' ', '$245.n']
					},
					'else': ''
				}
                },
                {
                    '$cond': {
                        'if': '$245.p',
                        'then': {
                            '$concat': [' ', '$245.p']
                        },
                        'else': ''
                    }
                }, 
                '.'
            ]
        }

        add_1['imprint'] = {
            '$concat': [
                #'$260.a', 
                {'$cond': {
                    'if': {'$isArray': ['$260.a']}, 
                    'then': {
                        '$concat': [
                            {'$arrayElemAt': ['$260.a', 0]}, 
                            ' ', 
                            {'$arrayElemAt': ['$260.a', 1]}
                        ]
                    }, 
                    'else': '$260.a'
                }},
                {'$cond': {
                    'if': '$260.b', 
                    'then': {
                        '$concat': [
                            ' ', 
                            {'$trim': {'input': '$260.b', 'chars': ' '}}
                        ]
                    }, 
                    'else': ''
                }}, 
                {'$cond': {
                    'if': '$260.c', 
                    'then': {
                        '$concat': [
                            ' ', '$260.c'
                        ]
                    }, 
                    'else': ''
                }}, 
                '.'
            ]
        }

        add_1['physdesc'] = {
            '$concat': [
                '$300.a', 
                {'$cond': {
                    'if': '$300.b', 
                    'then': {
                        '$concat': [
                            ' ', 
                            {'$trim': {'input': '$300.b', 'chars': ' '}}
                        ]
                    }, 
                    'else': ''
                }}
            ]
        }#'$300.a'

        add_1['ordocno'] = '$495.a'

        add_1['actualsession'] = {
            '$let': {
                'vars': {
                    'sesh': {
                        '$cond': {
                            'if': {'$isArray': '$191'}, 
                            'then': {'$split': [{'$arrayElemAt': ['$191.c', '$primary']}, '/']}, 
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

        add_stage1 = {}

        add_stage1['$addFields'] = add_1

        match_stage2 = {
            '$match': {'actualsession': 'current'}
        }

        transform = {}

        transform['_id'] = 0
        transform['bodysession'] = 1
        transform['section'] = 'itpsor'
        transform['record_id'] = 1

        transform['sorentry'] = {
            '$concat': [
                'No. ', 
                '$supplno'
            ]
        }

        transform['docsymbol'] = {
            '$cond': {
                'if': {'$isArray': '$191'}, 
                'then': {
                    '$let': {
                        'vars': {
                            'a': {'$arrayElemAt': ['$191.b', 0]}, 
                            'b': {'$arrayElemAt': ['$191.c', 0]}, 
                            'x': {'$arrayElemAt': ['$191.b', 1]}, 
                            'y': {'$arrayElemAt': ['$191.c', 1]}, 
                            'first': {'$arrayElemAt': ['$191.a', 0]}, 
                            'second': {'$arrayElemAt': ['$191.a', 1]}
                        }, 
                        'in': {
                            '$cond': {
                                'if': {
                                    '$and': [
                                        {'$eq': ['$$a', fullbody]}, 
                                        {'$eq': ['$$b', session]}, 
                                        '$$second'
                                    ]
                                }, 
                                'then': {
                                    '$concat': [
                                        '$$first', ' (', '$$second', ')'
                                    ]
                                }, 
                                'else': {
                                    '$cond': {
                                        'if': {
                                            '$and': [
                                                {'$eq': ['$$x', fullbody]}, 
                                                {'$eq': ['$$y', session]}, 
                                                '$$second'
                                            ]
                                        }, 
                                        'then': {
                                            '$concat': [
                                                '$$second', ' (', '$$first', ')'
                                            ]
                                        }, 
                                        'else': '$$first'
                                    }
                                }
                            }
                        }
                    }
                }, 
                'else': '$191.a'
            }
        }

        transform['sornorm'] = {
            '$concat': [
                '$title', ' - ', '$imprint'
            ]
        }

        transform['sornote'] = {
            '$concat': [
                '$physdesc', ' - ', '(', '$ordocno', ')', '.'
            ]
        }

        transform_stage = {}
        transform_stage['$project'] = transform

        add_2 = {}

        add_2['sortkey1'] = '$sorentry'
        add_2['sortkey2'] = '$docsymbol'

        add_stage2 = {}
        add_stage2['$addFields'] = add_2

        sort_stage = {
            '$sort': {
                'sortkey1': 1, 
                'sortkey2': 1
            }
        }

        merge_stage = {
            '$merge': { 'into': editorOutput}
        }

        pipeline.append(match_stage)
        pipeline.append(add_stage1)
        pipeline.append(match_stage2)
        pipeline.append(transform_stage)
        pipeline.append(add_stage2)
        pipeline.append(sort_stage)
        pipeline.append(merge_stage)

        #print(pipeline)

        inputCollection.aggregate(pipeline, collation=collation)
        #inputCollection.aggregate(pipeline)

        insert_itpsor("itpsor", bodysession)

        copyPipeline = []

        copyMatch_stage = {
            '$match': {
                'bodysession': bodysession, 
                'section': "itpsor"
            }
        }

        copySort_stage = {
            '$sort': {
                'sortkey1': 1, 
                'sortkey2': 1
            }
        }

        copyMerge_stage = {
            '$merge': { 'into': wordOutput}
        }
        
        clear_section("itpsor", bodysession)

        copyPipeline.append(copyMatch_stage)
        copyPipeline.append(copySort_stage)
        copyPipeline.append(copyMerge_stage)

        outputCollection.aggregate(copyPipeline, collation=collation)

        return "itpsor completed successfully"

    except Exception as e:
        return e

#### END Data transformations for each section ####

## Main function / switch ##
def process_section(bodysession, section):
    """
    Executes sections based on input.

    """ 
    bs = bodysession.split("/")
    body = bs[0]

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
    elif section == "itpvot" and body != "E": 
        s = itpvot(bodysession) #vote
    elif section == "itpsor" and body != "S": 
        s = itpsor(bodysession) #suppliments to official records
    elif section == "itpreps" and body == "A": 
        s = itpreps(bodysession) #reports
    else: 
        s = section + ": This section cannot be executed for this body (" + body + ")."

    print(section, ": " , s)

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
    
    #sort_stage1 = {
    #    '$sort': {
    #        'sortkey1': 1, 
    #        'sortkey2': 1, 
    #        'sortkey3': 1
    #    }
    #}
    
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
                'sort': {
                    '$substrCP': ['$_id.sortkey1', 0, {'$indexOfCP': ['$_id.sortkey1', '+']}]
                }
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
    #pipeline.append(sort_stage1)
    pipeline.append(group_stage1)
    pipeline.append(sort_stage2)
    pipeline.append(group_stage2)
    pipeline.append(sort_stage3)
    pipeline.append(group_stage3)
    pipeline.append(sort_stage4)
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    #print(pipeline)

    #outputCollection.aggregate(pipeline)

    outputCollection.aggregate(pipeline, 
        collation={
            'locale': 'en', 
            'strength': 1, #ignore diacritics
        })

def group_itpitsp(section, bodysession):

    clear_section(section, bodysession)

    pipeline = []

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            'section': section
        }
    }
    
    #sort_stage1 = {
    #    '$sort': {
    #        'sortkey1': 1, 
    #        'sortkey2': 1, 
    #        'sortkey3': 1
    #    }
    #}
    
    group_stage1 = {
        '$group': {
            '_id': {
                'itshead': '$itshead', 
                'itsubhead': '$itssubhead', 
                #'itsentry': '$itsentry', 
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
                'sortkey1': '$_id.sortkey1',
                'sortkey2': '$_id.sortkey2'
            }, 
            'itsentries': {
                '$push': {
                    #'itsentry': '$_id.itsentry', 
                    'docsymbols': '$docsymbols'
                }
            }
        }
    }
    
    sort_stage3 = {
        '$sort': {
            '_id.sortkey1': 1,
            '_id.sortkey2': 1
        }
    }

    group_stage3 = {
        '$group': {
            '_id': {
                'itshead': '$_id.itshead',
                'sort': {'$substrCP': ['$_id.sortkey1', 0, {'$indexOfCP': ['$_id.sortkey1', '+']}]}
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
    #pipeline.append(sort_stage1)
    pipeline.append(group_stage1)
    pipeline.append(sort_stage2)
    pipeline.append(group_stage2)
    pipeline.append(sort_stage3)
    pipeline.append(group_stage3)
    pipeline.append(sort_stage4)
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    #print(pipeline)

    outputCollection.aggregate(pipeline, 
        collation={
            'locale': 'en', 
            'strength': 1, #ignore diacritics
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

    #sort_stage1 = {
    #    '$sort': {
    #        'sortkey1': 1, 
    #        'sortkey2': 1, 
    #        'sortkey3': 1
    #    }
    #}

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
                'itp_head': '$_id.itp_head',
                'sortkey1': '$_id.sortkey1'
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
            '_id.sortkey1': 1
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
    #pipeline.append(sort_stage1)
    pipeline.append(group_stage1)
    pipeline.append(sort_stage2)
    pipeline.append(group_stage2)
    #pipeline.append(group_stage3)
    pipeline.append(sort_stage3)
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    #print(pipeline)

    outputCollection.aggregate(pipeline)
    #, collation={
    #    'locale': 'simple'
    #    'locale': 'en', 
    #    'strength': 1, #ignore diacritics
    #'numericOrdering': True,
    ##'alternate': 'shifted' #ignore punctuation
    #}) 

def group_itpdsl(section, bodysession):
    
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
                'committee': '$committee', 
                'series': '$series', 
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
                'committee': '$_id.committee', 
                'sortkey1': '$_id.sortkey1'
            }, 
            'series': {
                '$push': {
                    'series': '$_id.series', 
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
    
    project_stage = {
        '$project': {
            '_id': 0, 
            'committee': '$_id.committee', 
            'series': 1,
            'bodysession': bodysession, 
            'section': section,
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
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    outputCollection.aggregate(pipeline, collation={
            'locale': 'en', 
            'numericOrdering': True,
        })

def group_itpmeet(section, bodysession):
    
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
                'committee1': '$committee1', 
                'committee2': '$committee2', 
                'sortkey1': '$sortkey1', 
                'year': '$meetingyear', 
                'symbol': '$symbol'
            }, 
            'meetings': {
                '$push': {
                    'meetingnum': '$meetingnum', 
                    'meetingdate': '$meetingdate'
                }
            }
        }
    }

    sort_stage2 = {
        '$sort': {
            '_id.sortkey1': 1, 
            '_id.year': 1
        }
    }

    group_stage2 = {
        '$group': {
            '_id': {
                'committee1': '$_id.committee1', 
                'committee2': '$_id.committee2', 
                'symbol': '$_id.symbol', 
                'sortkey1': '$_id.sortkey1'
            }, 
            'years': {
                '$push': {
                    'year': '$_id.year', 
                    'meetings': '$meetings'
                }
            }
        }
    }

    sort_stage3 = {
        '$sort': {
            '_id.sortkey1': 1
        }
    }

    project_stage = {
        '$project': {
            '_id': 0, 
            'bodysession': bodysession, 
            'section': section, 
            'committee1': '$_id.committee1', 
            'committee2': '$_id.committee2', 
            'symbol': '$_id.symbol', 
            'years': 1
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
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    outputCollection.aggregate(pipeline, collation={
            'locale': 'en', 
            'numericOrdering': True,
        })

def group_itpage_S(section, bodysession):
    
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
        }
    }

    group_stage = {
        '$group': {
            '_id': '$heading', 
            'agendas': {
                '$push': {
                    'title': '$agendatitle', 
                    'subject': '$agendasubject'
                }
            }
        }
    }

    sort_stage2 = {
        '$sort': {
            '_id': 1
        }
    }

    project_stage = {
        '$project': {
            '_id': 0, 
            'bodysession': bodysession, 
            'section': section,
            'heading': '$_id', 
            'agendas': 1
        }
    }

    merge_stage = {
        '$merge': { 'into': wordOutput}
    }
    
    pipeline.append(match_stage)
    pipeline.append(sort_stage1)
    pipeline.append(group_stage)
    pipeline.append(sort_stage2)
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    outputCollection.aggregate(pipeline)

def group_itpage_AE(section, bodysession):
    
    clear_section(section, bodysession)

    collation={
            'locale': 'en', 
            'numericOrdering': True
        }
    
    pipeline = []

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            'section': section
        }
    }

    sort_stage0 = {
        '$sort': {
            'sortkey1': 1, 
            'sortkey2': 1, 
            'sortkey3': 1
        }
    }

    group_stage1 = {
        '$group': {
            '_id': {
                'a': '$agendanum', 
                'sub': '$subagenda', 
                'title': '$agendatitle', 
                'heading': '$heading'
            }, 
            'see': {
                '$push': '$agendasubject'
            }
        }
    }

    group_stage2 = {
        '$group': {
            '_id': {
                'a': '$_id.a', 
                'sub': '$_id.sub', 
                'h': '$_id.heading'
            }, 
            'titlesubject': {
                '$push': {
                    'title': '$_id.title', 
                    'subjects': '$see'
                }
            }
        }
    }

    sort_stage1 =  {
        '$sort': {
            '_id.a': 1, 
            '_id.sub': 1
        }
    }

    group_stage3 = {
        '$group': {
            '_id': {
                'a': '$_id.a', 
                'h': '$_id.h'
            }, 
            'agendainfo': {
                '$push': {
                    'subagenda': '$_id.sub', 
                    'agendatext': '$titlesubject'
                }
            }
        }
    }

    sort_stage2 = {
        '$sort': {
            '_id': 1
        }
    }

    group_stage4 = {
        '$group': {
            '_id': '$_id.h', 
            'agendas': {
                '$push': {
                    'agendanum': '$_id.a', 
                    'text': '$agendainfo'
                }
            }
        }
    }

    project_stage = {
        '$project': {
            '_id': 0, 
            'bodysession': bodysession, 
            'section': section,
            'heading': '$_id', 
            'agendas': 1
        }
    }

    ##
    sort_stage3 = {
        '$sort': {
            'heading': 1
        }
    }

    merge_stage = {
        '$merge': { 'into': wordOutput}
    }
    
    pipeline.append(match_stage)
    pipeline.append(sort_stage0)
    pipeline.append(group_stage1)
    pipeline.append(group_stage2)
    pipeline.append(sort_stage1)
    pipeline.append(group_stage3)
    pipeline.append(sort_stage2)
    pipeline.append(group_stage4)
    pipeline.append(project_stage)
    pipeline.append(sort_stage3)
    pipeline.append(merge_stage)

    outputCollection.aggregate(pipeline, collation=collation)

def group_itpreps(section, bodysession):
    
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
                'committee': '$committee', 
                'subject': '$subject', 
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
                'committee': '$_id.committee', 
                'sortkey1': '$_id.sortkey1'
            }, 
            'subjects': {
                '$push': {
                    'subject': '$_id.subject', 
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
    
    project_stage = {
        '$project': {
            '_id': 0, 
            'committee': '$_id.committee', 
            'subjects': 1,
            'bodysession': bodysession, 
            'section': section,
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
    pipeline.append(project_stage)
    pipeline.append(merge_stage)

    #print(pipeline)

    outputCollection.aggregate(pipeline, collation={
            'locale': 'en', 
            'numericOrdering': True,
        })


def insert_itpsor(section, bodysession):
    pipeline = []

    match_stage = {
        '$match': {
            'bodysession': bodysession, 
            'section': section
        }
    }

    add_stage = {
        '$addFields': {
            'num': {'$arrayElemAt': [{'$split': ['$sorentry', ' ']}, 1]}
        }
    }

    group_stage = {
        '$group': {
            '_id': 0, 
            'ar': {
                '$addToSet': {
                    '$let': {
                        'vars': {
                            'f': {
                                '$regexFind': {
                                    'input': '$num', 
                                    'regex': '[A-z]'
                                }
                            }
                        }, 
                        'in': {
                            '$cond': {
                                'if': '$$f.idx', 
                                'then': {'$toInt': {'$substrCP': ['$num', 0, '$$f.idx']}}, 
                                'else': {'$toInt': '$num'}
                            }
                        }
                    }
                }
            }
        }
    }

    project_stage = {
        '$project': {
            '_id': 0, 
            'highest': {
                '$max': '$ar'
            }, 
            'ar': 1, 
        }
    }

    pipeline.append(match_stage)
    pipeline.append(add_stage)
    pipeline.append(group_stage)
    pipeline.append(project_stage)

    results = list(outputCollection.aggregate(pipeline))

    ar = results[0]['ar']
    highest = results[0]['highest']

    for i in range(1, highest):
        if i not in ar:
            x = {}
            #print(str(i) + " is not in the set")
            x['bodysession'] = bodysession
            x['docsymbol'] = ""
            x['record_id'] = 0
            x['section'] = section
            x['sorentry'] = "No. " + str(i)
            x['sornorm'] = ""
            x['sornote'] = ""
            x['sortkey1'] = "No. " + str(i)
            x['sortkey2'] = ""

            outputCollection.insert_one(x)
    

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
    filter={
        'lookup_field': 'section', 
        'implemented': 'Y'
    }

    project={
        '_id': 0, 
        'code': 1
    }

    sort=list({
        'code': 1
    }.items())

    return lookupCollection.find(filter=filter, projection=project, sort=sort)

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
