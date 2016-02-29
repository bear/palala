create table if not exists domains (
  domain  varchar primary key,
  created varchar,
  updated varchar
);

create table if not exists posts (
  postid  varchar(36) primary key,
  domain  varchar,
  source  varchar,
  target  varchar,
  created varchar,
  updated varchar
);