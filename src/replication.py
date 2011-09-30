import copy
import unittest
from nose import tools
import uuid
from testconfig import config
from couchdbkit import client
import time
from docmaker import DocumentGenerator
import logger

log = logger.logger("ReplicationTests")

class ReplicationTests(unittest.TestCase):
    cleanup_dbs = []

    def setUp(self):
        self.node = config['couchdb-local']
        self.log = log
        url = "http://{0}:{1}/".format(self.node['ip'], self.node['port'])
        self.log.info("connecting to couchdb @ {0}".format(url))
        self.server = client.Server(url, full_commit=False)

    def tearDown(self):
        nodes = [config["couchdb-local"], config["couchdb-remote-1"], config["couchdb-remote-2"]]
        urls = ["http://{0}:{1}/".format(n['ip'], n['port']) for n in nodes]
        servers = [client.Server(url, full_commit=False) for url in urls]
        for server in servers:
            for db in server:
                if db.dbname.find("doctest") != -1 or db.dbname in self.cleanup_dbs:
                    try:
#                        server.delete_db(db.dbname)
                        pass
                    except Exception as ex:
                        print ex
                        pass
        self.cleanup_dbs = []

    def _get_db_name(self, postfix=""):
        name = "doctests-{0}-{1}".format(str(uuid.uuid4())[:6], postfix)
        self.cleanup_dbs.append(name)
        return name

    def test_simple_replication_10k_docs_remote_db(self):
        destination = config['couchdb-remote-1']
        self._replication(4000, "simple", destination, 102400)

    def test_filtered_replication_10k_docs_remote_db(self):
        destination = config['couchdb-remote-1']
        self._replication(4000, "filtered", destination, 102400)


    def _replication(self, items, replication_type, destination, doc_size):
        src_db_name = self._get_db_name(replication_type)
        self.server.create_db(src_db_name)
        dst_db_name = self._get_db_name(replication_type)
        url = "http://{0}:{1}/".format(destination['ip'], destination['port'])
        self.dst_server = client.Server(url, full_commit=False)
        self.dst_server.create_db(dst_db_name)
        description = "insert {0} items in source database.start replication from {1}(db:{2}) to {3}(db:{4})"
        self.log.info(description.format(items, config["couchdb-local"]["ip"],
                                         src_db_name, destination["ip"], dst_db_name))
        docs = DocumentGenerator.make_docs(items, {"name": "user-${prefix}", "payload": "payload-${prefix}-${padding}"},
                {"size": doc_size})
        src_db = self.server[src_db_name]
        for doc in docs:
            src_db.save_doc(doc)
        self.log.info("saved {0} docs".format(len(docs)))
        source = "http://{0}:{1}/{2}".format(self.node["ip"], self.node["port"], src_db_name)
        destination = "http://{0}:{1}/{2}".format(destination["ip"], destination["port"], dst_db_name)
        self.log.info("starting the replication")
        filter_fn = '''function(doc) { if(doc.name != null) { return true; } else { return false; }  }'''
        design_doc = {"_id": "_design/simple_filter", "filters": {"all_docs_filter": filter_fn}}
        self.server[src_db_name].save_doc(design_doc)
        replication_task_id = ""
        if replication_type == "filtered":
            data = self.server.replicate(source, destination, filter="simple_filter/all_docs_filter", continuous=True)
            self.log.info(data)
            if data and "_local_id" in data:
                replication_task_id = data["_local_id"]
                self._wait_for_replication(self.server, replication_task_id, 120)
                self.server.replicate(source, destination, filter="simple_filter/all_docs_filter", continuous=True,
                                      cancel=True)

        else:
            data = self.server.replicate(source, destination, continuous=True)
            self.log.info(data)
            if data and "_local_id" in data:
                replication_task_id = data["_local_id"]
                self._wait_for_replication(self.server, replication_task_id, 120)
            data = self.server.replicate(source, destination, continuous=True, cancel=True)

            #now let's cancel the replication
        self.log.info("replication completed")

        #verify that all the data is replicated
        tools.ok_(self._verify_replication(self.server, src_db_name, self.dst_server, dst_db_name, docs),
                  msg="replication did not replicate some items")


    def _verify_replication(self, src_server, src_db, dst_server, dst_db, docs):
        for doc in docs:
            id = doc["_id"]
            src_fetched = src_server[src_db].get(id)
            try:
                dst_fetched = dst_server[dst_db].get(id)
            except Exception:
                self.log.info("document {0} still not replicated".format(id))
                return False
            equal = self._compare_object_one_level(src_fetched, dst_fetched)
            if not equal:
                self.log.info("{0} != {1}".format(src_fetched, dst_fetched))
                return False
        return True


    # does a one level comparison
    def _compare_object_one_level(self, obj1, obj2):
        for k in obj1:
            if k in obj2:
                if obj1[k] != obj2[k]:
                    return False
            else:
                return False

        for k in obj2:
            if k in obj1:
                if obj2[k] != obj1[k]:
                    return False
            else:
                return False
        return True


#    def test_update_10k_docs(self):
#        description = "insert 10k items in source database." +\
#                      "start replication and then update those items.replicate again"
#
#
#    def test_delete_10k_docs(self):
#        description = "insert 20k items in source database." +\
#                      "start replication and then delete 10k items.replicate again"
#        self.log.info(description)
#
#
#    def test_add_10k_docs(self):
#        description = "insert 10k items in source database" +\
#                      "start replication and then add 10k new items.replicate again"
#        self.log.info(description)

    def _wait_for_replication(self, server, replication_task_id, timeout):
        task_found = False
        last_reported_values = []
        start = time.time()
        while (time.time() - start) < timeout:
            tasks = server.active_tasks()
            for task in tasks:
                if "task" in task:
                    task_id = task["task"]
                    if task_id.find(replication_task_id) != -1:
                        values = task["status"].replace("Processed ", "").replace(" changes", "").split("/")
                        if last_reported_values:
                            if last_reported_values[0] == values[0] and last_reported_values[1] == values[1] and (
                            int(values[1]) - int(values[0]) < 10):
                                self.log.info("replication took {0} seconds".format(time.time() - start))
                                return True
                        last_reported_values = copy.deepcopy(values)
                        self.log.info("processed {0} changes out of {1} changes".format(values[0], values[1]))
                        if int(values[0]) == int(values[1]):
                            self.log.info("replication took {0} seconds".format(time.time() - start))
                            return True
                        task_found = True
                        time.sleep(2)
            if not task_found:
                raise Exception("task {0} is not running".format(replication_task_id))
        raise Exception(
            "replication task {0} did not complete after waiting for {1} seconds".format(replication_task_id, timeout))

