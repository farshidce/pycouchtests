import logging
from logging.handlers import RotatingFileHandler


def logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)

    # create formatter
    formatter = logging.Formatter("[%(asctime)s] - [%(module)s] [%(thread)d] - %(levelname)s - %(message)s")

    max_size = 20 * 1024 * 1024 #max size is 50 megabytes

    filename = "{0}.log".format(name)
    fileHandler = RotatingFileHandler(filename, backupCount=2, maxBytes=max_size)

    # add formatter to ch
    consoleHandler.setFormatter(formatter)
    fileHandler.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(consoleHandler)
#    logger.addHandler(fileHandler)
    return logger