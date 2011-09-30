import os
import random
import string
import uuid

class DocumentGenerator(object):
    #will loop over all values in props and replace ${prefix} with ${i}
    @staticmethod
    def make_docs(items, kv_template, options=dict(size=1024, seed=str(uuid.uuid4()))):
        return GeneratedDocuments(items, kv_template, options)

    @staticmethod
    def _random_string(length):
        return (("%%0%dX" % (length * 2)) % random.getrandbits(length * 8)).decode("hex")

    @staticmethod
    def create_value(pattern, size):
        return (pattern * (size / len(pattern))) + pattern[0:(size % len(pattern))]


class GeneratedDocuments(object):
    def __init__(self, items, kv_template, options=dict(size=1024)):
        self._items = items
        self._kv_template = kv_template
        self._options = options
        self._pointer = 0
        self._pad = DocumentGenerator.create_value("*", options["size"])

    # Required for the for-in syntax
    def __iter__(self):
        return self

    def __len__(self):
        return self._items

    # Returns the next value of the iterator
    def next(self):
        if self._pointer == self._items:
            raise StopIteration
        else:
            i = self._pointer
            doc = {"_id": "{0}".format(i)}
            for k in self._kv_template:
                v = self._kv_template[k]
                if isinstance(v, str) and v.find("${prefix}") != -1:
                    v = v.replace("${prefix}", "{0}".format(i))
                    #how about the value size
                if isinstance(v, str) and v.find("${padding}") != -1:
                    v = v.replace("${padding}", self._pad)
                doc[k] = v
        self._pointer += 1
        return doc