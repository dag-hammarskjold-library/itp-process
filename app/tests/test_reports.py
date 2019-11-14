# assertion methods are documented here https://docs.python.org/3/library/unittest.html#classes-and-functions

from unittest import TestCase
from app.config import Config
Config.connect_string = "mongomock://localhost"
from app.reports import ReportList
from dlx import DB, Bib, Auth

class Reports(TestCase):
    # Data is committed to in-memory mock database by setting Config.connect_string to "mongomock://localhost"
    # This is copied from MongoEngine to allow the same string to init mock dbs in both DLX and MongoEngine
    
    def setUp(self):
        print(Config.connect_string)
        print(DB.handle)
        
    def test_24(self):
        pass
        
    def test_15(self):
        # https://unitednations.sharepoint.com/:x:/r/sites/dpi_od_dhl_iss/_layouts/15/Doc.aspx?sourcedoc=%7B84C697DA-C819-4884-9ADF-02078441EDE3%7D&file=REV-Validation%20Report%20Criteria.xlsx&action=default&mobileredirect=true
        report = ReportList.get_by_name('bib_incorrect_793_committees')
        
        Auth({'_id': 1}).set('190','b','A/').set('190','c','100').commit()
        Auth({'_id': 2}).set('190','b','A/').set('190','c','200').commit()
        
        Bib({'_id': 1}) \
            .set('191','a','A/C.6/GOOD') \
            .set('191','b',1) \
            .set('191','c',1) \
            .set('930','a','UND') \
            .set('793','a','06') \
            .commit()
    
        Bib({'_id': 2}) \
            .set('191','a','A/C.2/BAD') \
            .set('191','b',1) \
            .set('191','c',1) \
            .set('930','a','UND') \
            .set('793','a','00') \
            .commit()

        args = {}
        
        args['authority'] = 1
        results = report.execute(args)
        self.assertEqual(len(results),1)
        self.assertEqual(results[0][0],'A/C.2/BAD')
        
    def test_16(self):
       #print(list(Bib.match_value('191','a','A/C.6/GOOD')))
       pass
        
    ### speech
    
    ### vote