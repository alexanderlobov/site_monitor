import logging

def config_log(level):
    logging.basicConfig(
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        level=level.upper())
