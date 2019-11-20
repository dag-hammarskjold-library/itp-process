from dlx import DB, Bib, Auth
from mongoengine import connect
import boto3
import os, re

'''
This is your application configuration file. Use it to set your various configurations,
but DO NOT put credentials in this file because this file may be checked in to a public
repository.

Acceptable means of storing/accessing credentials:
  - AWS Parameter Store, e.g.:

        import boto3
        client = boto3.client('ssm')
        username = client.get_parameter(Name='username')['Parameter']['Value']
        password = client.get_parameter(Name='password')['Parameter']['Value']

    Obviously you need to have the desired parameters already stored in Parameter Store, and you
    should have the awscli installed and configured with a key id and secret key supplied by AWS 
    or your AWS administrator.

  - Environment variables:

        import os
        username = os.environ.get('username')
        password = os.environ.get('password')

Note that if you use environment variables and plan to incorporate a CI/CD pipeline, e.g., with 
Travis CI, you will need to make sure your CI environment has the appropriate variables defined
and stored.
'''

class ProductionConfig(object):
    context = 'production'
    client = boto3.client('ssm')
    connect_string = client.get_parameter(Name='connect-string')['Parameter']['Value']
    dbname = client.get_parameter(Name='dbname')['Parameter']['Value']
    collection_prefix = ''
    RPP = 10
    
class DevelopmentConfig(ProductionConfig):
    # Provide overrides for production settings here.
    context='development'
    collection_prefix = 'dev_'
    DEBUG = True

class TestConfig(ProductionConfig):
    context = 'test'
    DEBUG = True
    collection_prefix = ''
    connect_string = 'mongomock://localhost'
    
def get_config():
    if 'FLASK_TEST' in os.environ:
        return TestConfig

    flask_env = os.environ.setdefault('FLASK_ENV', 'development')
    
    if flask_env == 'production':
        return ProductionConfig
    elif flask_env == 'development':
        return DevelopmentConfig
    else:
        raise Exception('Environment variable "FLASK_ENV" set to invalid value "{}"'.format(flask_env))

Config = get_config()