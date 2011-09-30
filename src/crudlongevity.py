import unittest
import uuid
from testconfig import config
from couchdbkit import client
import time
from docmaker import DocumentGenerator
import logger

log = logger.logger("CrudLongevityTests")

class CrudLongevityTests(unittest.TestCase):
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

    def test_crud(self):
        db_name = self._get_db_name()
        self.server.create_db(db_name)
        number_of_items = int(self.params["number_of_items"])
        duration = int(self.params["duration"])
        if duration == -1:
            self.seed = str(uuid.uuid4())
            self._insert_data(number_of_items, db_name)
            self._update_data(number_of_items, db_name)
        else:
            loop_counter = 1
            finish = time.time() + duration
            while time.time() < finish:
                log.info("looping for {0} time".format(loop_counter))
                self.seed = str(uuid.uuid4())
                self._insert_data(number_of_items, db_name)
                self._update_data(number_of_items, db_name)
                loop_counter += 1


    def _insert_data(self, number_of_items, db_name):
        docs = DocumentGenerator.make_docs(number_of_items,
                {"name": "user-${prefix}", "payload": "payload-${prefix}-${padding}"},
                {"size": 1024, "seed": self.seed})
        src_db = self.server[db_name]
        for doc in docs:
            src_db.save_doc(doc)

    def _update_data(self, number_of_items, db_name):
        docs = DocumentGenerator.make_docs(number_of_items,
                {"name": "user-${prefix}", "payload": "updated-payload-${prefix}-${padding}"},
                {"size": 128, "seed": self.seed})
        src_db = self.server[db_name]
        for doc in docs:
            src_db.save_doc(doc, force_update=True)


    def _delete_data(self, docs, db_name):
        src_db = self.server[db_name]
        for doc in docs:
            src_db.delete(doc)