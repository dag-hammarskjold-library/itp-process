# assertion methods are documented here https://docs.python.org/3/library/unittest.html#classes-and-functions

from unittest import TestCase 
from flask import Flask

class TestInit(TestCase):
    def test_init(self):
        app = Flask('app.py')
        self.assertIsInstance(app,Flask)
