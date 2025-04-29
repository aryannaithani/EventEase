import pymysql
import pymysql.cursors

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='aryanyuvi5',
        db='eventease',
        cursorclass=pymysql.cursors.DictCursor  # Important: so you get dictionaries instead of tuples
    )