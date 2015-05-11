# logging test
import logging

logging.basicConfig(filename='example.log', format=50*'='+'\n%(asctime)s %(message)s', level=logging.DEBUG)
try:
    1 / 0
except Exception, e:
    logging.exception(e)
    raise