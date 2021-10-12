import os
import sqlite3
from ling import *
import dataclasses
import pymorphy2


@dataclasses.dataclass
class DBCtx:
    filename: str = ""
    database: sqlite3.Connection = None
    cursor: sqlite3.Cursor = None

    def open_from(self, filename):
        self.filename = filename
        self.database = sqlite3.connect(filename)
        self.cursor = self.database.cursor()

    def create_tables(self):
        tables_create_query = open("sql/tables.sql").read()
        self.cursor.executescript(tables_create_query)
        self.database.commit()

    def create_new(self, filename):
        self.filename = filename
        self.database = sqlite3.connect(filename)
        self.cursor = self.database.cursor()
        self.create_tables()

    def create_or_open(self, filename):
        if os.path.exists(filename):
            return self.open_from(filename)
        return self.create_new(filename)

    def add_words_if_not_exist(self, words: List[str]):
        sql = """INSERT OR IGNORE INTO Derivative_Form (form, initial_form_id) VALUES (?, ?)"""
        words_reformatted = list(map(lambda it: (it, 1), words))
        self.cursor.executemany(sql, words_reformatted)
        self.database.commit()

        # sql = "SELECT form FROM Derivative_Form WHERE form IN (%s)" % ", ".join("?" * len(words))
        sql = "SELECT form FROM Derivative_Form"
        # query = self.cursor.execute(sql, words)
        query = self.cursor.execute(sql)
        print(*query)

    def add_or_update_sentence_record(self, sent: SentenceCtx):
        self.add_words_if_not_exist(sent.words)
        #
        # add sentence record
        #
        sql = "INSERT OR IGNORE INTO Sentence (text) VALUES (?)"
        self.cursor.execute(sql, (sent.text, ))

        sql = "SELECT id from Sentence WHERE TEXT = (?)"
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
        for collocation in sent.collocations:
            sql = """INSERT INTO Collocation (kind) VALUES (?)"""
            self.cursor.execute(sql, (collocation.kind.value, ))
            sql = """SELECT id FROM Collocation
                     WHERE rowid = ( SELECT last_insert_rowid() )"""
            collocation_id = self.cursor.execute(sql)
            collocation_id = next(collocation_id)[0]
            collocation_ids.append(collocation_id)

            sql = """INSERT INTO Collocation_Junction (derivative_form_id, collocation_id)
                     SELECT Derivative_Form.id, ? 
                     FROM Derivative_Form
                     WHERE Derivative_Form.form = (?)
                     """
            words = list(map(lambda it: (collocation_id, sent.words[it],), collocation.words))
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

    def get_all_word_forms(self, word):
        ...

    def get_initial_form(self, word):
        ...

    def get_all_collocations_with_word(self, word: str):
        ...

    def get_all_connections_with_word(self, word: str):
        ...

    def get_all_words_collocated_with(self, word):
        ...

    def get_all_words_connected_with(self, word):
        ...


def test_db_ctx():
    text = "Летчик пилотировал самолет боковой ручкой управления в плохую погоду. Мама мыла Милу мылом."
    text_ctx = TextCtx()
    text_ctx.init_for_text(text)

    sentence1 = text_ctx.start_sentence_edit(10)
    sentence1.add_collocation([0, 1, 2], LingKind.OBJECT)
    sentence1.mark_text_part(20, 40, LingKind.PREDICATE)
    sentence1.make_connection(0, 1)

    ctx = DBCtx()
    ctx.create_or_open("db.sqlite")
    ctx.add_or_update_sentence_record(sentence1)

    ctx.database.close()


if __name__ == "__main__":
    test_db_ctx()
