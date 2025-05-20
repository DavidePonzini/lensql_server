import datetime
import os
import threading
import time
import pandas as pd
import psycopg2
from psycopg2.extensions import connection
from threading import Lock
from dav_tools import messages

from sql_code import SQLCode, SQLException, QueryResult, QueryResultDataset, QueryResultError, QueryResultMessage
from queries import Queries


HOST        =       os.getenv('USER_DB_HOST')
PORT        =   int(os.getenv('USER_DB_PORT'))

MAX_CONNECTION_AGE = datetime.timedelta(hours=float(os.getenv('MAX_CONNECTION_HOURS')))
CLEANUP_INTERVAL_SECONDS = int(os.getenv('CLEANUP_INTERVAL_SECONDS'))


class DBConnection:
    def __init__(self, username: str, password: str, autocommit: bool = True):
        self.username = username
        self.password = password
        self.autocommit = autocommit
        
        self.last_operation_ts = datetime.datetime.now()
        self.connection = psycopg2.connect(
            host=HOST,
            port=PORT,
            dbname=username,
            user=username,
            password=password
        )

        self.connection.autocommit = autocommit

    def close(self):
        try:
            self.connection.close()
        except Exception as e:
            messages.error(f"Error closing connection for user {self.username}: {e}")

    def cursor(self):
        return self.connection.cursor()
    
    def rollback(self):
        self.connection.rollback()

    def commit(self):
        self.connection.commit()
    
    def update_last_operation_ts(self):
        self.last_operation_ts = datetime.datetime.now()

    @property
    def time_since_last_operation(self) -> datetime.timedelta:
        return datetime.datetime.now() - self.last_operation_ts

    @property
    def notices(self) -> list:
        '''Returns the notices from the connection.'''
        try:
            return self.connection.notices
        except AttributeError:
            # Handle the case where notices are not available
            return []
        
    def clear_notices(self):
        '''Clears the notices from the connection.'''
        try:
            self.connection.notices = []
        except AttributeError:
            # Handle the case where notices are not available
            pass

        

connections: dict[str, DBConnection] = {}
conn_lock = Lock()



def connection_cleanup_thread():
    while True:
        with conn_lock:
            now = datetime.datetime.now()

            for username, conn in connections.items():
                if now - conn.last_operation_ts <= MAX_CONNECTION_AGE:
                    continue

                try:
                    connections[username].close()
                    del connections[username]
                    messages.info(f"Closed expired connection for user: {username}")
                except Exception as e:
                    messages.error(f"Error closing connection for user {username}: {e}")

        time.sleep(CLEANUP_INTERVAL_SECONDS)


cleanup_thread = threading.Thread(target=connection_cleanup_thread, daemon=True)
cleanup_thread.start()



def get_connection(username: str) -> DBConnection:
    '''
    Returns the connection for the given username.
    If the connection does not exist, it raises an exception.
    '''

    with conn_lock:
        if username in connections:
            conn = connections[username]
            conn.clear_notices()
            return conn
        raise Exception(f'User {username} does not have a connection to the database.')
    
def create_connection(username: str, password: str, autocommit: bool = True) -> connection | None:
    '''
    Returns a connection to the database for the given username.
    If the connection does not exist, it creates a new one.
    '''

    with conn_lock:
        if username in connections:
            return connections[username]
        
        try:
            conn = DBConnection(username, password, autocommit)
            connections[username] = conn
            return conn
        except Exception as e:
            messages.error('Error connecting to the database:', e)
            return None

def execute_queries(username: str, query_str: str) -> list[QueryResult]:
    '''
    Executes the given SQL queries and returns the results.
    The queries will be separated into individual statements.

    Parameters:
        query (str): The SQL query to execute.

    Returns:
        pd.DataFrame | str | SQLException: The result of the query.
        str: The original query string.
        bool: True if the query was successful, False otherwise.
    '''

    result = []
    for statement in SQLCode(query_str).strip_comments().split():
        try:
            conn = get_connection(username)
            with conn.cursor() as cur:
                cur.execute(statement.query)
                    
                if cur.description:  # Check if the query has a result set
                    rows = cur.fetchall()
                    columns = [desc[0] for desc in cur.description]
                    result.append(QueryResultDataset(pd.DataFrame(rows, columns=columns), statement.query, conn.notices))
                    continue
                
                # No result set, return the number of affected rows
                if cur.rowcount >= 0:
                    result.append(QueryResultMessage(f'{statement.first_token} {cur.rowcount}', statement.query, conn.notices))
                    continue

                # No number of affected rows, return the first token of the statement
                result.append(QueryResultMessage(f'{statement.first_token}', statement.query, conn.notices))

            conn.update_last_operation_ts()
        except Exception as e:
            result.append(QueryResultError(SQLException(e), statement.query, conn.notices))
            conn.rollback()
            conn.update_last_operation_ts()

    return result

def run_builtin_query(username: str, query: Queries) -> QueryResult:
    '''Runs a builtin query and returns the result.'''

    try:
        conn = get_connection(username)
        with conn.cursor() as cur:
            cur.execute(query.value)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            result = pd.DataFrame(rows, columns=columns)


        conn.update_last_operation_ts()
        return QueryResultDataset(result, query.name, conn.notices)
    except Exception as e:
        conn.rollback()
        conn.update_last_operation_ts()
        return QueryResultError(SQLException(e), query.name, conn.notices)

def list_schemas(username: str) -> QueryResult:
    '''Lists all schemas in the database.'''

    return run_builtin_query(username, Queries.LIST_SCHEMAS)

def list_tables(username: str) -> QueryResult:
    '''Lists all tables in the database.'''

    return run_builtin_query(username, Queries.LIST_TABLES)

def show_search_path(username: str) -> QueryResult:
    '''Shows the search path for the database.'''

    return run_builtin_query(username, Queries.SHOW_SEARCH_PATH)

