"""
File containing functions forming an API for interacting with SQL database
"""
import sqlite3
import traceback
import typing
from typing import Union, List
import logging
import functools

import ling.ling as ling
import dataclasses


def flatten_by_idx(arr, idx):
    return list(map(lambda it: it[idx], arr))


def unwrap(x):
    return flatten_by_idx(x, 0)


def safe_unpack(_list: list):
    assert _list
    return _list[0]


def db_api(func):
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
        raise RuntimeError
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
# ORM
#
@dataclasses.dataclass(frozen=True)
class SemanticGroup:
    """Semantic group is an object that simulates an expandable enumeration of linguistic semantic groups
       Semantic groups are linked with collocations and are used in connections"""
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
    # Some additional info, this may to be actually useful
    part_of_speech: ling.PartOfSpeech
    # Word for in russian, lowercase
    word: str


@dataclasses.dataclass(frozen=True)
class Collocation:
    """Collocation - combination of words with a semantic group attached to it"""
    id: CollocationID
    # What semantic group does this collocation has
    semantic_group_id: SemanticGroupID
    # All words in collocation in correct order
    words: List[WordID]
    # String used to ensure uniqueness of collocation in DB - this can be replaced with a proper hash functions
    words_hash: int
    # Words like they are met in sentence
    text: str


@dataclasses.dataclass(frozen=True)
class Connection:
    """Connection is a combination of predicate collocation and collocation of some other kind"""
    id: ConnID
    predicate: CollocationID
    object_: CollocationID


@dataclasses.dataclass(frozen=True)
class Sentence:
    """Sentence record like it is edited by user. Sentence is a connection of collocations, connections and words
       with same word set (or text)"""
    id: SentenceID
    # Text of sentence
    contents: str
    # Set of collocations
    collocations: List[CollocationID]
    # Set of connections
    connections: List[ConnID]
    # Set of words
    words: List[WordID]


@dataclasses.dataclass
class DBCtx:
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

    def create_or_open(self, filename):
        self.filename = filename
        self.database = sqlite3.connect(filename)
        self.cursor = self.database.cursor()
        self.create_tables()
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

    @db_api
    def create_tables(self):
        """
        Executes table creating script
        """
        tables_create_query = open("sql/tables.sql").read()
        self.cursor.executescript(tables_create_query)
        self.database.commit()

    def get_semantic_group_internal(self, id_: Union[SemanticGroupID, None] = None) \
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
                         ling.PartOfSpeech(pos),
                         form)
            result.append(deriv)
        return result

    def get_collocations_internal(self, id_: Union[CollocationID, None] = None) \
            -> List[Collocation]:
        """Helper function for getting collocations"""
        sql = "select id, semantic_group_id, word_hash, words_text from Collocation"
        values = self.abstract_sql_resource_get(sql, id_)
        logging.info("Queried %d collocations", len(values))
        result = []
        for id_, kind, word_hash, text in values:
            sql = """select word_id, idx from collocation_junction
                     where collocation_id = (?)"""
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

    def get_connections_internal(self, id_: Union[ConnID, None] = None) \
            -> List[Connection]:
        """Helper function for getting connections"""
        sql = "select id, predicate, object from Conn"
        values = self.abstract_sql_resource_get(sql, id_)
        logging.info("Queried %d connections", len(values))
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
            sql = """select conn_id from Sentence_Connection_Junction
                     where sentence_id = (?)"""
            conn_ids = self.execute(sql, id_)
            sql = """select collocation_id from Sentence_Collocation_Junction
                     where sentence_id = (?)"""
            coll_ids = self.execute(sql, id_)
            sql = """select idx, word_id from sentence_word_junction
                     where sentence_id = (?)"""
            words_serialized = self.execute(sql, id_)
            words = list(flatten_by_idx(sorted(words_serialized, key=lambda it: it[0]), 1))
            sent = Sentence(SentenceID(id_),
                            contents,
                            coll_ids,
                            conn_ids,
                            words)
            result.append(sent)
        return result

    @db_api
    def get_all_semantic_groups(self) -> List[SemanticGroup]:
        logging.info("Querying all semantic groups")
        return self.get_semantic_group_internal()

    @db_api
    def get_all_words(self) -> List[Word]:
        logging.info("Querying all words")
        return self.get_word_internal()

    @db_api
    def get_all_collocations(self) -> List[Collocation]:
        logging.info("Querying all collocations")
        return self.get_collocations_internal()

    @db_api
    def get_all_connections(self) -> List[Connection]:
        logging.info("Querying all connections")
        return self.get_connections_internal()

    @db_api
    def get_all_sentences(self) -> List[Sentence]:
        logging.info("Querying all sentences")
        return self.get_sentences_internal()

    @db_api
    def get_semantic_group(self, id_: SemanticGroupID) -> SemanticGroup:
        logging.info("Querying semantic group %d " % id_)
        result = self.get_semantic_group_internal(id_)
        if not result:
            logging.error("Failed to query semantic group %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @db_api
    def get_word(self, id_: WordID) -> Word:
        logging.info("Querying word %d" % id_)
        result = self.get_word_internal(id_)
        if not result:
            logging.error("Failed to query word %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @db_api
    def get_collocation(self, id_: CollocationID) -> Collocation:
        logging.info("Querying collocation %d" % id_)
        result = self.get_collocations_internal(id_)
        if not result:
            logging.error("Failed to query collocation %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @db_api
    def get_connection(self, id_: ConnID) -> Connection:
        logging.info("Querying connection %d" % id_)
        result = self.get_connections_internal(id_)
        if not result:
            logging.error("Failed to query connection %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @db_api
    def get_sentence(self, id_: SentenceID) -> Sentence:
        logging.info("Querying sentence %d" % id_)
        result = self.get_sentences_internal(id_)
        if not result:
            logging.error("Failed to query sentence %d" % id_)
        else:
            logging.debug(result)
        return result[0] if result else None

    @db_api
    def get_word_id_by_word(self, word: str) -> WordID:
        """Returns word id by its string"""
        sql = """select id from word where word = (?)"""
        deriv = self.execute(sql, word)
        deriv = list(map(WordID, deriv))
        assert len(deriv) <= 1
        return deriv[0]

    @db_api
    def get_word_ids_by_word_part(self, word_part: str) -> List[WordID]:
        """Returns word ids where word_part is met"""
        sql = "select id from word where form LIKE (?)"
        deriv = self.execute(sql, word_part)
        deriv = list(map(WordID, deriv))
        return deriv

    @db_api
    def get_collocation_ids_with_word_id(self, id_: WordID) -> List[CollocationID]:
        """Returns all collocations containing word"""
        sql = """select distinct collocation_id from Collocation_Junction
                 where word_id = (?)"""
        col_ids = self.execute(sql, id_)
        col_ids = list(map(CollocationID, col_ids))
        return col_ids

    @db_api
    def get_connection_ids_with_coll_id_object(self, id_: CollocationID) -> List[ConnID]:
        """Return all connections where object is given collocation"""
        sql = """select id from conn where object = (?)"""
        ids0 = self.execute(sql, id_)
        return ids0

    @db_api
    def get_connection_ids_with_coll_id_predicate(self, id_: CollocationID) -> List[ConnID]:
        """Return all connections where predicate is given collocation"""
        sql = """select id from conn where predicate = (?)"""
        ids1 = self.execute(sql, id_)
        return ids1

    @db_api
    def get_connection_ids_with_coll_id(self, id_: CollocationID) -> List[ConnID]:
        """Return all connections with given collocation"""
        return list(set(self.get_connection_ids_with_coll_id_object(id_) +
                        self.get_connection_ids_with_coll_id_predicate(id_)))

    @db_api
    def get_sentences_id_by_word_id(self, id_: WordID) -> List[SentenceID]:
        """Returns all sentences with word"""
        sql = """select distinct sentence_id from sentence_word_junction where word_id = (?)"""
        result = self.execute(sql, id_)
        return result

    @db_api
    def get_semantic_group_id_by_name(self, name: str) -> SemanticGroupID:
        """Returns semantic group id by name"""
        sql = """select id from semantic_group where name = (?)"""
        groups = self.execute(sql, name)
        result = 0
        if groups:
            result = groups[0]
        return result

    @db_api
    def get_sentences_id_by_word(self, word: str) -> List[SentenceID]:
        """Returns sentences where word is met in text"""
        sql = """select id from Sentence where contents LIKE '%' || ? || '%' """
        sentences = self.execute(sql, word)
        return sentences

    @db_api
    def get_collocations_of_sem_group(self, sg: SemanticGroupID) -> List[CollocationID]:
        """Returns all collocation that have given semantic group"""
        logging.info("get_collocations_of_sem_group %d" % sg)
        sql = """select id from collocation where semantic_group_id = (?)"""
        result = self.execute(sql, sg)
        return result

    @db_api
    def add_or_update_sentence_record(self, sent: ling.SentenceCtx):
        """Inserts sentence into database"""
        logging.info("Updating sentence %s (wc %d)", sent.text, len(sent.words))
        #
        # add sentence record
        #
        sql = "insert OR IGNORE into Sentence (contents) values (?)"
        self.execute(sql, sent.text)

        sql = "select id from Sentence where contents = (?)"
        sentence_id = safe_unpack(self.execute(sql, sent.text))

        #
        # first of all, delete all previous entries about sentence
        #
        sql = """delete from Sentence_Collocation_Junction where sentence_id = (?)"""
        self.execute(sql, sentence_id)

        sql = """delete from Sentence_Connection_Junction where sentence_id = (?)"""
        self.execute(sql, sentence_id)
        sql = """delete from sentence_word_junction where sentence_id = (?)"""
        self.execute(sql, sentence_id)
        #
        # now start populating database again
        #
        logging.info("Inserting %d words" % len(sent.words))
        word_ids = []
        for idx, (word, start_idx) in enumerate(zip(sent.words, sent.word_start_idxs)):
            word_id = self.get_or_insert_word(word)
            junction_data = (sentence_id, word_id, idx, start_idx)
            sql = """insert into sentence_word_junction (sentence_id, word_id, idx, text_idx)
                     values (?, ?, ?, ?)"""
            self.execute(sql, *junction_data)
            word_ids.append(word_id)

        logging.info("Inserting %d collocations" % len(sent.collocations))

        collocation_ids = []
        for idx, collocation in enumerate(sent.collocations):
            collocation_words = list(map(lambda it: sent.words[it], collocation.word_idxs))
            word_hash = " ".join(collocation_words)
            word_hash = word_hash.lower()
            # First of all, try to find collocation with same words
            # @HACK(hl): Because it is complicated and slow to do checks for all junctions, we use word hash here
            #  This way we can directly compare it
            sql = """select id from collocation where word_hash = (?)"""
            collocation_id = self.execute(sql, word_hash)
            if not collocation_id:
                logging.info("Inserting collocation %d %s" % (collocation.semantic_group, str(collocation_words)))
                sql = """insert into collocation (semantic_group_id, word_hash, words_text) values (?, ?, ?)"""
                # @TODO(hl): Proper words_text
                self.execute(sql, collocation.semantic_group, word_hash, word_hash)
                sql = """select id from collocation
                         where rowid = ( select last_insert_rowid() )"""
                collocation_id = safe_unpack(self.execute(sql))

                sql = """insert into collocation_junction (word_id, collocation_id, idx)
                         values (?, ?, ?)
                         """
                words = list(map(lambda it: (word_ids[it[1]], collocation_id, it[0]), enumerate(collocation.word_idxs)))
                self.cursor.executemany(sql, words)
            else:
                logging.info("Collocation %d %s is already present " % (collocation.semantic_group, str(collocation_words)))
                collocation_id = collocation_id[0]

            sql = """insert into Sentence_Collocation_Junction (sentence_id, collocation_id)
                     values (?, ?)"""
            self.execute(sql, sentence_id, collocation_id)
            collocation_ids.append(collocation_id)

        logging.info("Inserting %d connections" % len(sent.connections))
        for connection in sent.connections:
            sql = """insert or ignore into Conn (predicate, object) 
                     values(?, ?)
                     """
            conn_collocation_ids = (collocation_ids[connection[0]], collocation_ids[connection[1]])
            self.execute(sql, *conn_collocation_ids)

            sql = """select id from Conn
                     where predicate = (?) and object = (?)"""
            conn_id = safe_unpack(self.execute(sql, *conn_collocation_ids))
            sql = """insert into Sentence_Connection_Junction (sentence_id, conn_id)
                     values(?, ?)"""
            self.execute(sql, sentence_id, conn_id)

        self.database.commit()

    @db_api
    def get_or_insert_word(self, word_str: str) -> WordID:
        if not word_str:
            logging.warning("Empty word supplied to get_or_insert_word")
        word_str = word_str.lower()
        word = ling.Word.create(word_str)
        if word.initial_form is not None:
            initial_form_id = self.get_or_insert_word(word.initial_form)
        else:
            initial_form_id = None
        form_sql_data = (word.word, word.part_of_speech.value, initial_form_id, initial_form_id is not None)
        sql = """insert OR IGNORE into word 
                 (word, part_of_speech, initial_form_id, has_initial_form) 
                 values (?, ?, ?, ?)"""
        self.execute(sql, *form_sql_data)

        sql = """select id from word
                 where word = (?) and part_of_speech = (?) and (initial_form_id = (?) or not has_initial_form) """
        word_id = safe_unpack(self.execute(sql, *form_sql_data[:3]))
        logging.info("Inserted word %s" % word)
        return word_id

    @db_api
    def add_semantic_group(self, name: str) -> SemanticGroupID:
        sg = self.get_semantic_group_id_by_name(name)
        if sg:
            logging.warning("Semantic group %s is already defined (id %d)", name, sg)
        else:
            sql = """insert into semantic_group (name) values (?)"""
            self.execute(sql, name)
            sg = self.get_semantic_group_id_by_name(name)
            assert sg is not None and sg
            logging.info("Inserted semantic group %s" % name)
        return sg
        
    @db_api 
    def remove_semantic_group(self, id_: SemanticGroupID):
        # @TODO(hl): MAKE SURE NO LINKS TO DELETED SEMANTIC GROUP ARE STILL IN DB
        sg = self.get_semantic_group(id_)
        if sg is None:
            logging.error("Semantic group %d does nto exist" % id_)
        else:
            sql = """delete from semantic_group where id = (?)"""
            self.execute(sql, id_)

    @db_api
    def get_words_with_initial_form(self, word_id: WordID) -> List[WordID]:
        # Returns words with given initial form, not including initial form
        sql = """select id from word where initial_form_id = (?)"""
        word_ids = self.execute(sql, word_id)
        return word_ids


