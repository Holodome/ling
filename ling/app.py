"""
High-level application interface
"""

import dataclasses
import ling.db_model as db
import ling.ling as ling
import ling.sent_wdg as sent_wdg


class AppCtx:
    _instance = None

    def __init__(self):
        self.db = db.DBCtx()

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def create_sent_ctx_from_db(self, id_: db.SentenceID) -> ling.SentenceCtx:
        sentence = self.db.get_sentence(id_)
        db_collocations = [self.db.get_collocation(col_id) for col_id in sentence.collocations]
        db_connections = [self.db.get_connection(col_id) for col_id in sentence.connections]

        sent_ctx = ling.SentenceCtx()
        # @NOTE(hl): Cause we're lazy to do proper initialization with words
        sent_ctx.init_from_text(sentence.contents)

        ling_collocations = []
        for db_col in db_collocations:
            col_words = [self.db.get_word(word_id) for word_id in db_col.words]
            word_idxs = [sent_ctx.words.index(word.word) for word in col_words]
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


def get() -> AppCtx:
    return AppCtx.get()
