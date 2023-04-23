from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


print("tes t1")

app = Flask(__name__)

#with app.app_context():
#    init_db()

app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://localhost/PR?driver=SQL+Server+Native+Client+11.0'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SECRET_KEY = 'fdgfh78@#5?>gfhf89dx,v06k'

db = SQLAlchemy(app)

sql = text("select count(&) from PR.dbo.users ")
print('sql')
conn = db.engine.connect()
trans = conn.begin()
try:
    res = conn.execute(sql)
    trans.commit()
    print("добавили")
except:
    trans.rollback()
    print("При добавлении произошла ошибка")
print(res)
print("tes t2")

if __name__ == "__main__":
    app.run(debug=True)
