import os
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
            return func(*args, **kwargs)
        logging.debug("Tried to call func %s with no database open" % func.__name__)
        return None

    return wrapper


SemanticGroupID = typing.NewType("SemanticGroupID", int)
WordID = typing.NewType("WordID", int)
CollocationID = typing.NewType("CollocationID", int)
ConnID = typing.NewType("ConnID", int)
SentenceID = typing.NewType("SentenceID", int)


@dataclasses.dataclass(frozen=True)
class SemanticGroup:
    id: SemanticGroupID
    name: str


@dataclasses.dataclass(frozen=True)
class Word:
    id: WordID
    initial_form_id: Union[WordID, None]
    part_of_speech: ling.PartOfSpeech
    word: str


@dataclasses.dataclass(frozen=True)
class Collocation:
    id: CollocationID
    semantic_group_id: SemanticGroupID
    words: List[WordID]
    words_hash: int


@dataclasses.dataclass(frozen=True)
class Connection:
    id: ConnID
    predicate: CollocationID
    object_: CollocationID


@dataclasses.dataclass(frozen=True)
class Sentence:
    id: SentenceID
    contents: str
    word_count: int
    collocations: List[CollocationID]
    connections: List[ConnID]
    words: List[WordID]


def abstract_sql_resource_get(cursor, query, id_):
    if id_ is not None:
        query += " where id = (?)"
        values = list(cursor.execute(query, (id_,)))
    else:
        values = list(cursor.execute(query))
    return values


@dataclasses.dataclass
class DBCtx:
    filename: str = ""
    database: sqlite3.Connection = None
    cursor: sqlite3.Cursor = None

    def __del__(self):
        if self.cursor is not None:
            self.database.commit()
            self.cursor.close()
        if self.database is not None:
            self.database.close()

    def create_or_open(self, filename):
        self.filename = filename
        self.database = sqlite3.connect(filename)
        self.cursor = self.database.cursor()
        self.create_tables()
        logging.info("Opened DB %s", filename)

    @db_api
    def create_tables(self):
        tables_create_query = open("sql/tables.sql").read()
        self.cursor.executescript(tables_create_query)
        self.database.commit()

    def get_semantic_group_internal(self, id_: Union[SemanticGroupID, None] = None) \
        -> List[SemanticGroup]:
        sql = """select id, name from semantic_group"""
        values = abstract_sql_resource_get(self.cursor, sql, id_)
        logging.info("Queried %d semantic groups", len(values))
        result = []
        for id_, name in values:
            v = SemanticGroup(id_, name)
            result.append(v)
        return result

    def get_word_internal(self, id_: Union[WordID, None] = None) \
            -> List[Word]:
        sql = "select id, initial_form_id, word, part_of_speech, has_initial_form from word"
        values = abstract_sql_resource_get(self.cursor, sql, id_)
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
        sql = "select id, semantic_group_id, word_hash from Collocation"
        values = abstract_sql_resource_get(self.cursor, sql, id_)
        logging.info("Queried %d collocations", len(values))
        result = []
        for id_, kind, word_hash in values:
            sql = """select word_id, idx from collocation_junction
                     where collocation_id = (?)"""
            word_ids = list(self.cursor.execute(sql, (id_,)))
            word_ids.sort(key=lambda it: it[1])
            word_ids = [it[0] for it in word_ids]
            coll = Collocation(CollocationID(id_),
                               SemanticGroupID(kind),
                               word_ids,
                               word_hash)
            result.append(coll)
        return result

    def get_connections_internal(self, id_: Union[ConnID, None] = None) \
            -> List[Connection]:
        sql = "select id, predicate, object from Conn"
        values = abstract_sql_resource_get(self.cursor, sql, id_)
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
        sql = "select id, contents, word_count from Sentence"
        values = abstract_sql_resource_get(self.cursor, sql, id_)
        logging.info("Queried %d sentences", len(values))

        result = []
        for id_, contents, word_count in values:
            sql = """select conn_id from Sentence_Connection_Junction
                                     where sentence_id = (?)"""
            conn_ids = unwrap(self.cursor.execute(sql, (id_,)))
            sql = """select collocation_id from Sentence_Collocation_Junction
                                 where sentence_id = (?)"""
            coll_ids = unwrap(self.cursor.execute(sql, (id_,)))
            sql = """select idx, word_id from sentence_word_junction
                             where sentence_id = (?)"""
            words_serialized = list(self.cursor.execute(sql, (id_,)))
            words = list(flatten_by_idx(sorted(words_serialized, key=lambda it: it[0]), 1))
            sent = Sentence(SentenceID(id_),
                            contents,
                            word_count,
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
    def get_word_id_by_word(self, word: str) -> List[WordID]:
        sql = """select id from word where word = (?)"""
        deriv = unwrap(self.cursor.execute(sql, (word,)))
        deriv = list(map(WordID, deriv))
        return deriv

    @db_api
    def get_word_ids_by_word_part(self, word_part: str) -> List[WordID]:
        sql = "select id from word where form LIKE (?)"
        deriv = unwrap(self.cursor.execute(sql, (word_part,)))
        deriv = list(map(WordID, deriv))
        return deriv

    @db_api
    def get_collocation_ids_with_word_id(self, id_: WordID) -> List[CollocationID]:
        sql = """select DISTinCT collocation_id from Collocation_Junction
                 where word_id = (?)"""
        col_ids = self.cursor.execute(sql, (id_,))
        col_ids = unwrap(col_ids)
        col_ids = list(map(CollocationID, col_ids))
        return col_ids

    @db_api
    def get_connection_ids_with_coll_id(self, id_: CollocationID) -> List[ConnID]:
        sql = """select id from Conn where object = (?)"""
        ids0 = list(self.cursor.execute(sql, (id_,)))
        sql = """select id from Collocation where predicate = (?)"""
        ids1 = list(self.cursor.execute(sql, (id_,)))
        unique_ids = set(*ids0, *ids1)
        return list(unique_ids)

    @db_api
    def get_connection_ids_with_word_id(self, id_: WordID) -> List[ConnID]:
        # @TODO(hl): Speed
        collocation_ids = self.get_collocation_ids_with_word_id(id_)
        result = []
        for id_ in collocation_ids:
            coll_conns = self.get_connection_ids_with_coll_id(id_)
            result.extend(coll_conns)
        return result

    @db_api
    def get_sentences_id_by_word_id(self, id_: WordID) -> List[SentenceID]:
        # @TODO(hl): Speed
        coll_ids = self.get_collocation_ids_with_word_id(id_)
        sql = """select sentence_id from Sentence_Collocation_Junction 
                 where collocation_id = (?)"""
        result = []
        for coll_id in coll_ids:
            coll_sent_ids = list(self.cursor.execute(sql, (coll_id,)))
            result.extend(coll_sent_ids)
        return result

    @db_api
    def get_semantic_group_id_by_name(self, name: str) -> SemanticGroupID:
        sql = """select id from semantic_group where name = (?)"""
        groups = list(self.cursor.execute(sql, (name, )))
        result = 0
        if groups:
            result = groups[0][0]
        return result

    @db_api
    def get_sentences_id_by_word(self, word: str) -> List[SentenceID]:
        sql = """select id from Sentence where contents LIKE '%' || ? || '%' """
        sentences = self.cursor.execute(sql, (word,))
        sentences = unwrap(sentences)
        return sentences

    @db_api
    def get_collocations_of_sem_group(self, sg: SemanticGroupID) -> List[CollocationID]:
        # @TODO(hl): Speed
        logging.info("get_collocations_of_sem_group %d" % sg)
        colls = self.get_all_collocations()
        result = [it.id for it in colls if it.semantic_group_id == sg]
        return list(set(result))

    @db_api
    def add_or_update_sentence_record(self, sent: ling.SentenceCtx):
        logging.info("Updating sentence %s (wc %d)", sent.text, len(sent.words))
        #
        # add sentence record
        #
        sql = "insert OR IGNORE into Sentence (contents, word_count) values (?, ?)"
        self.cursor.execute(sql, (sent.text, len(sent.words)))

        sql = "select id from Sentence where contents = (?)"
        sentence_id = self.cursor.execute(sql, (sent.text,))
        sentence_id = next(sentence_id)

        #
        # first of all, delete all previous entries about sentence
        #
        sql = """delete from Sentence_Collocation_Junction where sentence_id = (?)"""
        self.cursor.execute(sql, sentence_id)

        sql = """delete from Sentence_Connection_Junction where sentence_id = (?)"""
        self.cursor.execute(sql, sentence_id)
        sql = """delete from sentence_word_junction where sentence_id = (?)"""
        self.cursor.execute(sql, sentence_id)
        #
        # now start populating database again
        #
        logging.info("Inserting %d words" % len(sent.words))
        word_ids = []
        for idx, (word, start_idx) in enumerate(zip(sent.words, sent.word_start_idxs)):
            word_id = self.get_or_insert_word(word)
            junction_data = (sentence_id[0], word_id, idx, start_idx)
            sql = """insert into sentence_word_junction (sentence_id, word_id, idx, text_idx)
                     values (?, ?, ?, ?)"""
            self.cursor.execute(sql, junction_data)
            word_ids.append(word_id)

        logging.info("Inserting %d collocations" % len(sent.collocations))

        collocation_ids = []
        for idx, collocation in enumerate(sent.collocations):
            from zlib import crc32
            # @TODO(hl): Better hash function
            collocation_words = list(map(lambda it: sent.words[it], collocation.word_idxs))
            words_hash = crc32(bytes(str(collocation_words), "utf8"))
            print(collocation_words, words_hash)
            # First of all, try to find collocation with same words
            # @HACK(hl): Because it is complicated and slow to do checks for all junctions, we use word hash here
            #  This way we can directly compare it
            sql = """select id from collocation where word_hash = (?)"""
            collocation_id = unwrap(self.cursor.execute(sql, (words_hash, )))
            if not collocation_id:
                logging.info("Inserting collocation %d %s" % (collocation.semantic_group, str(collocation_words)))
                sql = """insert into collocation (semantic_group_id, word_hash) values (?, ?)"""
                self.cursor.execute(sql, (collocation.semantic_group, words_hash))
                sql = """select id from collocation
                         where rowid = ( select last_insert_rowid() )"""
                collocation_id = self.cursor.execute(sql)
                collocation_id = next(collocation_id)[0]

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
            self.cursor.execute(sql, (sentence_id[0], collocation_id))
            collocation_ids.append(collocation_id)

        logging.info("Inserting %d connections" % len(sent.connections))
        for connection in sent.connections:
            print(connection, collocation_ids, sent.connections, sent.collocations)
            sql = """insert or ignore into Conn (predicate, object) 
                     values(?, ?)
                     """
            conn_collocation_ids = (collocation_ids[connection[0]], collocation_ids[connection[1]])
            self.cursor.execute(sql, conn_collocation_ids)

            # @TODO(hl): Uniquiness
            sql = """select id from Conn
                     where rowid = ( select last_insert_rowid() )"""
            conn_id = self.cursor.execute(sql)
            conn_id = next(conn_id)[0]
            sql = """insert into Sentence_Connection_Junction (sentence_id, conn_id)
                     values(?, ?)"""
            self.cursor.execute(sql, (sentence_id[0], conn_id))

        self.database.commit()

    @db_api
    def get_or_insert_word(self, word: str) -> WordID:
        word = word.lower()
        word = ling.Word.create(word)

        if word.initial_form is not None:
            initial_form_id = self.get_or_insert_word(word.initial_form)
        else:
            initial_form_id = None
        form_sql_data = (word.word, word.part_of_speech.value, initial_form_id, initial_form_id is not None)
        sql = """insert OR IGNORE into word 
                 (word, part_of_speech, initial_form_id, has_initial_form) 
                 values (?, ?, ?, ?)"""
        self.cursor.execute(sql, form_sql_data)

        sql = """select id from word
                 where word = (?) and part_of_speech = (?) and (initial_form_id = (?) or not has_initial_form) """
        word_id = self.cursor.execute(sql, form_sql_data[:3])
        word_id = next(word_id)[0]
        logging.info("Inserted word %s" % word)
        return word_id

    @db_api
    def add_semantic_group(self, name: str) -> SemanticGroupID:
        sg = self.get_semantic_group_id_by_name(name)
        if sg:
            logging.warning("Semantic group %s is already defined (id %d)", name, sg)
            return sg

        sql = """insert into semantic_group (name) values (?)"""
        self.cursor.execute(sql, (name, ))
        sg = self.get_semantic_group_id_by_name(name)
        assert sg is not None and sg
        return sg
        
    @db_api 
    def remove_semantic_group(self, id_: SemanticGroupID):
        # @TODO(hl): MAKE SURE NO LINKS TO DELETED SEMANTIC GROUP ARE STILL IN DB
        sg = self.get_semantic_group(id_)
        if sg is None:
            logging.error("Semantic group %d does nto exist" % id_)
        sql = """delete from semantic_group where id = (?)"""
        self.cursor.execute(sql, (id_, ))

    @db_api
    def get_words_with_initial_form(self, word_id: WordID) -> List[WordID]:
        sql = """select id from word where initial_form_id = (?)"""
        word_ids = unwrap(self.cursor.execute(sql, (word_id, )))
        return word_ids


def test_db_ctx():
    db_name = "test.sqlite"

    try:
        ctx = DBCtx()
        ctx.create_or_open(db_name)

        predicate = ctx.add_semantic_group("Предикат")
        object_ = ctx.add_semantic_group("Объект")

        text = "Летчик пилотировал самолет боковой ручкой управления в плохую погоду. Мама мыла Милу мылом."
        text_ctx = ling.TextCtx()
        text_ctx.init_for_text(text)

        sentence1 = text_ctx.start_sentence_edit(10)
        sentence1.add_collocation([0, 1, 2], object_)
        sentence1.mark_text_part(20, 40, predicate)
        sentence1.make_connection(0, 1)

        sentence2 = text_ctx.start_sentence_edit(80)

        ctx.add_or_update_sentence_record(sentence1)
        ctx.add_or_update_sentence_record(sentence2)

        # word = "ручкой"
        # print("--Init of ", word)
        # a = ctx.get_initial_form(word)
        # print('\n'.join(map(str, a)))
        #
        # print("--All inits")
        # a = ctx.get_initial_form()
        # print('\n'.join(map(str, a)))
        #
        # print("--Deriv of", word)
        # a = ctx.get_word(word)
        # print('\n'.join(map(str, a)))
        #
        # print("--All derivs")
        # a = ctx.get_word()
        # print('\n'.join(map(str, a)))
        #
        # print("--All collocations")
        # a = ctx.get_collocation()
        # print('\n'.join(map(str, a)))
        #
        # print("--Coll with", word)
        # a = ctx.get_collocation(word)
        # print('\n'.join(map(str, a)))
        #
        # print("--All connections")
        # a = ctx.get_connection()
        # print('\n'.join(map(str, a)))
        #
        # print("--Connection with", word)
        # a = ctx.get_connection(word)
        # print('\n'.join(map(str, a)))
        #
        # print("--All sentence ids")
        # a = ctx.get_sentence_id()
        # print("\n".join(map(str, a)))
        #
        # print("--All sentence texts")
        # a = list(map(ctx.get_sentence_text, a))
        # print("\n".join(a))
        #
        # print("--Sentences with", word)
        # a = ctx.get_sentences_by_word(word)
        # print("\n".join(map(str, a)))
    except Exception:
        traceback.print_exc()
    # os.remove(db_name)


if __name__ == "__main__":
    test_db_ctx()
