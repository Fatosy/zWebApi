from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os, sqlalchemy
from contextlib import contextmanager

OrmTableBase = sqlalchemy.orm.declarative_base()

class SqlOrmSession:

    def __init__(self):
        """初始化 SqlOrmSession，使用 SQLAlchemy 引擎和会话"""
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT', 3306)
        DB_NAME = os.getenv('DB_NAME')
        DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Base = OrmTableBase
        self.metadata = MetaData()

    @contextmanager
    def get_session(self):
        """
        获取一个数据库会话，确保在使用后关闭会话。

        Yields:
            Session: 新的 SQLAlchemy 会话
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def create_tables(self):
        """在数据库中创建所有由模型定义的表"""
        self.Base.metadata.create_all(bind=self.engine)

    def drop_tables(self):
        """从数据库中删除所有由模型定义的表"""
        self.Base.metadata.drop_all(bind=self.engine)

    def alter_table_add_column(self, table_name, column):
        """
        向现有表添加新列。

        参数:
            table_name (str): 要修改的表名。
            column (Column): 要添加的 SQLAlchemy 列对象。
        """
        self.metadata.reflect(bind=self.engine)
        table = self.metadata.tables[table_name]
        column.create(table, self.engine)

    def insert_single_data(self, data_class, insert_data):
        """
        将单个数据插入到表中。

        参数:
            data (dict): 包含数据的字典。
        """
        with self.get_session() as session:
            new_data = data_class(**insert_data)
            session.add(new_data)
            session.commit()

    def insert_multiple_data(self, data_class, insert_datas):
        """
        将多个用户插入到表中。

        参数:
            insert_datas (list of dict): 包含数据的字典列表。
        """
        with self.get_session() as session:
            session.bulk_insert_mappings(data_class, insert_datas)
            session.commit()

    def update_single_data(self, data_class, id, updated_data):
        """
        更新表中的单个数据。

        参数:
            data_class: orm类
            id (int): 要更新的的 ID。
            updated_data (dict): 包含要更新字段的字典。
        """
        with self.get_session() as session:
            user = session.query(data_class).filter(data_class.id == id).first()
            if user:
                for key, value in updated_data.items():
                    setattr(user, key, value)
                session.commit()

    def update_multiple_data(self, data_class, filter_condition, updated_data):
        """
        根据过滤条件更新表中的多个数据。

        参数:
            data_class: orm类
            filter_condition (list): SQLAlchemy 过滤条件列表。
            updated_data (dict): 包含要更新字段的字典。
        """
        with self.get_session() as session:
            session.query(data_class).filter(*filter_condition).update(updated_data, synchronize_session='fetch')
            session.commit()

    def delete_single_data(self, data_class, id):
        """
        从表中删除单个数据。

        参数:
            data_class: orm类
            id (int): 要删除的 ID。
        """
        with self.get_session() as session:
            om = session.query(data_class).filter(data_class.id == id).first()
            if om:
                session.delete(om)
                session.commit()

    def delete_multiple_data(self, data_class, filter_condition):
        """
        根据过滤条件从表中删除多个数据。

        参数:
            data_class: orm类
            filter_condition (list): SQLAlchemy 过滤条件列表。
        """
        with self.get_session() as session:
            session.query(data_class).filter(*filter_condition).delete(synchronize_session='fetch')
            session.commit()

    def query_single_data(self, data_class, id):
        """
        查询表中的单个数据。

        参数:
            data_class: orm类
            id (int): 要查询的 ID。

        返回:
            data: 查询到的对象或 None（如果未找到）。
        """
        with self.get_session() as session:
            return session.query(data_class).filter(data_class.id == id).first()

    def query_multiple_data(self, data_class, filter_condition=None):
        """
        根据过滤条件查询表中的多个数据。

        参数:
            data_class: orm类
            filter_condition (list, optional): SQLAlchemy 过滤条件列表，默认为 None。

        返回:
            list of data: 查询到的对象列表。
        """
        with self.get_session() as session:
            query = session.query(data_class)
            if filter_condition:
                query = query.filter(*filter_condition)
            return query.all()


