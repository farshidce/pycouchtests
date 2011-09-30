from docmaker import DocumentGenerator
import logger
import unittest

class BasicTests(unittest.TestCase):

    def test_make_docs_1(self):
        log = logger.logger("test_make_docs_1")
        docs = DocumentGenerator.make_docs(10,{"name":"employee-${prefix}"})
        for doc in docs:
            log.info(doc)

