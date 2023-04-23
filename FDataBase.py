from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Numeric, Integer, VARCHAR
from sqlalchemy.engine import result
from sqlalchemy import text
import time
import math
import re
from flask import url_for

class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.session()


    def addUser(self, name, email, hpsw):
        try:
            self.__cur.execute(f"SELECT COUNT() as `count` FROM users WHERE email LIKE '{email}'")
            res = self.__cur.fetchone()
            if res['count'] > 0:
                print("Пользователь с таким email уже существует")
                return False

            tm = math.floor(time.time())
            self.__cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, NULL, ?)", (name, email, hpsw, tm))
            self.__db.commit()
        except:
            print("Ошибка добавления пользователя в БД ")
            return False

        return True

    def getUser(self, user_id):
        try:
            #self.__db.execute(f"SELECT * FROM users WHERE id = {user_id} LIMIT 1")
            sql = text(f"SELECT id, email, login, pwd, name, avatar, userrole FROM users WHERE id = {user_id}")
            conn = self.__db.engine.connect()
            res = conn.execute(sql).fetchone()
            conn.close()
#            row = res.fetchone()
            #for row in res:
            #    break

            #row = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False

            return res
        except:
            print("Ошибка получения данных из БД getuser__")

        return False


    def getUser__(self, user_id):
        print ("fdatabase.UserLogingetUser")
        try:
            print("0")
            self.__cur.execute(f"SELECT * FROM users WHERE id = {user_id} LIMIT 1")
            print ("1")
            res = self.__cur.fetchone()
            print ("2")
            if not res:
                print("Пользователь не найден")
                return False

            return res
        except:
            print("Ошибка получения данных из БД fdatabase.getuser")


    def getUserByEmail(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email = '{email}' LIMIT 1")
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False

            return res
        except:
            print("Ошибка получения данных из БД ")

        return False

    def updateUserAvatar(self, avatar, user_id):
        if not avatar:
            return False

    #    try:
        binary = avatar
        self.__db.execute(text("UPDATE users SET avatar = ? WHERE id = ?"), (binary, user_id))
#        self.__cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, NULL, ?)", (name, email, hpsw, tm))
 #       self.__cur.query(User).filter(User.id == user_id).update({'avatar': avatar})
        self.__db.commit()
    #    except:
    #        print("UpdateUserAvatar Ошибка обновления аватара в БД: ")
    #        return False
        return True