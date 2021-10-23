CREATE TABLE IF NOT EXISTS Initial_Form (
    id INTEGER PRIMARY KEY,
    form TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Derivative_Form (
    id INTEGER PRIMARY KEY,
    initial_form_id INTEGER NOT NULL,
    form TEXT NOT NULL,
    part_of_speech int NOT NULL,
    -- this table can be populated with all word parameters there can exist - like type of speech, sex etc.
    FOREIGN KEY(initial_form_id) REFERENCES Initial_Form (id)
);

CREATE TABLE IF NOT EXISTS Collocation (
    id INTEGER PRIMARY KEY,
    kind INTEGER NOT NULL -- ling kind
);

CREATE TABLE IF NOT EXISTS Collocation_Junction (
    idx INTEGER NOT NULL,
    derivative_form_id INTEGER NOT NULL,
    collocation_id INTEGER NOT NULL,
    CONSTRAINT pk PRIMARY KEY (
        idx,
        derivative_form_id,
        collocation_id
    ),

    FOREIGN KEY(derivative_form_id) REFERENCES Derivative_Form(id),
    FOREIGN KEY(collocation_id) REFERENCES Collocation(id)
);

CREATE TABLE IF NOT EXISTS Conn ( -- connection, but it is reserved
    id INTEGER PRIMARY KEY,
    predicate INTEGER NOT NULL,
    object INTEGER NOT NULL,

    FOREIGN KEY(predicate) REFERENCES Collocation(id),
    FOREIGN KEY(object) REFERENCES Collocation(id)
);

CREATE TABLE IF NOT EXISTS Sentence (
    id INTEGER PRIMARY KEY,
    contents TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Sentence_Collocation_Junction (
    sentence_id INTEGER NOT NULL,
    collocation_id INTEGER NOT NULL,
    CONSTRAINT pk PRIMARY KEY (
       sentence_id,
       collocation_id
    ),

    FOREIGN KEY(sentence_id) REFERENCES Sentence(id),
    FOREIGN KEY(collocation_id) REFERENCES Collocation(id)
);

CREATE TABLE IF NOT EXISTS Sentence_Connection_Junction (
    sentence_id INTEGER NOT NULL,
    conn_id INTEGER NOT NULL,
    CONSTRAINT pk PRIMARY KEY (
       sentence_id,
       conn_id
    ),

    FOREIGN KEY(sentence_id) REFERENCES Sentence(id),
    FOREIGN KEY(conn_id) REFERENCES Conn(id)
);