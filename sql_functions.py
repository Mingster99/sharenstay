import sqlalchemy
from typing import Dict
import json

# ? A dictionary containing
data_types = {
    'boolean': 'BOOL',
    'integer': 'INT',
    'text': 'TEXT',
    'time': 'TIME',
}
    
def generate_table_return_result(res):
    # ? An empty Python list to store the entries/rows/tuples of the relation/table
    rows = []

    # ? keys of the SELECT query result are the columns/fields of the table/relation
    columns = list(res.keys())

    # ? Constructing the list of tuples/rows, basically, restructuring the object format
    for row_number, row in enumerate(res):
        rows.append({})
        for column_number, value in enumerate(row):
            rows[row_number][columns[column_number]] = value

    # ? JSON object with the relation data
    output = {}
    output["columns"] = columns  # ? Stores the fields
    output["rows"] = rows  # ? Stores the tuples

    """
        The returned object format:
        {
            "columns": ["a","b","c"],
            "rows": [
                {"a":1,"b":2,"c":3},
                {"a":4,"b":5,"c":6}
            ]
        }
    """
    # ? Returns the stringified JSON object
    return json.dumps(output, default=str)


def generate_delete_statement(details: Dict):
    # ? Fetches the entry id for the table name
    table_name = details["relationName"]
    id = details["deletionId"]
    # ? Generates the deletion query for the given entry with the id
    statement = f"DELETE FROM {table_name} WHERE id={id};"
    return sqlalchemy.text(statement)


def generate_update_table_statement(update: Dict):

    # ? Fetching the table name, entry/tuple id and the update body
    table_name = update["name"]
    id = update["id"]
    body = update["body"]

    # ? Default for the SQL update statement
    statement = f"UPDATE {table_name} SET "
    # ? Constructing column-to-value maps looping
    for key, value in body.items():
        statement += f"{key}=\'{value}\',"

    # ?Finalizing the update statement with table and row details and returning
    statement = statement[:-1]+f" WHERE {table_name}.id={id};"
    return sqlalchemy.text(statement)


def generate_insert_table_statement(insertion: Dict):
    # ? Fetching table name and the rows/tuples body object from the request
    table_name = insertion["name"]
    body = insertion["body"]
    valueTypes = insertion["valueTypes"]

    # ? Generating the default insert statement template
    statement = f"INSERT INTO {table_name}  "

    # ? Appending the entries with their corresponding columns
    column_names = "("
    column_values = "("
    for key, value in body.items():
        column_names += (key+",")
        if valueTypes[key] == "TEXT" or valueTypes[key] == "TIME":
            column_values += (f"\'{value}\',")
        else:
            column_values += (f"{value},")

    # ? Removing the last default comma
    column_names = column_names[:-1]+")"
    column_values = column_values[:-1]+")"

    # ? Combining it all into one statement and returning
    #! You may try to expand it to multiple tuple insertion in another method
    statement = statement + column_names+" VALUES "+column_values+";"
    return sqlalchemy.text(statement)


def generate_create_table_statement(table: Dict):
    # ? First key is the name of the table
    table_name = table["name"]
    # ? Table body itself is a JSON object mapping field/column names to their values
    table_body = table["body"]
    # ? Default table creation template query is extended below. Note that we drop the existing one each time. You might improve this behavior if you will
    # ! ID is the case of simplicity
    statement = f"DROP TABLE IF EXISTS {table_name}; CREATE TABLE {table_name} (id serial NOT NULL PRIMARY KEY,"
    # ? As stated above, column names and types are appended to the creation query from the mapped JSON object
    for key, value in table_body.items():
        statement += (f"{key}"+" "+f"{value}"+",")
    # ? closing the final statement (by removing the last ',' and adding ');' termination and returning it
    statement = statement[:-1] + ");"
    return sqlalchemy.text(statement)

# Function to create simple SELECT * FROM _ WHERE _ = _
def generate_select_from_table_query(ls):
    # ls will be in the format:
    #   [<table>, <col_to_select>, <value to check>]
    table_name = ls[0]
    table_col = ls[1]
    value_checked = ls[2]
    statement = f"SELECT * FROM {table_name} WHERE {table_col} = '{value_checked}';"
    return sqlalchemy.text(statement)

def generate_get_particular_value_from_table_query(ls):
    # ls will be in the format:
    #   [<table>, <col_to get value>, <col_to_select>, <value to check>]
    table_name = ls[0]
    table_col_retrieve = ls[1]
    table_col_filter = ls[2]
    value_checked = ls[3]
    statement = f"SELECT {table_col_retrieve} FROM {table_name} WHERE {table_col_filter} = '{value_checked}';"
    return sqlalchemy.text(statement)

def generate_distinct_values_from_column(ls):
    table_name = ls[0]
    table_col = ls[1]
    statement = f"SELECT DISTINCT {table_col} FROM {table_name};"
    return sqlalchemy.text(statement)

# Usable in admin page
def generate_count_of_classes_from_column(ls):
    table_name = ls[0]
    table_col = ls[1]
    statement = f"SELECT {table_col}, COUNT(*) FROM {table_name} GROUP BY {table_col};"
    return sqlalchemy.text(statement)

def generate_total_count_from_column(ls):
    table_name = ls[0]
    table_col = ls[1]
    statement = f"SELECT COUNT(*) FROM {table_name};"
    return sqlalchemy.text(statement)

def generate_total_of_type(ls):
    table_name = ls[0]
    table_col = ls[1]
    value_checked = ls[2]
    statement = f"SELECT COUNT(*) FROM {table_name} WHERE {table_col} = {value_checked};"
    return sqlalchemy.text(statement)

def generate_max_val_of_col(ls):
    table_name = ls[0]
    table_col = ls[1]
    statement = f"SELECT MAX({table_col}) FROM {table_name};"
    return sqlalchemy.text(statement)

# Return all resuts that have the top n of a column
def generate_top_n_by_col(ls):
    table_name = ls[0]
    table_col = ls[1]
    n = ls[2]
    if table_col and n:
        subquery1 = f"SELECT DISTINCT {table_col} FROM {table_name} WHERE {table_col} IS NOT NULL ORDER BY {table_col} DESC LIMIT {n}"
        statement = f"SELECT * FROM {table_name} a NATURAL JOIN ({subquery1}) b LIMIT 50;" 
        return sqlalchemy.text(statement)
    else:
        return sqlalchemy.text(f"SELECT * FROM {table_name} LIMIT 50;")

"SELECT * FROM sharenstay a NATURAL JOIN (SELECT * FROM sharenstay LIMIT 50) b ON "

def generate_avg_val_of_col(ls):
    table_name = ls[0]
    table_col = ls[1]
    column_checked = ls[2]
    value_checked = ls[3]
    statement = f"SELECT AVG({table_col}) FROM {table_name} WHERE {column_checked} = {value_checked};"
    return sqlalchemy.text(statement)

def update_val_of_col(ls):
    table_name = ls[0]
    table_col = ls[1]
    value_changed = ls[2]
    column_checked = ls[3]
    value_checked = ls[4]

    statement = f"UPDATE {table_name} SET {table_col} = {value_changed} WHERE {column_checked} = {value_checked};"
    return sqlalchemy.text(statement)