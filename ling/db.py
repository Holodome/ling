"""
File containing functions forming an API for interacting with SQL database
"""
import sqlite3
import typing
from typing import Union, List
import logging
import functools
import dataclasses

import ling.word 


def flatten_by_idx(arr, idx):
    return list(map(lambda it: it[idx], arr))


def unwrap(x):
    return flatten_by_idx(x, 0)


def safe_unpack(_list: list):
    assert _list
    return _list[0]


def require_db(func):
    """
    Декоратор для методов API работы с базой данных - мы хотим получить корректную обработку ошибок
    в случае отсутствия инициализации (когда бд не открыта) без исключений и их обработки
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        assert len(args) >= 1
        self = args[0]
        if self.database is not None:
            result = func(*args, **kwargs)
            return result
        logging.error("Tried to call func %s with no database open" % func.__name__)
        return None

    return wrapper


#
# Aliases for db id's to use in type annotations
#
SemanticGroupID = typing.NewType("SemanticGroupID", int)
WordID = typing.NewType("WordID", int)
CollocationID = typing.NewType("CollocationID", int)
ConnID = typing.NewType("ConnID", int)
SentenceID = typing.NewType("SentenceID", int)


#
# orM
#
@dataclasses.dataclass(frozen=True)
class SemanticGroup:
    """Semantic group is an object that simulates an expandable enumeration of linguistic semantic groups
       Semantic groups are linked with cols and are used in cons"""
    id: SemanticGroupID
    # Name in russian, case is undefined
    name: str


@dataclasses.dataclass(frozen=True)
class Word:
    """Word is a description of some abstract word"""
    # @NOTE(hl): Currently numbers are also words
    id: WordID
    # ID of initial form if word has some, otherwise None
    initial_form_id: Union[WordID, None]
    # Word for in russian, lowercase
    word: str
    # Part of speech
    pos: int


@dataclasses.dataclass(frozen=True)
class Collocation:
    """Collocation - combination of words with a semantic group attached to it"""
    id: CollocationID
    # What semantic group does this col has
    sg_id: SemanticGroupID
    # All words in col in correct order
    words: List[WordID]
    # String used to ensure uniqueness of col in DB - this can be replaced with a proper hash functions
    words_hash: int
    # Words like they are met in sentence
    text: str


@dataclasses.dataclass(frozen=True)
class Connection:
    """Connection is a combination of predicate col and col of some other kind"""
    id: ConnID
    predicate: CollocationID
    object_: CollocationID


@dataclasses.dataclass(frozen=True)
class Sentence:
    """Sentence record like it is edited by user. Sentence is a con of cols, cons and words
       with same word set (or text)"""
    id: SentenceID
    # Text of sentence
    contents: str
    # Set of cols
    cols: List[CollocationID]
    # Set of cons
    cons: List[ConnID]
    # Set of words
    words: List[WordID]


@dataclasses.dataclass
class DB:
    """
    Class encapsulating all methods of directly interacting with DB.
    It is made a dataclass to make interface function calls always work,
    even if the database itself is not present/open
    Instead, error message is given on improper function calls
    """
    # sqlite file name
    filename: str = ""
    database: sqlite3.Connection = None
    cursor: sqlite3.Cursor = None
    # @TODO(hl): Backups

    @property
    def connected(self):
        return self.database is not None

    def create_or_open(self, filename):
        self.filename = filename
        self.database = sqlite3.connect(filename)
        self.cursor = self.database.cursor()
        self.create_tables()
        default_sgs = [
            "Предикат",
            "Объект",
            "Агент",
            "Инструмент",
            "Локатив",
            "Погодные условия",
            "Высота",
            "Режим",
            "Угол наклона",
            "Скорость"
        ]
        for sg_name in default_sgs:
            self.add_sg(sg_name)

        logging.info("Opened DB %s", filename)

    def __del__(self):
        if self.cursor is not None:
            self.database.commit()
            self.cursor.close()
        if self.database is not None:
            self.database.close()

    def execute(self, sql: str, *args):
        """
        Wrapper for common sql execute idiom
        Returns list with elements either being tuples of results if there are multiple return values,
        or individual results

        Additionally has convenience of no need to form tuple for arguments, because in most cases
        arguments are passed as individual elements rather than tuples
        """
        result = list(self.cursor.execute(sql, tuple(args)))
        if result:
            if len(result[0]) == 1:
                result = unwrap(result)
        return result

    def abstract_sql_resource_get(self, query: str, id_):
        """
        Helper function for querying some value from db.
        They are written in a way that supports both getting all values and value of specific id
        In order to make that work this method is used, which does query in a way way that supports that behaviour
        If id_ is None, all resources are get, otherwise single one with this id
        """
        if id_ is not None:
            query += " where id = (?)"
            values = self.execute(query, id_)
        else:
            values = self.execute(query)
        return values

    @require_db
    def create_tables(self):
        """
        Executes table creating script
        """
        tables_create_query = open("sql/tables.sql", encoding="utf8").read()
        self.cursor.executescript(tables_create_query)
        self.database.commit()

    def get_sg_internal(self, id_: Union[SemanticGroupID, None] = None) \
            -> List[SemanticGroup]:
        """Helper function for getting semantic groups"""
        sql = """select id, name from semantic_group"""
        values = self.abstract_sql_resource_get(sql, id_)
        logging.info("Queried %d semantic groups", len(values))
        result = []
        for id_, name in values:
            v = SemanticGroup(id_, name)
            result.append(v)
        return result

    def get_word_internal(self, id_: Union[WordID, None] = None) \
            -> List[Word]:
        """Helper function for getting words"""
        sql = "select id, initial_form_id, word, part_of_speech, has_initial_form from word"
        values = self.abstract_sql_resource_get(sql, id_)
        logging.info("Queried %d derivative forms", len(values))
        result = []
        for id_, init_id, form, pos, has_init in values:
            deriv = Word(WordID(id_),
                         WordID(init_id),
                         form,
                         pos)
            result.append(deriv)
        return result

    def get_cols_internal(self, id_: Union[CollocationID, None] = None) \
            -> List[Collocation]:
        """Helper function for getting cols"""
        sql = "select id, sg_id, word_hash, words_text from Collocation"
        values = self.abstract_sql_resource_get(sql, id_)
        logging.info("Queried %d cols", len(values))
        result = []
        for id_, kind, word_hash, text in values:
            sql = """select word_id, idx from collocation_junction
                     where col_id = (?)"""
            word_ids = self.execute(sql, id_)
            word_ids.sort(key=lambda it: it[1])
            word_ids = [it[0] for it in word_ids]
            coll = Collocation(CollocationID(id_),
                               SemanticGroupID(kind),
                               word_ids,
                               word_hash,
                               text)
            result.append(coll)
        return result

    def get_cons_internal(self, id_: Union[ConnID, None] = None) \
            -> List[Connection]:
        """Helper function for getting cons"""
        sql = "select id, predicate, object from Conn"
        values = self.abstract_sql_resource_get(sql, id_)
        logging.info("Queried %d cons", len(values))
        result = []
        for id_, pred_id, obj_id in values:
            coll = Connection(ConnID(id_),
                              CollocationID(pred_id),
                              CollocationID(obj_id))
            result.append(coll)
        return result

    def get_sentences_internal(self, id_: Union[SentenceID, None] = None) \
            -> List[Sentence]:
        """Helper function for getting sentences"""
        sql = "select id, contents from Sentence"
        values = self.abstract_sql_resource_get(sql, id_)
        logging.info("Queried %d sentences", len(values))

        result = []
        for id_, contents in values:
            sql = """select con_id from Sentence_Connection_Junction
                     where sent_id = (?)"""
            conn_ids = self.execute(sql, id_)
            sql = """select col_id from Sentence_Collocation_Junction
                     where sent_id = (?)"""
            coll_ids = self.execute(sql, id_)
            sql = """select idx, word_id from sentence_word_junction
                     where sent_id = (?)"""
            words_serialized = self.execute(sql, id_)
            words = list(flatten_by_idx(sorted(words_serialized, key=lambda it: it[0]), 1))
            sent = Sentence(SentenceID(id_),
                            contents,
                            coll_ids,
                            conn_ids,
                            words)
            result.append(sent)
        return result

    @require_db
    def get_all_sgs(self) -> List[SemanticGroup]:
        logging.info("Querying all semantic groups")
        return self.get_sg_internal()

    @require_db
    def get_all_words(self) -> List[Word]:
        logging.info("Querying all words")
        return self.get_word_internal()

    @require_db
    def get_all_cols(self) -> List[Collocation]:
        logging.info("Querying all cols")
        return self.get_cols_internal()

    @require_db
    def get_all_cons(self) -> List[Connection]:
        logging.info("Querying all cons")
        return self.get_cons_internal()

    @require_db
    def get_all_sentences(self) -> List[Sentence]:
        logging.info("Querying all sentences")
        return self.get_sentences_internal()

    @require_db
    def get_sg(self, id_: SemanticGroupID) -> SemanticGroup:
        logging.info("Querying semantic group %d " % id_)
        result = self.get_sg_internal(id_)
        if not result:
            logging.error("Failed to query semantic group %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @require_db
    def get_word(self, id_: WordID) -> Word:
        logging.info("Querying word %d" % id_)
        result = self.get_word_internal(id_)
        if not result:
            logging.error("Failed to query word %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @require_db
    def get_col(self, id_: CollocationID) -> Collocation:
        logging.info("Querying col %d" % id_)
        result = self.get_cols_internal(id_)
        if not result:
            logging.error("Failed to query col %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @require_db
    def get_con(self, id_: ConnID) -> Connection:
        logging.info("Querying con %d" % id_)
        result = self.get_cons_internal(id_)
        if not result:
            logging.error("Failed to query con %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @require_db
    def get_sentence(self, id_: SentenceID) -> Sentence:
        logging.info("Querying sentence %d" % id_)
        result = self.get_sentences_internal(id_)
        if not result:
            logging.error("Failed to query sentence %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @require_db
    def get_word_id_by_word(self, word: str) -> WordID:
        """Returns word id by its string"""
        sql = """select id from word where word = (?)"""
        deriv = self.execute(sql, word)
        deriv = list(map(WordID, deriv))
        assert len(deriv) <= 1
        return deriv[0]

    @require_db
    def get_col_ids_with_word_id(self, id_: WordID) -> List[CollocationID]:
        """Returns all cols containing word"""
        sql = """select distinct col_id from Collocation_Junction
                 where word_id = (?)"""
        col_ids = self.execute(sql, id_)
        col_ids = list(map(CollocationID, col_ids))
        return col_ids

    @require_db
    def get_con_ids_with_coll_id_object(self, id_: CollocationID) -> List[ConnID]:
        """Return all cons where object is given col"""
        sql = """select id from conn where object = (?)"""
        ids0 = self.execute(sql, id_)
        return ids0

    @require_db
    def get_con_ids_with_coll_id_predicate(self, id_: CollocationID) -> List[ConnID]:
        """Return all cons where predicate is given col"""
        sql = """select id from conn where predicate = (?)"""
        ids1 = self.execute(sql, id_)
        return ids1

    @require_db
    def get_con_ids_with_col_id(self, id_: CollocationID) -> List[ConnID]:
        """Return all cons with given col"""
        return list(set(self.get_con_ids_with_coll_id_object(id_) +
                        self.get_con_ids_with_coll_id_predicate(id_)))

    @require_db
    def get_sentences_id_by_word_id(self, id_: WordID) -> List[SentenceID]:
        """Returns all sentences with word"""
        sql = """select distinct sent_id from sentence_word_junction where word_id = (?)"""
        result = self.execute(sql, id_)
        return result

    @require_db
    def get_sg_id_by_name(self, name: str) -> SemanticGroupID:
        """Returns semantic group id by name"""
        sql = """select id from semantic_group where name = (?)"""
        groups = self.execute(sql, name)
        result = 0
        if groups:
            result = groups[0]
        return result

    @require_db
    def get_word_ids_by_word_part(self, word: str) -> List[SentenceID]:
        """Returns sentences where word is met in text"""
        sql = """select id from word where word LIKE '%' || ? || '%' """
        sentences = self.execute(sql, word)
        return sentences

    @require_db
    def get_cols_of_sg(self, sg: SemanticGroupID) -> List[CollocationID]:
        """Returns all col that have given semantic group"""
        logging.info("get_cols_of_sg %d" % sg)
        sql = """select id from collocation where sg_id = (?)"""
        result = self.execute(sql, sg)
        return result

    @require_db
    def delete_sentence(self, sent_id: SentenceID):
        sql = """delete from sentence where id = (?)"""
        self.execute(sql, sent_id)

        sql = """delete from Sentence_Collocation_Junction where sent_id = (?)"""
        self.execute(sql, sent_id)

        sql = """delete from Sentence_Connection_Junction where sent_id = (?)"""
        self.execute(sql, sent_id)
        sql = """delete from sentence_word_junction where sent_id = (?)"""
        self.execute(sql, sent_id)

        sql = """delete from collocation where id not in (
            select col_id from sentence_collocation_junction
        )"""
        self.execute(sql)
        sql = """delete from conn where id not in (
            select con_id from sentence_connection_junction
        )"""
        self.execute(sql)
        sql = """delete from word where id not in (
            select word_id from sentence_word_junction
        ) and id not in (
            select initial_form_id from word 
        )"""
        self.execute(sql)
        self.database.commit()

    @require_db
    def add_or_update_sentence_record(self, sent: "sentence.Sentence"):
        """Inserts sentence into database"""
        logging.info("Updating sentence %s (wc %d)", sent.text, len(sent.words))
        #
        # add sentence record
        #
        sql = "insert or ignore into Sentence (contents) values (?)"
        self.execute(sql, sent.text)

        sql = "select id from Sentence where contents = (?)"
        sentence_id = safe_unpack(self.execute(sql, sent.text))

        #
        # first of all, delete all previous entries about sentence
        #
        sql = """delete from Sentence_Collocation_Junction where sent_id = (?)"""
        self.execute(sql, sentence_id)

        sql = """delete from Sentence_Connection_Junction where sent_id = (?)"""
        self.execute(sql, sentence_id)
        sql = """delete from sentence_word_junction where sent_id = (?)"""
        self.execute(sql, sentence_id)

        #
        # now start populating database again
        #
        logging.info("Inserting %d words" % len(sent.words))
        word_ids = []
        for idx, (word, start_idx) in enumerate(zip(sent.words, sent.word_starts)):
            word_id = self.get_or_insert_word(word)
            junction_data = (sentence_id, word_id, idx, start_idx)
            sql = """insert into sentence_word_junction (sent_id, word_id, idx, text_idx)
                     values (?, ?, ?, ?)"""
            self.execute(sql, *junction_data)
            word_ids.append(word_id)

        logging.info("Inserting %d cols" % len(sent.cols))

        col_ids = []
        for idx, col in enumerate(sent.cols):
            col_words = list(map(lambda it: sent.words[it], col.word_idxs))
            word_hash = " ".join(col_words)
            word_hash = word_hash.lower()
            # First of all, try to find col with same words
            # @HACK(hl): Because it is complicated and slow to do checks for all junctions, we use word hash here
            #  This way we can directly compare it
            sql = """select id from collocation where word_hash = (?)"""
            col_id = self.execute(sql, word_hash)
            if not col_id:
                logging.info("Inserting col %d %s" % (col.sg, str(col_words)))
                sql = """insert into collocation (sg_id, word_hash, words_text) values (?, ?, ?)"""
                # @TODO(hl): Proper words_text
                self.execute(sql, col.sg, word_hash, word_hash)
                sql = """select id from collocation
                         where rowid = ( select last_insert_rowid() )"""
                col_id = safe_unpack(self.execute(sql))

                sql = """insert into collocation_junction (word_id, col_id, idx)
                         values (?, ?, ?)
                         """
                words = list(map(lambda it: (word_ids[it[1]], col_id, it[0]), enumerate(col.word_idxs)))
                self.cursor.executemany(sql, words)
            else:
                logging.debug("Collocation %d %s is already present " % (col.sg, str(col_words)))
                col_id = col_id[0]

            sql = """insert into Sentence_Collocation_Junction (sent_id, col_id)
                     values (?, ?)"""
            self.execute(sql, sentence_id, col_id)
            col_ids.append(col_id)

        logging.info("Inserting %d cons" % len(sent.cons))
        for con in sent.cons:
            sql = """insert or ignore into Conn (predicate, object) 
                     values(?, ?)
                     """
            conn_col_ids = (col_ids[con.predicate_idx], col_ids[con.actant_idx])
            self.execute(sql, *conn_col_ids)

            sql = """select id from Conn
                     where predicate = (?) and object = (?)"""
            conn_id = safe_unpack(self.execute(sql, *conn_col_ids))
            sql = """insert into Sentence_Connection_Junction (sent_id, con_id)
                     values(?, ?)"""
            self.execute(sql, sentence_id, conn_id)

        self.database.commit()

    @require_db
    def get_or_insert_word(self, word_str: str) -> WordID:
        if not word_str:
            logging.warning("Empty word supplied to get_or_insert_word")
        word_str = word_str.lower()
        word = ling.word.analyse_word(word_str)
        if word.initial_form is not None:
            initial_form_id = self.get_or_insert_word(word.initial_form)
        else:
            initial_form_id = None
        form_sql_data = (word.word, word.part_of_speech, initial_form_id, initial_form_id is not None)
        sql = """insert or ignore into word 
                 (word, part_of_speech, initial_form_id, has_initial_form) 
                 values (?, ?, ?, ?)"""
        self.execute(sql, *form_sql_data)

        sql = """select id from word
                 where word = (?) and part_of_speech = (?) and (initial_form_id = (?) or not has_initial_form) """
        word_id = safe_unpack(self.execute(sql, *form_sql_data[:3]))
        logging.info("Inserted word %s" % word)
        return word_id

    @require_db
    def add_sg(self, name: str) -> SemanticGroupID:
        sg = self.get_sg_id_by_name(name)
        if sg:
            logging.warning("Semantic group %s is already defined (id %d)", name, sg)
        else:
            sql = """insert into semantic_group(name) values (?)"""
            self.execute(sql, name)
            sg = self.get_sg_id_by_name(name)
            assert sg is not None and sg
            logging.info("Inserted semantic group %s" % name)
        return sg
        
    @require_db 
    def remove_sg(self, id_: SemanticGroupID):
        # @TODO(hl): MAKE SURE NO LINKS TO DELETED SEMANTIC GROUP ARE STILL IN DB
        sg = self.get_sg(id_)
        if sg is None:
            logging.error("Semantic group %d does nto exist" % id_)
        else:
            sql = """delete from semantic_group where id = (?)"""
            self.execute(sql, id_)

    @require_db
    def get_words_with_initial_form(self, word_id: WordID) -> List[WordID]:
        # Returns words with given initial form, not including initial form
        sql = """select id from word where initial_form_id = (?)"""
        word_ids = self.execute(sql, word_id)
        return word_ids


