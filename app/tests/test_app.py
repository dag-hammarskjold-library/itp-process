# assertion methods are documented here https://docs.python.org/3/library/unittest.html#classes-and-functions

from unittest import TestCase 
from flask import Flask

from app.app import app

# prints list of routes
#for rule in app.url_map.iter_rules(): print(rule)

class Init(TestCase):
    def test_init(self):
        self.assertIsInstance(app,Flask)

class Routes(TestCase):
    client = app.test_client()
    
    def test_root(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code,200)
       
    def test_login(self):
        r = self.client.get('/login')
        self.assertEqual(r.status_code,200)
       
    def test_reports(self):
        r = self.client.get('/reports/missing_field')
        self.assertEqual(r.status_code,200)
        
        #r = self.client.get('/reports/missing_field')
        #self.assertEqual(r.status_code,200)
        