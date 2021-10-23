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


def api_call(func):
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


InitialFormID = typing.NewType("InitialFormID", int)
DerivativeFormID = typing.NewType("DerivativeFormID", int)
CollocationID = typing.NewType("CollocationID", int)
ConnID = typing.NewType("ConnID", int)
SentenceID = typing.NewType("SentenceID", int)


@dataclasses.dataclass
class InitialForm:
    id: InitialFormID
    form: str


@dataclasses.dataclass
class DerivativeForm:
    id: DerivativeFormID
    initial_form_id: InitialFormID
    form: str
    part_of_speech: ling.PartOfSpeech


@dataclasses.dataclass
class Collocation:
    id: CollocationID
    kind: ling.LingKind
    words: List[DerivativeFormID]


@dataclasses.dataclass
class Connection:
    id: ConnID
    predicate: CollocationID
    object_: CollocationID


@dataclasses.dataclass
class Sentence:
    id: SentenceID
    contents: str
    collocations: List[CollocationID]
    connections: List[ConnID]


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

    @api_call
    def create_tables(self):
        tables_create_query = open("sql/tables.sql").read()
        self.cursor.executescript(tables_create_query)
        self.database.commit()

    @api_call
    def get_all_initial_forms(self) -> List[InitialForm]:
        logging.info("Querying all initial forms")
        sql = "SELECT id, form FROM Initial_Form"
        values = list(self.cursor.execute(sql))
        logging.info("Queried %d initial forms", len(values))
        result = []
        for id_, form in values:
            init = InitialForm(InitialFormID(id_), form)
            result.append(init)
        return result

    @api_call
    def get_all_derivative_forms(self) -> List[DerivativeForm]:
        logging.info("Querying all derivative forms")
        # NOTE(hl): not calling SELECT * to make changes easier
        sql = "SELECT id, initial_form_id, form, part_of_speech FROM Derivative_Form"
        values = list(self.cursor.execute(sql))
        logging.info("Queried %d derivative forms", len(values))
        result = []
        for id_, init_id, form, pos in values:
            deriv = DerivativeForm(DerivativeFormID(id_),
                                   InitialFormID(init_id),
                                   form,
                                   ling.PartOfSpeech(pos))
            result.append(deriv)
        return result

    @api_call
    def get_all_collocations(self) -> List[Collocation]:
        logging.info("Querying all collocations")
        sql = "SELECT id, kind FROM Collocation"
        values = list(self.cursor.execute(sql))
        logging.info("Queried %d collocations", len(values))
        result = []
        for id_, kind in values:
            sql = """SELECT derivative_form_id FROM Collocation_Junction
                             WHERE collocation_id = (?)"""
            deriv_ids = list(self.cursor.execute(sql, (id_, )))
            coll = Collocation(CollocationID(id_),
                               ling.LingKind(kind),
                               deriv_ids)
            result.append(coll)
        return result

    @api_call
    def get_all_connections(self) -> List[Connection]:
        logging.info("Querying all connections")
        sql = "SELECT id, predicate, object FROM Conn"
        values = list(self.cursor.execute(sql))
        logging.info("Queried %d connections", len(values))
        result = []
        for id_, pred_id, obj_id in values:
            coll = Connection(ConnID(id_),
                              CollocationID(pred_id),
                              CollocationID(obj_id))
            result.append(coll)
        return result

    @api_call
    def get_all_sentences(self) -> List[Sentence]:
        logging.info("Querying all sentences")
        sql = "SELECT id, contents FROM Sentence"
        values = list(self.cursor.execute(sql))
        logging.info("Queried %d sentences", len(values))

        result = []
        for id_, contents in values:
            sql = """SELECT conn_id FROM Sentence_Connection_Junction
                             WHERE sentence_id = (?)"""
            conn_ids = self.cursor.execute(sql, (id_, ))
            sql = """SELECT collocation_id FROM Sentence_Collocation_Junction
                         WHERE sentence_id = (?)"""
            coll_ids = list(self.cursor.execute(sql, (id_, )))
            sent = Sentence(SentenceID(id_),
                            contents,
                            conn_ids,
                            coll_ids)
            result.append(sent)
        return result

    @api_call
    def get_initial_form(self, id_: InitialFormID) -> InitialForm:
        # @TODO(hl): SPEED
        all_forms = self.get_all_initial_forms()
        result = list(filter(lambda it: it.id == id_, all_forms))
        return result[0] if result else None

    @api_call
    def get_derivative_form(self, id_: DerivativeFormID) -> DerivativeForm:
        # @TODO(hl): SPEED
        all_forms = self.get_all_derivative_forms()
        result = list(filter(lambda it: it.id == id_, all_forms))
        return result[0] if result else None

    @api_call
    def get_collocation(self, id_: CollocationID) -> Collocation:
        # @TODO(hl): SPEED
        all_forms = self.get_all_collocations()
        result = list(filter(lambda it: it.id == id_, all_forms))
        return result[0] if result else None

    @api_call
    def get_connection(self, id_: ConnID) -> Connection:
        # @TODO(hl): SPEED
        all_forms = self.get_all_connections()
        result = list(filter(lambda it: it.id == id_, all_forms))
        return result[0] if result else None

    @api_call
    def get_sentence(self, id_: SentenceID) -> Sentence:
        # @TODO(hl): SPEED
        all_forms = self.get_all_sentences()
        result = list(filter(lambda it: it.id == id_, all_forms))
        return result[0] if result else None

    @api_call
    def get_initial_form_id_by_word(self, word: str) -> InitialFormID:
        sql = """SELECT initial_form_id FROM Derivative_Form WHERE form = (?)"""
        init_id = self.cursor.execute(sql, (word,))
        init_id = flatten_by_idx(init_id, 0)
        assert len(init_id) <= 1
        return init_id[0] if init_id else None

    @api_call
    def get_deriv_form_id_by_word(self, word: str) -> List[DerivativeFormID]:
        sql = """SELECT id FROM Derivative_Form WHERE form = (?)"""
        deriv = list(self.cursor.execute(sql, (word,)))
        deriv = list(map(DerivativeFormID, deriv))
        return deriv

    @api_call
    def get_collocation_ids_with_deriv_id(self, id_: DerivativeFormID) -> List[CollocationID]:
        sql = """SELECT DISTINCT collocation_id FROM Collocation_Junction
                 WHERE derivative_form_id = (?)"""
        col_ids = self.cursor.execute(sql, (id_,))
        col_ids = unwrap(col_ids)
        col_ids = list(map(CollocationID, col_ids))
        return col_ids

    @api_call
    def get_connection_ids_with_coll_id(self, id_: CollocationID) -> List[ConnID]:
        sql = """SELECT id FROM Conn WHERE object = (?)"""
        ids0 = list(self.cursor.execute(sql, (id_, )))
        sql = """SELECT id FROM Collocation WHERE predicate = (?)"""
        ids1 = list(self.cursor.execute(sql, (id_, )))
        unique_ids = set(*ids0, *ids1)
        return list(unique_ids)

    @api_call
    def get_connection_ids_with_deriv_id(self, id_: DerivativeFormID) -> List[ConnID]:
        # @TODO(hl): Speed
        collocation_ids = self.get_collocation_ids_with_deriv_id(id_)
        result = []
        for id_ in collocation_ids:
            coll_conns = self.get_connection_ids_with_coll_id(id_)
            result.extend(coll_conns)
        return result

    @api_call
    def get_sentences_id_by_deriv_id(self, id_: DerivativeFormID) -> List[SentenceID]:
        # @TODO(hl): Speed
        coll_ids = self.get_collocation_ids_with_deriv_id(id_)
        sql = """SELECT sentence_id FROM Sentence_Collocation_Junction 
                 WHERE collocation_id = (?)"""
        result = []
        for coll_id in coll_ids:
            coll_sent_ids = list(self.cursor.execute(sql, (coll_id, )))
            result.extend(coll_sent_ids)
        return result

    @api_call
    def get_sentences_id_by_word(self, word: str) -> List[SentenceID]:
        sql = """SELECT id FROM Sentence WHERE contents LIKE '%' || ? || '%' """
        sentences = self.cursor.execute(sql, (word,))
        sentences = unwrap(sentences)
        return sentences

    @api_call
    def add_words_if_not_exist(self, words: List[str]):
        derivative_forms = list(map(ling.DerivativeForm.create, words))

        initial_forms = list(map(lambda it: (it.initial_form, ), derivative_forms))
        sql = """INSERT OR IGNORE INTO Initial_Form (form) VALUES (?)"""
        self.cursor.executemany(sql, initial_forms)

        words_reformatted = []
        for derivative_form in derivative_forms:
            sql = """SELECT id FROM Initial_Form WHERE form = (?)"""
            initial_form_id_it = self.cursor.execute(sql, (derivative_form.initial_form, ))
            initial_form_id = next(initial_form_id_it)[0]
            form_sql_data = (derivative_form.form, initial_form_id, derivative_form.part_of_speech.value)
            words_reformatted.append(form_sql_data)

        sql = """INSERT OR IGNORE INTO Derivative_Form (form, initial_form_id, part_of_speech) VALUES (?, ?, ?)"""
        self.cursor.executemany(sql, words_reformatted)
        self.database.commit()

    @api_call
    def add_or_update_sentence_record(self, sent: ling.SentenceCtx):
        self.add_words_if_not_exist(sent.words)
        #
        # add sentence record
        #
        sql = "INSERT OR IGNORE INTO Sentence (contents) VALUES (?)"
        self.cursor.execute(sql, (sent.text, ))

        sql = "SELECT id from Sentence WHERE contents = (?)"
        sentence_id = self.cursor.execute(sql, (sent.text, ))
        sentence_id = next(sentence_id)

        #
        # first of all, delete all previous entries about sentence
        #
        sql = """DELETE FROM Collocation_Junction WHERE collocation_id IN (
                    SELECT collocation_id FROM Sentence_Collocation_Junction 
                    WHERE sentence_id = (?)
                 )"""
        self.cursor.execute(sql, sentence_id)
        sql = """DELETE FROM Collocation WHERE id IN (
                    SELECT collocation_id FROM Sentence_Collocation_Junction 
                    WHERE sentence_id = (?)
                 )"""
        self.cursor.execute(sql, sentence_id)
        sql = """DELETE FROM Sentence_Collocation_Junction WHERE sentence_id = (?)"""
        self.cursor.execute(sql, sentence_id)

        sql = """DELETE FROM Conn WHERE id IN (
                 SELECT conn_id FROM Sentence_Connection_Junction 
                    WHERE sentence_id = (?)
                 )"""
        self.cursor.execute(sql, sentence_id)
        sql = """DELETE FROM Sentence_Connection_Junction WHERE sentence_id = (?)"""
        self.cursor.execute(sql, sentence_id)
        #
        # now start populating database again
        #
        collocation_ids = []
        for idx, collocation in enumerate(sent.collocations):
            sql = """INSERT INTO Collocation (kind) VALUES (?)"""
            self.cursor.execute(sql, (collocation.kind.value, ))
            sql = """SELECT id FROM Collocation
                     WHERE rowid = ( SELECT last_insert_rowid() )"""
            collocation_id = self.cursor.execute(sql)
            collocation_id = next(collocation_id)[0]
            collocation_ids.append(collocation_id)

            sql = """INSERT INTO Collocation_Junction (derivative_form_id, collocation_id, idx)
                     SELECT Derivative_Form.id, (?), (?)
                     FROM Derivative_Form
                     WHERE Derivative_Form.form = (?)
                     """
            words = list(map(lambda it: (collocation_id, it[0], sent.words[it[1]] ), enumerate(collocation.words)))
            print(words)
            self.cursor.executemany(sql, words)

            sql = """INSERT INTO Sentence_Collocation_Junction (sentence_id, collocation_id)
                     VALUES (?, ?)"""
            self.cursor.execute(sql, (sentence_id[0], collocation_id))

        for connection in sent.connections:
            sql = """INSERT INTO Conn (predicate, object) 
                     VALUES(?, ?)
                     """
            conn_collocation_ids = (collocation_ids[connection[0]], collocation_ids[connection[1]])
            self.cursor.execute(sql, conn_collocation_ids)
            sql = """SELECT id FROM Conn
                     WHERE rowid = ( SELECT last_insert_rowid() )"""
            conn_id = self.cursor.execute(sql)
            conn_id = next(conn_id)[0]
            sql = """INSERT INTO Sentence_Connection_Junction (sentence_id, conn_id)
                     VALUES(?, ?)"""
            self.cursor.execute(sql, (sentence_id[0], conn_id))

        self.database.commit()


def test_db_ctx():
    text = "Летчик пилотировал самолет боковой ручкой управления в плохую погоду. Мама мыла Милу мылом."
    text_ctx = ling.TextCtx()
    text_ctx.init_for_text(text)

    sentence1 = text_ctx.start_sentence_edit(10)
    sentence1.add_collocation([0, 1, 2], ling.LingKind.OBJECT)
    sentence1.mark_text_part(20, 40, ling.LingKind.PREDICATE)
    sentence1.make_connection(0, 1)

    db_name = "test.sqlite"

    try:
        ctx = DBCtx()
        ctx.create_or_open(db_name)
        ctx.add_or_update_sentence_record(sentence1)

        word = "ручкой"
        print("--Init of ", word)
        a = ctx.get_initial_form(word)
        print('\n'.join(map(str, a)))

        print("--All inits")
        a = ctx.get_initial_form()
        print('\n'.join(map(str, a)))

        print("--Deriv of", word)
        a = ctx.get_deriv_form(word)
        print('\n'.join(map(str, a)))

        print("--All derivs")
        a = ctx.get_deriv_form()
        print('\n'.join(map(str, a)))

        print("--All collocations")
        a = ctx.get_collocation()
        print('\n'.join(map(str, a)))

        print("--Coll with", word)
        a = ctx.get_collocation(word)
        print('\n'.join(map(str, a)))

        print("--All connections")
        a = ctx.get_connection()
        print('\n'.join(map(str, a)))

        print("--Connection with", word)
        a = ctx.get_connection(word)
        print('\n'.join(map(str, a)))

        print("--All sentence ids")
        a = ctx.get_sentence_id()
        print("\n".join(map(str, a)))

        print("--All sentence texts")
        a = list(map(ctx.get_sentence_text, a))
        print("\n".join(a))

        print("--Sentences with", word)
        a = ctx.get_sentences_by_word(word)
        print("\n".join(map(str, a)))

        ctx.database.close()
    except Exception:
        traceback.print_exc()
    # os.remove(db_name)


if __name__ == "__main__":
    test_db_ctx()