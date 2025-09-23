USE dataengine;

CREATE TABLE IF NOT EXISTS t_operator
(
  id          varchar(64),
  name        varchar(64),
  description varchar(256),
  language    varchar(256),
  version     varchar(256),
  modal       varchar(256),
  inputs      varchar(256),
  outputs     varchar(256),
  runtime     text,
  settings    text,
  file_name   text,
  is_star     bool,
  create_at   timestamp,
  update_at   timestamp
);

CREATE TABLE IF NOT EXISTS t_operator_category
(
  id        int primary key auto_increment,
  name      varchar(64),
  type      varchar(64),
  parent_id int
);

CREATE TABLE IF NOT EXISTS t_operator_category_relation
(
  id int primary key auto_increment,
  category_id int,
  operator_id varchar(64)
);

