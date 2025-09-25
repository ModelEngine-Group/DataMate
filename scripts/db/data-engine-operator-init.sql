USE dataengine;

CREATE TABLE IF NOT EXISTS t_operator
(
  id          varchar(64) primary key,
  name        varchar(64),
  description varchar(256),
  version     varchar(256),
  inputs      varchar(256),
  outputs     varchar(256),
  runtime     text,
  settings    text,
  file_name   text,
  is_star     bool,
  created_at   timestamp default current_timestamp,
  updated_at   timestamp default current_timestamp
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

CREATE OR REPLACE VIEW v_operator AS
SELECT
  o.id AS operator_id,
  o.name AS operator_name,
  description,
  version,
  inputs,
  outputs,
  runtime,
  settings,
  is_star,
  created_at,
  updated_at,
  toc.id AS category_id,
  toc.name AS category_name
FROM t_operator_category_relation tocr
LEFT JOIN t_operator o ON tocr.operator_id = o.id
LEFT JOIN t_operator_category toc ON tocr.category_id = toc.id;

INSERT IGNORE INTO t_operator_category(id, name, type, parent_id) VALUES
(1, 'modal', 'predefined', 0),
(2, 'language', 'predefined', 0),
(3, 'text', 'predefined', 1),
(4, 'image', 'predefined', 1),
(5, 'audio', 'predefined', 1),
(6, 'video', 'predefined', 1),
(7, 'multimodal', 'predefined', 1),
(8, 'python', 'predefined', 2),
(9, 'java', 'predefined', 2);

INSERT IGNORE INTO t_operator
  (id, name, description, version, inputs, outputs, runtime, settings, file_name, is_star) VALUES
('TestOp1', 'TestOp1', '', '1.0.0', 'text', 'text', '', '', '', false),
('TestOp2', 'TestOp2', '', '1.0.0', 'text', 'text', '', '', '', false),
('TestOp3', 'TestOp3', '', '1.0.0', 'text', 'text', '', '', '', false);

INSERT IGNORE INTO t_operator_category_relation(category_id, operator_id) VALUES
(3, 'TestOp1'),
(3, 'TestOp2'),
(3, 'TestOp3'),
(8, 'TestOp1'),
(8, 'TestOp2'),
(9, 'TestOp3');
