# assertion methods are documented here https://docs.python.org/3/library/unittest.html#classes-and-functions

import os
os.environ['FLASK_TEST'] = 'True'

from unittest import TestCase
from copy import deepcopy
from app.config import Config
from app.reports import ReportList
from dlx import DB, Bib, Auth
from mongomock.database import Database as MockDB 

class Reports(TestCase):
    # Data is committed to in-memory mock database by setting Config.connect_string to "mongomock://localhost".
    # DLX and MongoEngine both use this string to connect to a mock DB.
    
    def setUp(self):
        # runs before every test method
         
        # an abundance of caution
        self.assertEqual(Config.connect_string,'mongomock://localhost')
        self.assertIsInstance(DB.handle,MockDB)
        
        # clear the db
        DB.bibs.delete_many({})
        DB.auths.delete_many({})
        
        # mock session auths
        Auth({'_id': 1}).set('190','b','A/').set('190','c','SESSION_1').commit()
        Auth({'_id': 2}).set('190','b','A/').set('190','c','SESSION_2').commit()
        
    ### bib
    
    # Agenda List    
    def test_24(self):
        pass
    
    # Incorrect field - 793 (Committees)
    def test_15(self):
        report = ReportList.get_by_name('bib_incorrect_793_committees')
        
        Bib({'_id': 1}).set_values(
            ('191','a','A/C.6/GOOD'),
            ('191','b',1),
            ('191','c',1),
            ('930','a','UND'),
            ('793','a','06')
        ).commit()
        
        Bib({'_id': 2}).set_values(
            ('191','a','A/C.2/BAD'),
            ('191','b',1),
            ('191','c',1),
            ('930','a','UND'),
            ('793','a','WRONG')
        ).commit()
        
        Bib({'_id': 3}).set_values(
            ('191','a','A/C.9/GOOD'),
            ('191','b',1),
            ('191','c',1),
            ('930','a','UND'),
            ('793','a','09')
        ).commit()
        
        args = {}
        
        args['authority'] = 1
        results = report.execute(args)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0][0],'A/C.2/BAD')

        args['authority'] = 2
        results = report.execute(args)
        self.assertEqual(len(results),0)  
    
    # Incorrect field - 793 (Plenary)
    def test_14b(self):
        report = ReportList.get_by_name('bib_incorrect_793_plenary')
        
        Bib({'_id': 1}).set_values(
            ('191','a','A/RES/GOOD'),
            ('191','b',1),
            ('191','c',1),
            ('930','a','UND'),
            ('793','a','PL')
        ).commit()
        
        Bib({'_id': 2}).set_values(
            ('191','a','A/SESSION_1/L.GOOD'),
            ('191','b',1),
            ('191','c',1),
            ('930','a','UND'),
            ('793','a','PL')
        ).commit()

        Bib({'_id': 3}).set_values(
            ('191','a','A/RES/BAD'),
            ('191','b',1),
            ('191','c',1),
            ('930','a','UND'),
            ('793','a','WRONG')
        ).commit()
        
        Bib({'_id': 4}).set_values(
            ('191','a','A/SESSION_1/L.BAD'),
            ('191','b',1),
            ('191','c',1),
            ('930','a','UND'),
            ('793','a','WRONG')
        ).commit()
        
        args = {}
        
        args['authority'] = 1
        results = report.execute(args)
        self.assertEqual(len(results),2)
        self.assertEqual(results[0][0],'A/RES/BAD')
        self.assertEqual(results[1][0],'A/SESSION_1/L.BAD')
        
        
    # incorrect field - bib
    def test_9(self):
        pass
        
    # incorrect session - bib
    def test_4(self):
        pass
    
    # incorrect subfield - bib
    def test_7b(self):
        pass
   
    # missing field - bib
    def test_8a_14a_16(self):
        pass
    
    # missing subfield - bib
    def test_7a_12a(self):
        pass
      
    # missing subfield value - bib
    def test_1_2_13(self):
        pass

    ### speech
    
    # Duplicate speech records
    def test25(self):
        pass
    
    # Field mismatch - 269 & 992 - speech
    def test_23a(self):
        pass
    
    # Incomplete authorities - speech
    def test_26(self):
        pass
    
    # Incorrect field 
    def test_10_21(self):
        pass
        
    # incorrect session - speech
    def test_5(self):
        pass
        
    # missing field - speech
    def test_8b_17a_18a_20a(self):
        pass
    
    # missing subfield - speech
    def test_12b(self):
        pass
        
    ### vote
    
    # Field mismatch - 269 & 992 - vote
    def test_23b(self):
        pass
    
    # Incorrect field - vote
    def test_11_22(self):
        pass
        
    # incorrect session - vote
    def test_6(self):
        pass
    
    # missing field - vote
    def test_12c_17b_18b_20b(self):
        pass
        
    # Missing subfield - 991$d
    def test_12c(self):
        pass

    ### other
    
    # missing 930 - all
    def test_3_19a_19b(self):
        pass
        
# util

class SetBib(Bib):
    def __init__(self,doc):
        super().__init__(doc)
    
    def set_vals(self,*tuples):
        for t in tuples:
            tag,sub,val = t[0],t[1],t[2]
            self.set(tag,sub,val)
    