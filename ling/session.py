import logging
import os
from typing import List, Tuple
import ling.db as db


def get_config_filename():
    home_folder = os.path.expanduser("~")
    config_file = os.path.join(home_folder, ".ling")
    return config_file


class Session:
    def __init__(self):
        self.db = db.DB()

        # Try to load config
        config_filename = get_config_filename()
        logging.info("Config filename '%s'", config_filename)
        if os.path.exists(config_filename):
            try:
                with open(config_filename, "r", encoding="utf8") as f:
                    data = f.readline()
                    db_name = data.strip()
                    logging.info("Config db path: '%s'", db_name)
                    if os.path.exists(db_name):
                        self.init_for_db(db_name, False)
            except OSError:
                logging.info("Failed to read config file")

    @property
    def connected(self):
        return self.db.connected

    def init_for_db(self, db_name: str, save_config: bool = True):
        self.db.create_or_open(db_name)
        # Try to save to config
        if save_config:
            try:
                config_filename = get_config_filename()
                with open(config_filename, "w", encoding="utf8") as f:
                    f.write(db_name)
                logging.info("Saved db '%s' to config", db_name)
            except OSError:
                logging.info("Failed to write config file")

    def get_collocations_from_ids(self, ids: List[db.CollocationID]) -> List[db.Collocation]:
        db_collocations = [self.db.get_col(col_id) for col_id in ids]
        return db_collocations

    def get_connections_from_ids(self, ids: List[db.ConnID]) -> List[db.Connection]:
        db_collocations = [self.db.get_con(col_id) for col_id in ids]
        return db_collocations

    def get_words_from_ids(self, ids: List[db.WordID]) -> List[db.Word]:
        db_words = [self.db.get_word(id_) for id_ in ids]
        return db_words

    def create_sent_ctx_from_db(self, id_: db.SentenceID) -> "ling.Sentence":
        raise NotImplementedError

    def get_initial_form(self, word: db.Word) -> db.Word:
        # @NOTE(hl): Wrapper for conditional
        # @TODO(hl): It may be beneficial to always store initial_form_id and detect it is the initial form by comparing
        #  ids?
        return self.db.get_word(word.initial_form_id) if word.initial_form_id is not None else word

    def get_initial_form_by_id(self, word_id: db.WordID) -> db.Word:
        return self.get_initial_form(self.db.get_word(word_id))

    def get_words_of_sem_group(self, sg: db.SemanticGroupID) -> List[db.WordID]:
        # @TODO(hl): SPEED
        coll_ids = self.db.get_cols_of_sem_group(sg)
        colls = self.get_collocations_from_ids(coll_ids)
        assert len(set(coll_ids)) == len(coll_ids)
        result = []
        for coll in colls:
            result.extend(coll.words)
        return result

    def get_connection_ids_with_word_id(self, id_: db.WordID) -> List[db.ConnID]:
        # @TODO(hl): Speed
        collocation_ids = self.db.get_col_ids_with_word_id(id_)
        result = []
        for id_ in collocation_ids:
            coll_conns = self.db.get_con_ids_with_coll_id(id_)
            result.extend(coll_conns)
        return result

    def get_pred_sg(self) -> db.SemanticGroupID:
        result_id = self.db.get_sg_id_by_name("Предикат")
        return result_id

    def get_sg_list(self) -> List[Tuple[str, int]]:
        db_sgs = self.db.get_all_sgs()
        result = []
        if db_sgs:
            result = [(sg.name, sg.id) for sg in db_sgs]
        return result
