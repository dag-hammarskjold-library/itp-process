# assertion methods are documented here https://docs.python.org/3/library/unittest.html#classes-and-functions

import os
os.environ['FLASK_TEST'] = 'True'

from unittest import TestCase
from copy import deepcopy
from app.config import Config
from app.reports import ReportList
from dlx import DB, Bib, Auth

import mongomock

class Reports(TestCase):
    # Data is committed to in-memory mock database by setting Config.connect_string to "mongomock://localhost"
    # This is copied from MongoEngine to allow the same string to init mock dbs in both DLX and MongoEngine
    
    def setUp(self):
        self.assertEqual(Config.connect_string,'mongomock://localhost')
        self.assertIsInstance(DB.handle,mongomock.database.Database)
        DB.bibs.delete_many({})
        DB.auths.delete_many({})
        
        Auth({'_id': 1}).set('190','b','A/').set('190','c','x').commit()
        Auth({'_id': 2}).set('190','b','A/').set('190','c','xx').commit()
        
    def test_24(self):
        pass
        
    def test_15(self):
        # https://unitednations.sharepoint.com/:x:/r/sites/dpi_od_dhl_iss/_layouts/15/Doc.aspx?sourcedoc=%7B84C697DA-C819-4884-9ADF-02078441EDE3%7D&file=REV-Validation%20Report%20Criteria.xlsx&action=default&mobileredirect=true
        report = ReportList.get_by_name('bib_incorrect_793_committees')
        
        bib = Bib({'_id': 1})
        bib.set('191','a','A/C.6/GOOD').set('191','b',1).set('191','c',1)
        bib.set('930','a','UND').set('793','a','06')
        bib.commit()
        
        bib = Bib({'_id': 2})
        bib.set('191','a','A/C.2/BAD').set('191','b',1).set('191','c',1)
        bib.set('930','a','UND').set('793','a','WRONG')
        bib.commit()
        
        bib = Bib({'_id': 3})
        bib.set('191','a','A/C.9/GOOD').set('191','b',2).set('191','c',2)
        bib.set('930','a','UND').set('793','a','09')
        bib.commit()
        
        args = {}
        
        args['authority'] = 1
        results = report.execute(args)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0][0],'A/C.2/BAD')
        
        args['authority'] = 2
        results = report.execute(args)
        self.assertEqual(len(results),0)  
        
    def test_16(self):
       print(list(Bib.match_value('191','a','A/C.6/GOOD')))
       #pass
        
    ### speech
    
    ### vote
    
    