# assertion methods are documented here https://docs.python.org/3/library/unittest.html#classes-and-functions

from unittest import TestCase 
from flask import Flask

class TestInit(TestCase):
    def test_init(self):
        app = Flask('app.py')
        self.assertIsInstance(app,Flask)

class TestDb(TestCase):
    def test_connection(self):
        #self.assertTrue(DB.check_connection())
        pass
        
    def test_data(self):
        #self.assertGreater(DB.bibs.count,0)
        #self.assertGreater(DB.auths.count,0)
        pass