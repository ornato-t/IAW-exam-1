BEGIN TRANSACTION;

INSERT INTO PERSON(username, email, password, name, landlord)
VALUES('admin', 'admin@example.com', 'password', 'admin', true);

INSERT INTO ADVERTISEMENT(adress, title, rooms, type, description, rent, furniture, available, landlord_username)
VALUES
    ('Via Roma 1', 'Casa n.1', 3, 'detached', 'Splendida casa unifamiliare in pieno centro.', 800, true, true, 'admin'),
    ('Via Cavour 8', 'Casa n.2', 3, 'flat', 'Grazioso monolocale con servizi accessibili', 300, true, true, 'admin'),
    ('Corso Moncalieri 15', 'Casa n.3', 3, 'villa', 'Sfarzosa villa con ampio giardino.', 3000, true, true, 'admin'),
    ('Via XX Settembre 20', 'Casa n.4', 3, 'loft', 'Ex immobile industriale, recentemente ammodernato', 1200, false, true, 'admin');

INSERT INTO PICTURES(path, ADVERTISEMENT_id)
VALUES('1.jpg', 1), ('2.jpg', 2), ('3.jpg', 3), ('4.jpg', 4);

COMMIT;