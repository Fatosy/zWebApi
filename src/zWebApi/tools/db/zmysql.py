import pymysql
import os

class MysqlSession:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.db = os.getenv('DB_NAME', 'test_db')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.connection = None

    def __enter__(self):
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            db=self.db,
            port=self.port,
            cursorclass=pymysql.cursors.DictCursor
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            try:
                self.connection.commit()
            except Exception as e:
                print(f"事务提交异常: {e}")
                self.connection.rollback()
            finally:
                self.connection.close()

    def execute_query(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result

    def execute_single_query(self, query, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result

    def execute_batch_query(self, queries_params_list):
        with self.connection.cursor() as cursor:
            for query, params in queries_params_list:
                cursor.execute(query, params)

    def execute_batch_single_query(self, query, params_list):
        with self.connection.cursor() as cursor:
            cursor.executemany(query, params_list)

