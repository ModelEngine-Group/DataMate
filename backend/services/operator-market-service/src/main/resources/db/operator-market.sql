CREATE TABLE "operator_label"
(
    "id"   serial NOT NULL UNIQUE,
    "name" varchar(255),
    PRIMARY KEY ("id")
);


CREATE TABLE "category"
(
    "id"        serial NOT NULL UNIQUE,
    "name"      varchar(255),
    "type"      varchar(255),
    "parent_id" int,
    PRIMARY KEY ("id")
);


CREATE TABLE "operator"
(
    "id"   serial NOT NULL UNIQUE,
    "name" varchar(255),
    PRIMARY KEY ("id")
);


CREATE TABLE "operator_label_relation"
(
    "operator_id" int NOT NULL,
    "label_id"    int NOT NULL,
    PRIMARY KEY ("operator_id", "label_id")
);


CREATE TABLE "operator_category"
(
    "operator_id" serial NOT NULL UNIQUE,
    "category_id" int    NOT NULL,
    PRIMARY KEY ("operator_id", "category_id")
);


ALTER TABLE "operator_category"
    ADD FOREIGN KEY ("operator_id") REFERENCES "operator" ("id")
        ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "operator_label_relation"
    ADD FOREIGN KEY ("operator_id") REFERENCES "operator" ("id")
        ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "operator_label_relation"
    ADD FOREIGN KEY ("label_id") REFERENCES "operator_label" ("id")
        ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "operator_category"
    ADD FOREIGN KEY ("category_id") REFERENCES "category" ("id")
        ON UPDATE NO ACTION ON DELETE NO ACTION;
