from collections import OrderedDict, defaultdict
from ..utils import Templates


class OperationSet:
    def __init__(self):
        self.sets = {}
        self.pushes = {}
        self.unsets = {}
        self.pulls = {}

    def build_sets(self):
        return {p.path_str(): v for p, v in list(self.sets.items())}

    def build_pushes(self):
        return {p.path_str(): v for p, v in list(self.pushes.items())}

    def build_unsets(self):
        return {p.path_str(): v for p, v in list(self.unsets.items())}

    def build_pulls(self):
        return {p.path_str(): v for p, v in list(self.pulls.items())}


class Path:
    def __init__(self, path):
        self.path = path

    def __eq__(self, other):
        return self.path == other.path

    def path_str(self):
        return Templates.make_path(self.path)

    def __hash__(self):
        return hash('.'.join(map(str, self.path)))


class UpdatesHandler:
    def __init__(self):
        self._updates = defaultdict(OrderedDict)

    def clear(self):
        self._updates.clear()

    def set(self, collection, doc_id, field_path, value):
        operations = self._get_operations(collection, doc_id)
        operations.sets[Path(field_path)] = value

    def push(self, collection, doc_id, field_path, value):
        operations = self._get_operations(collection, doc_id)
        operations.pushes[Path(field_path)] = value

    def unset(self, collection, doc_id, field_path):
        operations = self._get_operations(collection, doc_id)
        operations.unsets[Path(field_path)] = ""

    def pull(self, collection, doc_id, field_path, value):
        operations = self._get_operations(collection, doc_id)
        operations.pulls[Path(field_path)] = value

    def _get_operations(self, collection, doc_id):
        coll_updates = self._updates[collection]

        operations = coll_updates.get(doc_id)

        if not operations:
            operations = OperationSet()
            coll_updates[doc_id] = operations

        return operations

    def build_sentences(self):
        sentences = []

        for collection, coll_updates in list(self._updates.items()):
            for doc_id, operations in list(coll_updates.items()):

                sets = operations.build_sets()

                if len(sets) > 0:
                    sentences.append((collection, doc_id, {'$set': sets}))

                pushes = operations.build_pushes()

                if len(pushes) > 0:
                    sentences.append((collection, doc_id, {'$push': pushes}))

                unsets = operations.build_unsets()

                if len(unsets) > 0:
                    sentences.append((collection, doc_id, {'$unset': unsets}))

                pulls = operations.build_pulls()

                if len(pulls) > 0:
                    sentences.append((collection, doc_id, {'$pull': pulls}))

        return sentences

    def __len__(self):
        return len(self._updates)
