import logging


# General settings
logging.basicConfig(
    format='%(asctime)-15s: %(message)s',
    level=logging.INFO)


# Backend
#from backends.postgresql import PostgresqlBackend
#BACKEND = PostgresqlBackend(host='127.0.0.1', database='ba', user='ba', password='ba')
