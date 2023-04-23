from flask_login import UserMixin
from sqlalchemy import text
from flask import url_for


class UserLogin(UserMixin):
#    def getUser(self, user_id):
#        print ("UserLogingetUser")
#        try:
#            sql = text(f"select top 1 login, email, name, pwd from PR.dbo.users where id = '{user_id}' ")
#            print (sql)
#            conn = db.engine.connect()
#            res = conn.execute(sql)
#            for row in res:
#                break
#
#            if not res:
#                print("Пользователь не найден")
#                return False
#
#            return row
#        except:
#            print("Ошибка получения данных из БД ")

    def fromDB(self, user_id, db):
        self.__user = db.getUser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user.id)

    def get_login(self):
        return str(self.__user.login)

    def get_email(self):
        return str(self.__user.email)

    def getRole(self):
        return str(self.__user.userrole)

    def getName(self):
        return self.__user.name if self.__user else "Без имени"

    def getEmail(self):
        return self.__user.email if self.__user else "Без email"

    def getAvatar(self, app):
        img = None

        if not self.__user.avatar:
            try:
                with app.open_resource(app.root_path + url_for('static', filename='images/default.png'), "rb") as f:
                    img = f.read()
            except FileNotFoundError as e:
                print("Не найден аватар по умолчанию: "+str(e))
        else:
            img = self.__user.avatar

        return img

    def verifyExt(self, filename):
        ext = filename.rsplit('.', 1)[1]
        if ext == "png" or ext == "PNG":
            return True
        return False