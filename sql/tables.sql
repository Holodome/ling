create table if not exists semantic_group (
    id integer primary key,
    name text not null
);

CREATE TABLE IF NOT EXISTS word (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,

    part_of_speech int NOT NULL,
    initial_form_id integer,
    has_initial_form boolean not null, -- this is not to change every query comparing initial_form_id to null
    CONSTRAINT uniq UNIQUE (
        word
        -- part_of_speech,
        -- initial_form_id
    )
);

CREATE TABLE IF NOT EXISTS collocation (
    id INTEGER PRIMARY KEY,
    semantic_group_id INTEGER NOT NULL,
    word_hash INTEGER NOT NULL, -- see db_model.py

    constraint uniq unique (
        semantic_group_id,
        word_hash
    ),

    FOREIGN KEY(semantic_group_id) REFERENCES semantic_group(id)
);

CREATE TABLE IF NOT EXISTS collocation_junction (
    idx INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    collocation_id INTEGER NOT NULL,
    CONSTRAINT pk PRIMARY KEY (
        idx,
        word_id,
        collocation_id
    ),

    FOREIGN KEY(word_id) REFERENCES word(id),
    FOREIGN KEY(collocation_id) REFERENCES collocation(id)
);

CREATE TABLE IF NOT EXISTS conn ( -- connection, but it is reserved
    id INTEGER PRIMARY KEY,
    predicate INTEGER NOT NULL,
    object INTEGER NOT NULL,

    CONSTRAINT uniq UNIQUE (
        predicate,
        object
    ),

    FOREIGN KEY(predicate) REFERENCES collocation(id),
    FOREIGN KEY(object) REFERENCES collocation(id)
);

CREATE TABLE IF NOT EXISTS sentence (
    id INTEGER PRIMARY KEY,
    contents TEXT NOT NULL UNIQUE,
    word_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sentence_collocation_junction (
    sentence_id INTEGER NOT NULL,
    collocation_id INTEGER NOT NULL,
    CONSTRAINT pk PRIMARY KEY (
       sentence_id,
       collocation_id
    ),

    FOREIGN KEY(sentence_id) REFERENCES sentence(id),
    FOREIGN KEY(collocation_id) REFERENCES collocation(id)
);

CREATE TABLE IF NOT EXISTS sentence_connection_junction (
    sentence_id INTEGER NOT NULL,
    conn_id INTEGER NOT NULL,
    CONSTRAINT pk PRIMARY KEY (
       sentence_id,
       conn_id
    ),

    FOREIGN KEY(sentence_id) REFERENCES sentence(id),
    FOREIGN KEY(conn_id) REFERENCES conn(id)
);

CREATE TABLE IF NOT EXISTS sentence_word_junction (
    sentence_id INTEGER NOT NULL,
    word_id   INTEGER NOT NULL,
    idx      INTEGER NOT NULL,
    text_idx INTEGER NOT NULL, -- index in sentence text
    CONSTRAINT pk PRIMARY KEY (
        sentence_id,
        word_id,
        idx
    ),

    FOREIGN KEY(sentence_id) REFERENCES sentence(id),
    FOREIGN KEY(word_id) REFERENCES word(id)
);
