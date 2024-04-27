# db_operations.py
import pymysql
import logging

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'db': 'your_database',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 日志配置
logging.basicConfig(filename='app.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


def connect_to_db():
    """建立到MySQL数据库的连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        raise


def insert_into_aigcFileList(conn, data):
    """将数据插入到aigcFileList表"""
    try:
        with conn.cursor() as cursor:
            # 假设createTime和updateTime需要当前时间
            import datetime
            now = datetime.datetime.now()
            data['createTime'] = now
            data['updateTime'] = now
            # 假设bizDate也是当前日期
            data['bizDate'] = now.date()

            # 构建SQL语句
            sql = """  
            INSERT INTO aigcFileList (name, type, hashTag, link, status, partition, createTime, updateTime, bizDate)  
            VALUES (%(name)s, %(type)s, %(hashTag)s, %(link)s, %(status)s, %(partition)s, %(createTime)s, %(updateTime)s, %(bizDate)s)  
            """
            # 执行SQL语句
            cursor.execute(sql, data)
            conn.commit()
    except Exception as e:
        logging.error(f"Error inserting data into aigcFileList: {e}")
        raise

        # 可以在这里添加更多的数据库操作函数...

# todo update逻辑
def updateStatus(conn, data, status):
    """将数据插入到aigcFileList表"""
    try:
        with conn.cursor() as cursor:
            # 假设createTime和updateTime需要当前时间
            import datetime
            now = datetime.datetime.now()
            data['updateTime'] = now

            # 构建SQL语句
            sql = """  
            INSERT INTO aigcFileList (name, type, hashTag, link, status, partition, createTime, updateTime, bizDate)  
            VALUES (%(name)s, %(type)s, %(hashTag)s, %(link)s, %(status)s, %(partition)s, %(createTime)s, %(updateTime)s, %(bizDate)s)  
            """
            # 执行SQL语句
            cursor.execute(sql, data)
            conn.commit()
    except Exception as e:
        logging.error(f"Error inserting data into aigcFileList: {e}")
        raise

        # 可以在这里添加更多的数据库操作函数...