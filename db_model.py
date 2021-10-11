import os
import sqlite3
from ling import *
import dataclasses
import pymorphy2


@dataclasses.dataclass
class DBCtx:
    filename: str = ""
    database: sqlite3.Connection = None
    # cursor: sqlite3.Cursor = None

    def open_from(self, filename):
        self.filename = filename
        self.database = sqlite3.connect(filename)

    def create_tables(self):
        tables_create_query = \
            """CREATE TABLE Initial_Form (
    id INTEGER PRIMARY KEY,
    form TEXT NOT NULL UNIQUE
);

CREATE TABLE Derivative_Form (
    id INTEGER PRIMARY KEY,
    initial_form_id INTEGER NOT NULL, 
    form TEXT NOT NULL,
    FOREIGN KEY(initial_form_id) REFERENCES Initial_Form (id)
);

CREATE TABLE Collocation (
    id INTEGER PRIMARY KEY, 
    kind INTEGER NOT NULL -- ling kind
);

CREATE TABLE Collocation_Junction (
    derivative_form_id INTEGER NOT NULL, 
    collocation_id INTEGER NOT NULL, 
    CONSTRAINT pk PRIMARY KEY (
        derivative_form_id,
        collocation_id
    ), 
    
    FOREIGN KEY(derivative_form_id) REFERENCES Derivative_Form(id),
    FOREIGN KEY(collocation_id) REFERENCES Collocation(id)
);

CREATE TABLE Conn ( -- connection, but it is reserved
    id INTEGER PRIMARY KEY, 
    predicate INTEGER NOT NULL, 
    object INTEGER NOT NULL,
                         
    FOREIGN KEY(predicate) REFERENCES Collocation(id),
    FOREIGN KEY(object) REFERENCES Collocation(id)
);

CREATE TABLE Sentence (
    id INTEGER PRIMARY KEY,
    text TEXT NOT NULL
);

CREATE TABLE Sentence_Collocation_Junction (
    sentence_id INTEGER NOT NULL,
    collocation_id INTEGER NOT NULL,
    CONSTRAINT pk PRIMARY KEY (
       sentence_id,
       collocation_id                       
    ),

    FOREIGN KEY(sentence_id) REFERENCES Sentence(id),
    FOREIGN KEY(collocation_id) REFERENCES Collocation(id)
);
            
CREATE TABLE Sentence_Connection_Junction (
    sentence_id INTEGER NOT NULL,
    conn_id INTEGER NOT NULL,
    CONSTRAINT pk PRIMARY KEY (
       sentence_id,
       conn_id                       
    ),

    FOREIGN KEY(sentence_id) REFERENCES Sentence(id),
    FOREIGN KEY(conn_id) REFERENCES Conn(id)
);"""
        cursor = self.database.cursor()
        cursor.executescript(tables_create_query)
        self.database.commit()
        cursor.close()

    def create_new(self, filename):
        self.filename = filename
        self.database = sqlite3.connect(filename)
        self.create_tables()

    def create_or_open(self, filename):
        if os.path.exists(filename):
            return self.open_from(filename)
        return self.create_new(filename)

    def add_words_if_not_exist_and_return_their_ids(self, words: List[str]):
        cursor = self.database.cursor()
        sql = """INSERT OR IGNORE INTO Initial_Form (form) VALUES (?)"""
        cursor.executemany(sql, words)
        self.database.commit()
        cursor.close()

        sql = "SELECT id FROM Initial_Form WHERE form IN (%s)" % ", ".join("?" * len(words))
        cursor = self.database.cursor()
        query = cursor.execute(sql, words)
        result = list(map(lambda it: it[0], query))
        cursor.close()

        return result

    def add_sentence_record(self, sent: SentenceCtx):
        # add words
        ...


def test_db_ctx():
    ctx = DBCtx()
    ctx.create_or_open("db.sqlite")
    ctx.add_words_if_not_exist_and_return_their_ids(["A", "B", "C", "A"])

    ctx.database.close()


if __name__ == "__main__":
    test_db_ctx()
