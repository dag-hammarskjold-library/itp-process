# assertion methods are documented here https://docs.python.org/3/library/unittest.html#classes-and-functions

import os
os.environ['FLASK_TEST'] = 'True'

from unittest import TestCase
from copy import deepcopy
from app.reports import ReportList
from dlx import DB
from dlx.marc import Bib, Auth
from mongomock.database import Database as MockDB 

class Reports(TestCase):
    # Data is committed to in-memory mock database by setting Config.connect_string to "mongomock://localhost".
    # DLX and MongoEngine both use this string to connect to a mock DB.
    
    def setUp(self):
        # runs before every test method
         
        # an abundance of caution
        #self.assertEqual(get_config.connect_string,'mongomock://localhost')
        self.assertIsInstance(DB.client, MockDB)
        
        # clear the db
        DB.bibs.delete_many({})
        DB.auths.delete_many({})
        
        # mock auths
        # all xrefs in the mock bibs must point to an auth in the mock db to work properly
        Auth({'_id': 1}).set('190','b','A/').set('190','c','SESSION_1').commit()
        Auth({'_id': 2}).set('190','b','A/').set('190','c','SESSION_2').commit()
        Auth({'_id': 3}).set('191','d','AGENDA SUBJECT').commit()
        
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
        args = {}
        args['authority'] = 1
        
        for tag in ('793','991','992'):
            report = ReportList.get_by_name('bib_missing_' + tag)
            
            Bib({'_id': 1}).set_values(
                ('191','a','GOOD'),
                ('191','b',1),
                ('191','c',1),
                ('930','a','UND'),
                (tag,'a',3)
            ).commit()
            
            Bib({'_id': 2}).set_values(
                ('191','a','BAD'),
                ('191','b',1),
                ('191','c',1),
                ('930','a','UND')
            ).commit()
            
            results = report.execute(args)
            self.assertEqual(results[0][2],'BAD')
    
    # missing subfield - bib
    def test_7a_12a(self):
        args = {}
        args['authority'] = 1
        
        for t in [('191','9'),('991','d')]:
            tag,code = t[0],t[1]
            report = ReportList.get_by_name('bib_missing_' + tag + code)
            
            Bib({'_id': 1}).set_values(
                ('001',None,'2'),
                ('191','a','GOOD'),
                ('191','b',1),
                ('191','c',1),
                ('930','a','UND'),
                (tag,code,3)
            ).commit()
            
            Bib({'_id': 2}).set_values(
                ('001',None,'2'),
                ('191','a','BAD'),
                ('191','b',1),
                ('191','c',1),
                ('930','a','UND'),
                (tag,'z','WRONG')
            ).commit()
            
            Bib({'_id': 3}).set_values(
                ('001',None,'3'),
                ('191','a','GOOD'),
                ('191','b',1),
                ('191','c',1),
                ('930','a','UND')
            ).commit()

            results = report.execute(args)
            expected = 2 if tag == '191' else 1
            self.assertEqual(len(results),expected)
            
    # missing subfield value - bib
    def test_1_2_13(self):
        pass

    ### speech
    
    # Duplicate speech records
    def test_25(self):
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
        args = {}
        args['authority'] = 1
        
        for tag in ('039','856','991','992'):
            report = ReportList.get_by_name('speech_missing_' + tag)
            
            Bib({'_id': 1}).set_values(
                ('791','a','GOOD'),
                ('791','b',1),
                ('791','c',1),
                ('930','a','ITS'),
                (tag,'a','x')
            ).commit()
            
            Bib({'_id': 2}).set_values(
                ('791','a','BAD'),
                ('791','b',1),
                ('791','c',1),
                ('930','a','ITS')
            ).commit()
            
            results = report.execute(args)
            self.assertEqual(results[0][2],'BAD')
    
    # missing subfield - speech
    def test_12b(self):
        args = {}
        args['authority'] = 1
        tag,code = '991','d'
        report = ReportList.get_by_name('speech_missing_' + tag + code)
        
        Bib({'_id': 1}).set_values(
            ('791','a','GOOD'),
            ('791','b',1),
            ('791','c',1),
            ('930','a','ITS'),
            (tag,code,3)
        ).commit()
        
        Bib({'_id': 2}).set_values(
            ('001',None,'2'),
            ('791','a','BAD'),
            ('791','b',1),
            ('791','c',1),
            ('930','a','ITS'),
            (tag,'z','WRONG')
        ).commit()
        
        Bib({'_id': 3}).set_values(
            ('791','a','GOOD'),
            ('791','b',1),
            ('791','c',1),
            ('930','a','ITS')
        ).commit()

        results = report.execute(args)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0],['ITS','2','BAD'])
        
    ### vote
    
    # Field mismatch - 269 & 992 - vote
    def test_23b(self):
        pass
    
    # Incorrect field - vote
    def test_11_22(self):
        pass
        
    # incorrect session - vote
    def test_6(self):
        '''
        authority ID for the body/session;
        930$a starts with "VOT";
        
        If 791 $a starts with:
        
        A/72 => 791 $r should also start with A72
        
        S/RES/(year)
        
        E/2018 => 791 $r should also start with E2018
        '''
        
        Bib({'_id': 1}).set_values(
            ('791','a','A/RES/72/GOOD'),
            ('791','b',1),
            ('791','c',1),
            ('791','r','A72'),
            ('930','a','VOT'),
        ).commit()
        
        Bib({'_id': 2}).set_values(
            ('791','a','A/RES/72/BAD'),
            ('791','b',1),
            ('791','c',1),
            ('791','r','A1'),
            ('930','a','VOT')
        ).commit()
        
        report = ReportList.get_by_name('vote_incorrect_session')
        results = report.execute({'authority': 1})
        self.assertEqual(len(results),1)
        self.assertEqual(results[0][1],'A/RES/72/BAD')
        
        Bib({'_id': 1}).set_values(
            ('791','a','S/RES/1999/BAD'),
            ('791','b',1),
            ('791','c',1),
            ('791','r','S1900'),
            ('930','a','VOT'),
        ).commit()
        
        Bib({'_id': 2}).set_values(
            ('791','a','S/RES/1999/GOOD'),
            ('791','b',1),
            ('791','c',1),
            ('791','r','S1999'),
            ('930','a','VOT')
        ).commit()
        
        report = ReportList.get_by_name('vote_incorrect_session')
        results = report.execute({'authority': 1})
        self.assertEqual(len(results),1)
        self.assertEqual(results[0][1],'S/RES/1999/BAD')
        
        Bib({'_id': 1}).set_values(
            ('791','a','E/RES/2012/GOOD'),
            ('791','b',1),
            ('791','c',1),
            ('791','r','E2012'),
            ('930','a','VOT'),
        ).commit()
        
        Bib({'_id': 2}).set_values(
            ('791','a','E/RES/1970/BAD'),
            ('791','b',1),
            ('791','c',1),
            ('791','r','E1969'),
            ('930','a','VOT')
        ).commit()
        
        report = ReportList.get_by_name('vote_incorrect_session')
        results = report.execute({'authority': 1})
        self.assertEqual(len(results),1)
        self.assertEqual(results[0][1],'E/RES/1970/BAD')
        
    
    # missing field - vote
    def test_12c_17b_18b_20b(self):
        args = {}
        args['authority'] = 1
        
        for tag in ('039','856','991','992'):
            report = ReportList.get_by_name('vote_missing_' + tag)
            
            Bib({'_id': 1}).set_values(
                ('791','a','GOOD'),
                ('791','b',1),
                ('791','c',1),
                ('930','a','VOT'),
                (tag,'a','x')
            ).commit()
            
            Bib({'_id': 2}).set_values(
                ('791','a','BAD'),
                ('791','b',1),
                ('791','c',1),
                ('930','a','VOT')
            ).commit()
            
            results = report.execute(args)
            self.assertEqual(results[0][2],'BAD')
        
    # Missing subfield - vote
    def test_12c(self):
        args = {}
        args['authority'] = 1
        tag,code = '991','d'
        report = ReportList.get_by_name('vote_missing_' + tag + code)
        
        Bib({'_id': 1}).set_values(
            ('791','a','GOOD'),
            ('791','b',1),
            ('791','c',1),
            ('930','a','VOT'),
            (tag,code,3)
        ).commit()
        
        Bib({'_id': 2}).set_values(
            ('791','a','BAD'),
            ('791','b',1),
            ('791','c',1),
            ('930','a','VOT'),
            (tag,'z','WRONG')
        ).commit()
        
        Bib({'_id': 3}).set_values(
            ('791','a','GOOD'),
            ('791','b',1),
            ('791','c',1),
            ('930','a','VOT')
        ).commit()

        results = report.execute(args)
        self.assertEqual(len(results),1)

    ### other
    
    # missing 930 - all
    def test_3_19a_19b(self):
        pass

    