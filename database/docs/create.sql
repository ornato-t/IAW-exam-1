BEGIN TRANSACTION;

CREATE TABLE VISIT (
    date DATE NOT NULL,
    time INTEGER CHECK(time IN (1, 2, 3, 4)),
    virtual BOOLEAN NOT NULL,
    status TEXT CHECK(status IN ('pending', 'accepted', 'rejected')),
    refusal_reason TEXT,
    PRIMARY KEY (date, time)
);
CREATE TABLE PERSON (
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    landlord BOOLEAN NOT NULL,
    PRIMARY KEY (username)
);
CREATE TABLE PICTURES (
    path TEXT NOT NULL,
    ADVERTISEMENT_id INTEGER NOT NULL,
    PRIMARY KEY (path),
    FOREIGN KEY (ADVERTISEMENT_id) REFERENCES ADVERTISEMENT(id)
);
CREATE TABLE ADVERTISEMENT (
    id INTEGER PRIMARY KEY,
    adress TEXT NOT NULL,
    title TEXT NOT NULL,
    rooms INTEGER CHECK(rooms IN (1, 2, 3, 4, 5, 6)),
    type TEXT CHECK(type IN ('detached', 'flat', 'loft', 'villa')),
    description TEXT NOT NULL,
    rent REAL NOT NULL,
    furniture BOOLEAN NOT NULL,
    available BOOLEAN NOT NULL,
    landlord_username TEXT NOT NULL,
    FOREIGN KEY (landlord_username) REFERENCES PERSON(username)
);
CREATE TABLE PERSON_VISITS (
    VISIT_date DATE NOT NULL,
    VISIT_time INTEGER NOT NULL,
    visitor_username TEXT NOT NULL,
    ADVERTISEMENT_id INTEGER NOT NULL,
    PRIMARY KEY (VISIT_date, VISIT_time, visitor_username, ADVERTISEMENT_id),
    FOREIGN KEY (VISIT_date) REFERENCES VISIT(date),
    FOREIGN KEY (VISIT_time) REFERENCES VISIT(time),
    FOREIGN KEY (visitor_username) REFERENCES PERSON(username),
    FOREIGN KEY (ADVERTISEMENT_id) REFERENCES ADVERTISEMENT(id)
);

COMMIT;