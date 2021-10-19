import os
import sqlite3
import traceback
from typing import Union

from ling import *
import dataclasses


def flatten_by_idx(arr, idx):
    return list(map(lambda it: it[idx], arr))


def unwrap(x):
    return flatten_by_idx(x, 0)


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
        init_id = flatten_by_idx(init_id, 0)
        sql = """SELECT form FROM Initial_Form WHERE id IN (%s)""" % ", ".join("?" * len(init_id))
        form_it = self.cursor.execute(sql, init_id)
        form = flatten_by_idx(form_it, 0)

        return form

    def get_collocation_ids(self, word: Union[str, None] = None):
        sql = """SELECT DISTINCT collocation_id FROM Collocation_Junction"""
        if word is not None:
            sql += """ WHERE derivative_form_id IN (
                        SELECT id FROM Derivative_Form 
                        WHERE form = (?)
                    )"""
            col_ids = self.cursor.execute(sql, (word,))
        else:
            col_ids = self.cursor.execute(sql)
        col_ids = unwrap(col_ids)
        return col_ids

    def get_collocation_by_id(self, col_id):
        sql = """SELECT f.form, j.idx FROM Derivative_Form f
                             INNER JOIN Collocation_Junction j 
                             ON f.id = j.derivative_form_id 
                             WHERE j.collocation_id = (?)"""
        derivative_forms = self.cursor.execute(sql, (col_id,))
        derivative_forms = list(derivative_forms)
        derivative_forms.sort(key=lambda it: it[1])
        derivative_forms = unwrap(derivative_forms)

        deriv_structs = []
        for form in derivative_forms:
            ds = self.get_deriv_form(form)
            assert ds
            deriv_structs.append(ds[0])
        return deriv_structs

    def get_collocation(self, word: Union[str, None] = None):
        col_ids = self.get_collocation_ids(word)

        result = []
        for col_id in col_ids:
            deriv_structs = self.get_collocation_by_id(col_id)
            result.append(deriv_structs)

        return result

    def get_connection(self, word: Union[str, None] = None):
        col_ids = self.get_collocation_ids(word)
        col_ids_fmt = ",".join("?" * len(col_ids))
        sql = """SELECT id, predicate, object FROM Conn"""
        if word is not None:
            sql += """ WHERE predicate in (%s)
               OR object in (%s)""" % (col_ids_fmt, col_ids_fmt)
            conn_ids = self.cursor.execute(sql, [*col_ids, *col_ids])
        else:
            conn_ids = self.cursor.execute(sql)

        result = []

        conn_ids = list(conn_ids)
        for conn_id, pred_id, obj_id in conn_ids:
            pred_conn = self.get_collocation_by_id(pred_id)
            obj_conn = self.get_collocation_by_id(obj_id)
            conn_info = (pred_conn, obj_conn)
            result.append(conn_info)

        return result

    def get_sentence_words(self):
        ...

    def get_sentence_text(self, sent_id: int):
        sql = """SELECT contents from Sentence WHERE id = (?)"""
        sentences = self.cursor.execute(sql, (sent_id, ))
        result = next(sentences)[0]
        return result

    def get_sentence_collocations(self, sent_id):
        sql = """SELECT collocation_id FROM Sentence_Colloction_Junction
                 WHERE sentence_id = (?)"""
        collocation_ids = self.cursor.execute(sql, (sent_id, ))
        collocation_ids = unwrap(collocation_ids)
        return collocation_ids

    def get_sentence_connections(self, sent_id):
        sql = """SELECT connection_id FROM Sentence_Connection_Junction
                 WHERE sentence_id = (?)"""
        conn_ids = self.cursor.execute(sql, (sent_id, ))
        conn_ids = unwrap(conn_ids)
        return conn_ids

    def get_sentences_by_word(self, word: str):
        # @TODO(hl): Should this go through the DerivativeForm?
        sql = """SELECT id FROM Sentence WHERE contents LIKE '%' || ? || '%' """
        sentences = self.cursor.execute(sql, (word, ))
        sentences = unwrap(sentences)
        return sentences

    def get_sentence_id(self, text: Union[str, None] = None):
        sql = """SELECT id, contents FROM Sentence"""
        if text is not None:
            sql += """ WHERE text in (?)"""
            sent_ids = self.cursor.execute(sql, (text, ))
        else:
            sent_ids = self.cursor.execute(sql)
        sent_ids = unwrap(sent_ids)
        return sent_ids


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