create table if not exists semantic_group (
    id integer primary key,
    name text not null
);

create table if not exists word (
    id integer primary key,
    word TEXT not null,

    part_of_speech int not null,
    initial_form_id integer,
    has_initial_form boolean not null, -- this is not to change every query comparing initial_form_id to null
    constraint uniq UNIQUE (
        word
        -- part_of_speech,
        -- initial_form_id
    )
);

create table if not exists collocation (
    id integer primary key,
    sg_id integer not null,
    word_hash text not null,
    words_text text not null,

    constraint uniq unique (
        sg_id,
        word_hash
    ),

    foreign key(sg_id) references semantic_group(id)
);

create table if not exists collocation_junction (
    idx integer not null,
    word_id integer not null,
    col_id integer not null,
    constraint pk primary key (
        idx,
        word_id,
        col_id
    ),

    foreign key(word_id) references word(id),
    foreign key(col_id) references collocation(id)
);

create table if not exists conn ( -- connection, but it is reserved
    id integer primary key,
    predicate integer not null,
    object integer not null,

    constraint uniq UNIQUE (
        predicate,
        object
    ),

    foreign key(predicate) references collocation(id),
    foreign key(object) references collocation(id)
);

create table if not exists sentence (
    id integer primary key,
    contents TEXT not null UNIQUE
);

create table if not exists sentence_collocation_junction (
    sent_id integer not null,
    col_id integer not null,
    constraint pk primary key (
       sent_id,
       col_id
    ),

    foreign key(sent_id) references sentence(id),
    foreign key(col_id) references collocation(id)
);

create table if not exists sentence_connection_junction (
    sent_id integer not null,
    con_id integer not null,
    constraint pk primary key (
       sent_id,
       con_id
    ),

    foreign key(sent_id) references sentence(id),
    foreign key(con_id) references conn(id)
);

create table if not exists sentence_word_junction (
    sent_id integer not null,
    word_id   integer not null,
    idx      integer not null,
    text_idx integer not null, -- index in sentence text
    constraint pk primary key (
        sent_id,
        word_id,
        idx
    ),

    foreign key(sent_id) references sentence(id),
    foreign key(word_id) references word(id)
);
