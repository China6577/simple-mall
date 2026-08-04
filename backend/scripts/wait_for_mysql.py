"""
等待 MySQL 就绪的小脚本。

Docker Compose 启动时，backend/celery 服务可通过本脚本避免在数据库未就绪前启动。
"""

import os
import sys
import time

import MySQLdb


def wait_for_mysql(host, port, user, password, db, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = MySQLdb.connect(host=host, port=int(port), user=user, passwd=password, db=db, connect_timeout=5)
            conn.close()
            print("MySQL is ready.")
            return 0
        except MySQLdb.Error as exc:
            print(f"MySQL not ready yet: {exc}")
            time.sleep(2)

    print("MySQL connection timeout.")
    return 1


if __name__ == "__main__":
    sys.exit(
        wait_for_mysql(
            host=os.getenv("DB_HOST", "mysql"),
            port=os.getenv("DB_PORT", "3306"),
            user=os.getenv("DB_USER", "mall_user"),
            password=os.getenv("DB_PASSWORD", "mall_password"),
            db=os.getenv("DB_NAME", "mall"),
        )
    )
