import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import grpc

import schema_pb2 as stub
import schema_pb2_grpc as service

SERVER_ADDR = '0.0.0.0:1234'


class Database(service.DatabaseServicer):
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with closing(self.conn.cursor()) as cur:
            cur.execute('DROP TABLE IF EXISTS Users;')
            cur.execute('CREATE TABLE Users('
                        'user_id integer PRIMARY KEY, '
                        'user_name text NOT NULL);')

    def __del__(self):
        self.conn.close()

    def PutUser(self, request, context):
        user_id, user_name = request.user_id, request.user_name
        print(f'PutUser({user_id}, \'{user_name}\')')
        try:
            with closing(self.conn.cursor()) as cur:
                cur.execute(f'SELECT * FROM Users WHERE user_id={user_id} LIMIT 1')

                if len(cur.fetchall()):
                    cur.execute(f'UPDATE Users SET user_name=\'{user_name}\' WHERE user_id={user_id}')
                else:
                    cur.execute(f'INSERT INTO Users(user_id, user_name) VALUES ({user_id}, \'{user_name}\')')

                self.conn.commit()

            return stub.Response(status=True)
        except sqlite3.Error as e:
            print(e)
            return stub.Response(status=False)

    def GetUsers(self, request, context):
        try:
            with closing(self.conn.cursor()) as cur:
                cur.execute('SELECT user_id, user_name FROM Users;')
                users = [dict(r) for r in cur.fetchall()]
                return stub.Users(users=users)
        except sqlite3.Error as e:
            return stub.Users(users=[])

    def DeleteUser(self, request, context):
        print(f'DeleteUser({request.user_id})')
        try:
            with closing(self.conn.cursor()) as cur:
                cur.execute(f'DELETE FROM Users WHERE user_id={request.user_id}')
            self.conn.commit()

            return stub.Response(status=True)
        except sqlite3.Error as e:
            return stub.Response(status=False)


if __name__ == '__main__':
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    service.add_DatabaseServicer_to_server(Database('db.sql'), server)
    server.add_insecure_port(SERVER_ADDR)
    server.start()

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print('Shutting down...')
