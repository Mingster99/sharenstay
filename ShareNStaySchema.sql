/*******************

  Create the schema

********************/

CREATE TABLE IF NOT EXISTS sharenstay(
   id                             VARCHAR(18) NOT NULL PRIMARY KEY
  ,name                           VARCHAR(245) NOT NULL
  ,host_id                        INTEGER  NOT NULL
  ,host_name                      VARCHAR(35) NOT NULL
  ,neighbourhood_group            VARCHAR(17) NOT NULL
  ,neighbourhood                  VARCHAR(23) NOT NULL
  ,room_type                      VARCHAR(15) NOT NULL
  ,price                          INTEGER  NOT NULL
  ,minimum_nights                 INTEGER  NOT NULL
  ,number_of_reviews              INTEGER  NOT NULL
  ,reviews_per_month              NUMERIC(5,2)
  ,calculated_host_listings_count INTEGER  NOT NULL
  ,number_of_reviews_ltm          INTEGER  NOT NULL
  ,license                        VARCHAR(29)
);