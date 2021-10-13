import os
import sqlite3
import traceback
from typing import Union

from ling import *
import dataclasses


@dataclasses.dataclass
class DBCtx:
    filename: str = ""
    database: sqlite3.Connection = None
    cursor: sqlite3.Cursor = None

    def create_tables(self):
        tables_create_query = open("sql/tables.sql").read()
        self.cursor.executescript(tables_create_query)
        self.database.commit()

    def create_or_open(self, filename):
        self.filename = filename
        self.database = sqlite3.connect(filename)
        self.cursor = self.database.cursor()
        self.create_tables()

    def add_words_if_not_exist(self, words: List[str]):
        derivative_forms = list(map(DerivativeForm.create, words))

        initial_forms = list(map(lambda it: (it.initial_form, ), derivative_forms))
        sql = """INSERT OR IGNORE INTO Initial_Form (form) VALUES (?)"""
        self.cursor.executemany(sql, initial_forms)
        #
        # sql = """SELECT id FROM Initial_Form WHERE form IN (%s)""" % ", ".join("?" * len(words))
        # initial_form_ids = self.cursor.execute(sql, list(map(lambda it: it[0], initial_forms)))
        # initial_form_ids = [it[0] for it in initial_form_ids]

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
            words = list(map(lambda it: (collocation_id, sent.words[it[1]], it[0]), enumerate(collocation.words)))
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

    def get_deriv_form(self, word: Union[str, None] = None):
        sql = """SELECT form, initial_form_id, part_of_speech FROM Derivative_Form"""
        if word is not None:
            sql += " WHERE form = (?)"
            deriv = self.cursor.execute(sql, (word, ))
        else:
            deriv = self.cursor.execute(sql)

        deriv_forms = []
        parts_of_speech = []
        init_ids = []
        for d in deriv:
            deriv_forms.append(d[0])
            init_ids.append(d[1])
            parts_of_speech.append(d[2])

        derivs = []
        for deriv_form, part_of_speech in zip(deriv_forms, parts_of_speech):
            init_form = self.get_initial_form(deriv_form)
            d = DerivativeForm.from_deserialized(deriv_form, init_form[0], part_of_speech)
            derivs.append(d)
        return derivs

    def get_initial_form(self, word: Union[str, None] = None):
        sql = """SELECT initial_form_id FROM Derivative_Form"""
        if word is not None:
            sql += " WHERE form = (?)"
            init_id = self.cursor.execute(sql, (word, ))
        else:
            init_id = self.cursor.execute(sql)
        init_id = list(map(lambda it: it[0], init_id))
        sql = """SELECT form FROM Initial_Form WHERE id IN (%s)""" % ", ".join("?" * len(init_id))
        form_it = self.cursor.execute(sql, init_id)
        form = list(map(lambda it: it[0], form_it))

        return form

    def get_all_collocations(self, word: Union[str, None] = None):
        ...

    def get_all_connections(self, word: Union[str, None] = None):
        ...


def test_db_ctx():
    text = "Летчик пилотировал самолет боковой ручкой управления в плохую погоду. Мама мыла Милу мылом."
    text_ctx = TextCtx()
    text_ctx.init_for_text(text)

    sentence1 = text_ctx.start_sentence_edit(10)
    sentence1.add_collocation([0, 1, 2], LingKind.OBJECT)
    sentence1.mark_text_part(20, 40, LingKind.PREDICATE)
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

        ctx.database.close()
    except Exception:
        traceback.print_exc()
    os.remove(db_name)


if __name__ == "__main__":
    test_db_ctx()