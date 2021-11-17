import dataclasses
import ling.db_model as db
import ling.ling as ling
import ling.sent_wdg as sent_wdg
from typing import List


class AppCtx:
    """
    Acts as an interface to DB, linking db functionality with other application parts
    by providing high-level interface to DB api
    """
    _instance = None

    def __init__(self):
        self.db = db.DBCtx()

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init__()
        return cls._instance

    # @NOTE(hl): Put helper methods for accessing db here to keep db api clear
    def get_collocations_from_ids(self, ids: List[db.CollocationID]) -> List[db.Collocation]:
        db_collocations = [self.db.get_collocation(col_id) for col_id in ids]
        return db_collocations

    def get_connections_from_ids(self, ids: List[db.ConnID]) -> List[db.Connection]:
        db_collocations = [self.db.get_connection(col_id) for col_id in ids]
        return db_collocations

    def get_words_from_ids(self, ids: List[db.WordID]) -> List[db.Word]:
        db_words = [self.db.get_word(id_) for id_ in ids]
        return db_words

    def create_sent_ctx_from_db(self, id_: db.SentenceID) -> ling.SentenceCtx:
        sentence = self.db.get_sentence(id_)
        db_collocations = self.get_collocations_from_ids(sentence.collocations)
        db_connections = self.get_connections_from_ids(sentence.connections)

        sent_ctx = ling.SentenceCtx()
        # @NOTE(hl): Cause we're lazy to do proper initialization with words
        sent_ctx.init_from_text(sentence.contents)

        ling_collocations = []
        for db_col in db_collocations:
            col_words = [self.db.get_word(word_id) for word_id in db_col.words]
            word_idxs = [sent_ctx.word_idx(word.word) for word in col_words]
            ling_col = ling.Collocation(word_idxs, ling.SemanticGroup(db_col.semantic_group_id))
            ling_collocations.append(ling_col)

        sent_ctx.collocations = ling_collocations

        ling_connections = []
        for db_con in db_connections:
            obj = sentence.collocations.index(db_con.object_)
            pred = sentence.collocations.index(db_con.predicate)
            ling_con = (obj, pred)
            ling_connections.append(ling_con)

        sent_ctx.connections = ling_connections
        return sent_ctx

    def get_initial_form(self, word: db.Word) -> db.Word:
        # @NOTE(hl): Wrapper for conditional
        # @TODO(hl): It may be beneficial to always store initial_form_id and detect it is the initial form by comparing
        #  ids?
        return self.db.get_word(word.initial_form_id) if word.initial_form_id is not None else word

    def get_words_of_sem_group(self, sg: db.SemanticGroupID) -> List[db.WordID]:
        # @TODO(hl): SPEED
        coll_ids = self.db.get_collocations_of_sem_group(sg)
        colls = self.get_collocations_from_ids(coll_ids)
        assert len(set(coll_ids)) == len(coll_ids)
        result = []
        for coll in colls:
            result.extend(coll.words)
        return result

    def get_connection_ids_with_word_id(self, id_: db.WordID) -> List[db.ConnID]:
        # @TODO(hl): Speed
        collocation_ids = self.db.get_collocation_ids_with_word_id(id_)
        result = []
        for id_ in collocation_ids:
            coll_conns = self.db.get_connection_ids_with_coll_id(id_)
            result.extend(coll_conns)
        return result


def get() -> AppCtx:
    return AppCtx.get()
