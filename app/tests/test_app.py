# assertion methods are documented here https://docs.python.org/3/library/unittest.html#classes-and-functions

from unittest import TestCase

class TestDb(TestCase):
    def test_connection(self):
        self.assertTrue(DB.check_connection())
        
    def test_data(self):
        self.assertGreater(DB.bibs.count,0)
        self.assertGreater(DB.auths.count,0)
    
    
    


