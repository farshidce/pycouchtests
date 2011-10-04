import unittest
import uuid
from couchdbkit.exceptions import ResourceConflict
from nose import tools
from nose.case import Test
from testconfig import config
from couchdbkit import client
import time
from docmaker import DocumentGenerator
import logger

log = logger.logger("CrudLongevityTests")

class AttachmentTests(unittest.TestCase):
    cleanup_dbs = []

    def setUp(self):
        self.node = config['couchdb-local']
        self.params = config["test-params"]
        self.log = log
        url = "http://{0}:{1}/".format(self.node['ip'], self.node['port'])
        self.log.info("connecting to couchdb @ {0}".format(url))
        self.server = client.Server(url, full_commit=False)

    def tearDown(self):
        nodes = [config["couchdb-local"]]
        urls = ["http://{0}:{1}/".format(n['ip'], n['port']) for n in nodes]
        servers = [client.Server(url, full_commit=False) for url in urls]
        for server in servers:
            for db in server:
                if db.dbname.find("test_suite") != -1 or db.dbname.find(
                    "doctest") != -1 or db.dbname in self.cleanup_dbs:
                    try:
                        server.delete_db(db.dbname)
                        pass
                    except Exception as ex:
                        print ex
                        pass
        self.cleanup_dbs = []

    def _get_db_name(self):
        name = "doctests-{0}".format(str(uuid.uuid4())[:6])
        log.info(name)
        self.cleanup_dbs.append(name)
        return name

    #ATTCH001 : save a document with a text/plain attachment where data is also a plain string
    def test_attach001(self):
        log.info("ATTCH001 : save a document with a text/plain attachment where data is also a plain string")
        src_db, docs = self._get_db_and_generated_docs()
        self._set_and_verify_attachment(docs, u"a random text attachment", "text/plain", "test_attach001")

    #ATTCH002: save a document with text/plain attachment where data is an empty string
    def test_attach002(self):
        log.info("ATTCH002: save a document with text/plain attachment where data is an empty string")
        src_db, docs = self._get_db_and_generated_docs()
        self._set_and_verify_attachment(docs, "", "text/plain", "test_attach002")

    #ATTCH003: add a new attachment to a document which already has an attachment
    def test_attach003(self):
        log.info("ATTCH003: add a new attachment to a document which already has an attachment")
        src_db, docs = self._get_db_and_generated_docs()
        for doc in docs:
            src_db.save_doc(doc)
            text_attachment = u"a random text attachment-1-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach003-1", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach001-1')
            tools.eq_(file, text_attachment)
            text_attachment = u"a random text attachment-2-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach003-2", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach003-2')
            tools.eq_(file, text_attachment)

    #ATTCH004: overwrite the existing attachment with a new value
    def test_attach004(self):
        log.info("ATTCH003: add a new attachment to a document which already has an attachment")
        src_db, docs = self._get_db_and_generated_docs()

        for doc in docs:
            src_db.save_doc(doc)
            text_attachment = u"a random text attachment-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach001", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach001')
            tools.eq_(file, text_attachment)
            text_attachment = u"overwritten - a random text attachment-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach001", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach001')
            tools.eq_(file, text_attachment)

    #ATTCH005- add a new attachment to a document with content as text/plain;charset=utf-8
    def test_attach005(self):
        log.info("ATTCH001 : save a document with a text/plain attachment where data is also a plain string")
        src_db, docs = self._get_db_and_generated_docs()
        self._set_and_verify_attachment(docs, u"a random text attachment", "text/plain;charset=utf-8", "test_attach005")


    #ATTCH006: delete an attachment without specifying a revision ( should fail)
    def test_attach006(self):
        log.info("ATTCH006: delete an attachment without specifying a revision ( should fail)")
        src_db, docs = self._get_db_and_generated_docs()
        for doc in docs:
            src_db.save_doc(doc)
            text_attachment = u"a random text attachment-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach006", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach006')
            tools.eq_(file, text_attachment)
            doc["_rev"] = None
            try:
                src_db.delete_attachment(doc, "attach-006")
                assert "couchdb did not raise ResourceConflict"
            except ResourceConflict as rc:
                pass

    #ATTCH007: delete an attachment by specifying the right revision
    def test_attach007(self):
        log.info("ATTCH007: delete an attachment by specifying the right revision")
        src_db, docs = self._get_db_and_generated_docs()
        for doc in docs:
            src_db.save_doc(doc)
            text_attachment = u"a random text attachment-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach007", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach007')
            tools.eq_(file, text_attachment)
            src_db.delete_attachment(doc, "attach-007")

    #ATTCH008 : from a document with two attachments delete only one attachment
    def test_attach008(self):
        log.info("#ATTCH008 : from a document with two attachments delete only one attachment")
        src_db, docs = self._get_db_and_generated_docs()
        for doc in docs:
            src_db.save_doc(doc)
            text_attachment = u"a random text attachment-1-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach008-1", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach008-1')
            tools.eq_(file, text_attachment)
            text_attachment = u"a random text attachment-2-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach008-2", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach008-2')
            tools.eq_(file, text_attachment)
            src_db.delete_attachment(doc, "attach008-2")
            #verify that the first attachment is still valid
            text_attachment = u"a random text attachment-1-{0}".format(doc["_id"])
            src_db.put_attachment(doc, text_attachment, "attach008-1", "text/plain")
            file = src_db.fetch_attachment(doc, 'attach008-1')
            tools.eq_(file, text_attachment)


    def _get_db_and_generated_docs(self):
        db_name = self._get_db_name()
        self.server.create_db(db_name)
        src_db = self.server[db_name]
        number_of_items = 100
        docs = DocumentGenerator.make_docs(number_of_items,
                {"name": "user-${prefix}", "payload": "payload-${prefix}-${padding}"},
                {"size": 1024, "seed": str(uuid.uuid4())})
        return src_db, docs

    def _set_and_verify_attachment(self, docs, attachment_base_string, content_type, attachment_name):
        for doc in docs:
            src_db.save_doc(doc)
            text_attachment = attachment_base_string
            if attachment_base_string != "":
                text_attachment = u"{0}-{1}".format(attachment_base_string, doc["_id"])
            src_db.put_attachment(doc, text_attachment, attachment_name, content_type)
            file = src_db.fetch_attachment(doc, attachment_name)
            tools.eq_(file, text_attachment)
