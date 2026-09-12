from slgbot.database import database_schema_queries, quote_mysql_identifier, table_schema_queries


def test_quote_mysql_identifier_wraps_and_escapes_backticks():
    assert quote_mysql_identifier("slg`bot") == "`slg``bot`"


def test_database_schema_queries_create_required_database_and_tables():
    queries = database_schema_queries("slg_bot")
    sql = "\n".join(queries)

    assert "CREATE DATABASE IF NOT EXISTS `slg_bot`" in queries[0]
    assert "USE `slg_bot`" in queries[1]
    assert "CREATE TABLE IF NOT EXISTS groups" in sql
    assert "CREATE TABLE IF NOT EXISTS admins" in sql
    assert "has_appeal BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "superadmin BOOLEAN NOT NULL DEFAULT FALSE" in sql


def test_table_schema_queries_do_not_require_create_database_privilege():
    queries = table_schema_queries()
    sql = "\n".join(queries)

    assert "CREATE DATABASE" not in sql
    assert "USE `" not in sql
    assert "CREATE TABLE IF NOT EXISTS groups" in sql
    assert "CREATE TABLE IF NOT EXISTS admins" in sql
