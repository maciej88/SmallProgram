CREATE TABLE Messages (
    id integer NOT NULL,
    from_id integer,
    to_id integer,
    text text,
    creation_date date
);