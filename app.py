import mail
import json
import os
import shutil
import datetime
from flask import Flask, render_template, url_for, request, redirect, make_response
from flask import g, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Numeric, Integer, VARCHAR
from sqlalchemy.engine import result
from sqlalchemy import text, or_
from FDataBase import FDataBase

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
from flask_login import UserMixin
from forms import PRForm, LoginForm
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = 'fdgfh78@#5?>gfhf89dx,v06k'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
paramfile = open("params.json")
parameters = json.load(paramfile)
mailparams = {}
mailparams.setdefault('smtpserver', parameters.get("smtpserver"))
mailparams.setdefault("smtplogin", parameters.get("smtplogin"))
mailparams.setdefault("smtppassword", parameters.get("smtppassword"))
app.config['SQLALCHEMY_DATABASE_URI'] = parameters.get('connectionstring')# 'mssql+pyodbc://localhost/PaymentRequest?driver=SQL+Server+Native+Client+11.0'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SECRET_KEY = 'fdgfh78@#5?>gfhf89dx,v06k'
MAX_CONTENT_LENGTH = 1024 * 1024
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"
dbase = None

db = SQLAlchemy(app)

class attachment(db.Model):
    __tablename__ = 'attachment'
    id = db.Column(db.Integer, primary_key=True)
    prid = db.Column(db.Integer)
    filename = db.Column(db.String(256))
    path = db.Column(db.String(256))
    CreateDate = db.Column(db.DateTime, default=datetime.datetime.today())
    login = db.Column(db.String(10))

class PaymentRequest(db.Model):
    __tablename__ = 'PaymentRequest'
    id = db.Column(db.Integer, primary_key=True)
    direction = db.Column(db.String(50))
    payer = db.Column(db.String(250))
    responsible = db.Column(db.String(50))
    paymenttype = db.Column(db.String(50))
    porderno = db.Column(db.String(50))
    invoice = db.Column(db.String(50))
    invdate = db.Column(db.Date)
    trno = db.Column(db.String(50), default='')
    trdate = db.Column(db.Date)
    paymentdate = db.Column(db.Date)
    plandate = db.Column(db.Date)
    amount = db.Column(db.Numeric(20, 2))
    currency = db.Column(db.String(3))
    dept = db.Column(db.String(50))
    contract = db.Column(db.String(50))
    inn = db.Column(db.String(12))
    vendorname = db.Column(db.String(250))
    status = db.Column(db.String(20))
    requested = db.Column(db.String(10), default='00000')
    requeststatus = db.Column(db.String(10), default='00000')
    acomment = db.Column(db.String(500), default='')
    pcomment = db.Column(db.String(500), default='')
    CreateDate = db.Column(db.DateTime, default=datetime.datetime.today())

class department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    approvermail = db.Column(db.String(50))
    approver = db.Column(db.String(50))

class task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    prid = db.Column(db.Integer)
    alttaskid = db.Column(db.Integer)
    tasktype = db.Column(db.String(50))
    taskstatus = db.Column(db.String(50))
    assignee = db.Column(db.String(50))
    assigneemail = db.Column(db.String(50))
    scomment = db.Column(db.String(250), default='')
    acomment = db.Column(db.String(250), default='')
    isactive = db.Column(db.String(1), default='1')
    approvedate =db.Column(db.DateTime)
    CreateDate = db.Column(db.DateTime, default=datetime.datetime.today())

class Vendor(db.Model):
    __tablename__ = 'Vendors'
    ID = db.Column(db.Integer, primary_key=True)
    LegalCode = db.Column(db.String(10), primary_key=True)
    INN = db.Column(db.String(50))
    Name = db.Column(db.String(500))
    KPP = db.Column(db.String(50))
    Address = db.Column(db.String(500))
    OGRN = db.Column(db.String(50))
    ShortName = db.Column(db.String(500))
    AlternateName = db.Column(db.String(500))
    LegalName = db.Column(db.String(50))
    GeneralDirectorName = db.Column(db.String(150))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    login = db.Column(db.String(50))
    pwd = db.Column(db.String(50))
    userrole = db.Column(db.String(50))
    avatar = db.Column(db.LargeBinary)


@app.before_request
def before_request():
    """Установление соединения с БД перед выполнением запроса"""
    global dbase
    dbase = FDataBase(db)


@app.teardown_appcontext
def close_db(error):
    '''Закрываем соединение с БД, если оно было установлено'''
    if hasattr(g, 'link_db'):
        g.link_db.close()


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, dbase)

#    def __repr__(self):
#        return '<Article %r>' % self.id


 #   def __repr__(self):
  #      return '<User %r>' % self.id


@app.route('/')
@app.route('/home')
def index():
    userrole = ''
    if current_user.is_authenticated:
        print('userrole', parameters.get('userrole'))
        userrole = getUserByLogin(current_user.get_login()).userrole
#        if not(parameters.get('userrole')):
#            userrole = getUserByLogin(current_user.get_login()).userrole
#            print('home role', userrole, current_user.get_login())
        if userrole == 'accounting':
            articles = PaymentRequest.query.filter(or_(PaymentRequest.status == "Закрыто", PaymentRequest.status == "Одобрено", PaymentRequest.status == "Передано в оплату")).order_by(
                PaymentRequest.CreateDate.desc()).limit(100).all()
        elif userrole == 'admin':
            articles = PaymentRequest.query.order_by(PaymentRequest.CreateDate.desc()).limit(100).all()
        else:
            print('user ',current_user.get_login())
            articles = PaymentRequest.query.filter(PaymentRequest.status != "Закрыто" and PaymentRequest.responsible == current_user.get_login()).order_by(PaymentRequest.CreateDate.desc()).limit(1000).all()
    #    tasks = task.query.filter(task.taskstatus == "Created", task.assignee == current_user.get_login()).limit(100).all()
        sql = text(f"""select  a.id, a.prid, descr, dept, paymenttype, amount, currency, vendorname, b.responsible, c.name, substring(a.tasktype,charindex(' ',a.tasktype),100) as tasktype 
        from task a with(nolock) left join tasktypes t on a.tasktype=t.tasktype join PaymentRequest b with(nolock) on a.prid=b.id left join users c on b.responsible=c.login 
         where a.taskstatus='Created' and upper(a.assignee)=upper('{current_user.get_login()}')""")
        conn = db.engine.connect()
        tasks = conn.execute(sql).fetchall()
        conn.close
    else:
        articles = None
        tasks = None

    return render_template("index.html", articles=articles, tasks=tasks, userrole=userrole)


@app.route('/payments', methods=["POST", "GET"])
@login_required
def payments():
    if request.method == "POST":
        args = []

        if request.form['prno']>'':
            args.append('prno=' + request.form['prno'])
        elif request.form['trno']>'':
            args.append('trno=' + request.form['trno'])
        else:
            args.append('date1='+request.form['date1']+'&date2='+request.form['date2'])

        if request.form['payer'] == 'Стоков Машинное Оборудование АО':
            args.append('le=SMO')
        if request.form['payer'] == 'Стоков Компоненты ООО':
            args.append('le=SK')
        if request.form['payer'] == 'Стоков Конструкция ООО':
            args.append('le=SST')

        if request.form['sorting'] == 'Дата планируемая платежа':
            args.append('sort=plandate')
        if request.form['sorting'] == 'Получатель платежа':
            args.append('sort=vendor')
        if len(args)>0:
            args = '?'+'&'.join(args)
        return redirect(url_for('payments') + args)

    fparams = {}
    if request.args.get('sort') == 'vendor':
        sOrderBy="vendorname"
        fparams['OrderBy'] = "Получатель платежа"
    else:
        sOrderBy = "plandate desc"
        fparams['OrderBy'] = "Дата платежа планируемая"

    sWhere = f"status='Передано в оплату'"

    if request.args.get('prno') != None:
        fparams['prno'] = request.args.get('prno')
        sWhere=f"a.id={str(request.args.get('prno'))}"

    if request.args.get('trno') != None:
        fparams['trno'] = request.args.get('trno')
        print(fparams['trno'])
        sWhere=f"upper(a.trno) like upper('{str(request.args.get('trno'))}%')"

    if request.args.get('date1') != None and request.args.get('date2') != None:
        sdate1 = datetime.date.strftime(datetime.datetime.strptime(request.args.get('date1'), '%Y-%m-%d'), r'%m/%d/%Y')
        sdate2 = datetime.date.strftime(datetime.datetime.strptime(request.args.get('date2'), '%Y-%m-%d'), r'%m/%d/%Y')
        print(sdate2, type(sdate2))
        sWhere=f"status='Передано в оплату' and isnull(plandate,trdate)>='{sdate1}' and isnull(plandate,trdate)<='{sdate2}'"

    if request.args.get('le') != None:
        if request.args.get('le') == 'SMO':
            fparams['le'] = "SMO"
            sWhere += f" and payer='Стоков Машинное Оборудование АО'"
        if request.args.get('le') == 'SK':
            fparams['le'] = "SK"
            sWhere += f" and payer='Стоков Компоненты ООО'"
        if request.args.get('le') == 'SST':
            fparams['le'] = "SST"
            sWhere += f" and payer='Стоков Конструкция ООО'"

    sql = text(f"""select a.id, direction, payer, responsible, b.name as respname, paymenttype, amount, currency, dept, 
    vendorname, trno, trdate, plandate, acomment, max(filename) as file1, min(filename) as file2, count(c.id) as nfiles from PaymentRequest a 
    left join users b on a.responsible=b.login left join attachment c on a.id=c.prid 
    where {sWhere}
    group by a.id, direction, payer, responsible, b.name, paymenttype, amount, currency, dept, 
    vendorname, trno, trdate, plandate, acomment
    order by {sOrderBy}""")
    print(sql)

    conn = db.engine.connect()
    articles = conn.execute(sql).fetchall()
    conn.close
    print('request.args.get(date2)', request.args.get('date2'))
    date1 = request.args.get('date1')
    date2 = request.args.get('date2')
    if date2 == None:
        date2 = datetime.date.today() + timedelta(days=10)
    if date1 == None:
        date1 = datetime.date.today() - timedelta(days=90)
    return render_template("payments.html", articles=articles, date1=date1, date2=date2, fparams=fparams)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route("/login1", methods=["POST", "GET"])
def login1():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        #user = db.session.query(User).filter(User.login == request.form['login']).first()
        user = User.query.filter(User.login == request.form['login']).first()
#        user = getUserByLogin(request.form['login'])
        if user and check_password_hash(user.pwd, request.form['psw']):
            userlogin = UserLogin().create(user)
            rm = True if request.form.get('remainme') else False
            #parameters['userrole'] = getUserByLogin(current_user.get_login()).userrole
            login_user(userlogin, remember=rm)
#            return redirect(url_for('index'))
            return redirect(request.args.get("next") or url_for("index"))
        flash("Неверная пара логин/пароль", "error")
    return render_template("login.html")

@app.route('/testf', methods=['POST','GET'])
def testf():
    return copyprfiles(22)

def copyprfiles(prid):
    pr=PaymentRequest.query.filter(PaymentRequest.id == prid).first()
    files = attachment.query.filter(attachment.prid == prid).all()
    print('copyprfiles', pr.trno)
    trno = pr.trno if pr.trno != None else ''
    trno += '_'+str(prid)

    rstr = 'nothing'
    dpath = parameters.get('archivepath')
    if dpath == None:
        dpath = 'prarchive'
    if not os.path.exists(os.path.join(dpath, trno)):
        os.makedirs(os.path.join(dpath, trno))
    for f in files:
        sfilepath = os.path.join('archive',str(prid),f.filename)
        dfilepath = os.path.join(dpath, trno, f.filename)

        if os.path.isfile(sfilepath):
            shutil.copy2(sfilepath, dfilepath)

            rstr = "copied from " + sfilepath + " into " + dfilepath

    return rstr
@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    print('login 1')
    form = LoginForm()

    if form.validate_on_submit():
#        user = dbase.getUserByEmail(form.email.data)
        user = User.query.filter(User.login == request.form['login']).first()
        print('login user', request.form['login'], user.name)
        if user and check_password_hash(user.pwd, form.psw.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            #parameters['userrole'] = getUserByLogin(current_user.get_login()).userrole

            return redirect(request.args.get("next") or url_for("index"))

        flash("Неверная пара логин/пароль", "error")
        return render_template("login1.html", form=form)
    else:
        print('novalid user')
    return render_template("login1.html", form=form)

@app.route('/logout')
@login_required
def logout():
    #parameters['userrole'] = ""
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
#    return f"""<p><a href="{url_for('logout')}">Выйти из профиля</a><p>user info: {current_user.get_id()}"""
    return render_template("profile.html")


@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        if len(request.form['login']) != 7 or request.form['login'].upper()[0] != 'V':
            flash("Логин должен начинаться с v и быть длинной 7 символов", "error")
            return render_template("register.html")
        #if len(request.form['psw'])<4:
        #    flash("Пароль слишком короткий ", "error")
        #    return render_template("register.html")
        if request.form['psw'] != request.form['psw2']:
            flash("Пароль не совпадает с контролем", "error")
            return render_template("register.html")

        sql = text(f"select count(*) from dbo.users where upper(login) = upper('{request.form['login']}') ")
        conn = db.engine.connect()
        res = conn.execute(sql)
        for row in res:
            break
        if row[0] > 0:
            flash("Такой логин уже зарегистрирован", "error")
            return render_template("register.html")
        email = request.form['login'].strip() + "@stokov.ru"
        hash = generate_password_hash(request.form['psw'])
        res = addUser(request.form['name'], request.form['login'], email, hash)
        if res:
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))
        else:
            flash("Ошибка при добавлении в БД", "error")

    return render_template("register.html")

@app.route('/test3', methods=['POST','GET'])
def test3():
    name = "n2sf"
    email = "emareil"
    sql = text(f"select count(*) from dbo.users where name = '{name}' or email='{email}'       ")
    conn = db.engine.connect()
    res = conn.execute(sql)
    for row in res:
        break
    return "test3 finished" + str(row[0])


#def getUser(user_id):
#    try:
#        sql = text(f"select top 1 login, email, name, pwd, userrole from dbo.users where id = {user_id} ")
#        conn = db.engine.connect()
#        res = conn.execute(sql)
##        for row in res:
#            break
#
#        if not res:
#            print("Пользователь не найден")
#            return False
#
#        return row
#    except:
#        print("Ошибка получения данных из БД (getUser)")
#    return False


def getUserByLogin(login):
    try:
        user = User.query.filter(User.login == login).first()
        return user
    except:
        print("Ошибка получения данных из БД getuserbylogin ")

    return False

def addUser(name, login, email, hpsw):
    sql = text(f"select count(*) from dbo.users where upper(login) = upper('{login}') or upper(email)=upper('{email}')       ")
    conn = db.engine.connect()
    res = conn.execute(sql)
    for row in res:
        break
    if row[0] > 0:
            print("Пользователь с таким login|email уже существует")
            return False

    sql = text(f"insert into dbo.users (name, login, email, pwd) values('{name}', '{login}', '{email}','{hpsw}')")
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(sql)
        trans.commit()
        print("adduser добавили")
    except:
        trans.rollback()
        print("adduser При добавлении произошла ошибка")
        return False

    return True


@app.route('/test1', methods=['POST','GET'])
def test1():
    a = getUserByLogin('v000529')#addUser("u","p","h")
    return "test1 finished"+a.userrole


#@app.route('/posts')
#def posts():
#    articles = PaymentRequest.query.order_by(PaymentRequest.CreateDate.desc()).all()
#    return render_template("posts.html", articles=articles)


@app.route('/posts/<int:id>')
def post_detail(id):
    article = PaymentRequest.query.get(id)
    tasks = task.query.filter(task.prid == id).order_by(task.CreateDate.desc()).all()
    files =attachment.query.filter(attachment.prid == id)
    return render_template("post_detail.html", article=article, tasks=tasks, files=files)

@app.route('/approve/<int:prid>/<int:taskid>', methods=['GET', 'POST'])
def approve(prid, taskid):
    article = PaymentRequest.query.get(prid)
    files =attachment.query.filter(attachment.prid == prid)
#    tasks =task.query.filter(task.id == taskid).first()
    sql = text(f"""select  a.id, a.prid, b.responsible, c.name as requestorname, a.scomment, a.acomment, a.tasktype, descr  
    from task a left join tasktypes t on a.tasktype=t.tasktype join PaymentRequest b on a.prid=b.id left join users c on b.responsible=c.login 
     where a.id='{taskid}'""")
    conn = db.engine.connect()
    tasks = conn.execute(sql).first()
    if request.method == 'POST':
        print('approve', request.form['action'])
        if request.form['action'] == "Утвердить":
            sql = text(f"update task set taskstatus='Approved', approvedate=getdate() where id={taskid}")
            conn.execute(sql)
            conn.commit()
            n=-1
            if tasks.tasktype == 'Approvement std':
                n = 0
            if tasks.tasktype =='Approvement m5':
                n = 1
            if tasks.tasktype == 'Approvement nondeduct':
                n = 2
            if tasks.tasktype == 'Approvement adv':
                n = 3
            if tasks.tasktype == 'Approvement noorg':
                n = 4
            if n > -1:
                if article.requeststatus == None:
                    article.requeststatus = '0' * 5
                article.requeststatus = article.requeststatus[:n ] + "+" + article.requeststatus[n+1:]
                PaymentRequest.query.filter(PaymentRequest.id == prid).update({'requeststatus': article.requeststatus})
                db.session.commit()
                isclosed = True
                for i in range(5):
                    if article.requested[i] != '0':
                        if article.requeststatus[i] != "+":
                            isclosed = False
                            break

                if isclosed:
                    PaymentRequest.query.filter(PaymentRequest.id == prid).update({'status': 'Одобрено'})
                    db.session.commit()
                    user = User.query.filter(User.login == article.responsible).first()
                    respmail = user.email

                    subj = "PR " + str(prid) + " Одобрено"
                    msg = "<p>Здравствуйте,<br>Ваш запрос на утверждение платежа в пользу " + article.vendorname + " сумма " + str(
                        article.amount) + " " + article.currency +"</p>"
                    msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
                    msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
                    msg += f"<p><b>был одобрен и будет передан в бухгалтерию</b></p>"
                    msg += '<p>Посмотреть подробности можно по ссылке <a href="'+parameters.get("webserver")+'/posts/' + str(prid) + '">Payment request</a></p>'
                    print('mail1', respmail[0])
                    mail.sendmail(mailparams, respmail, subj, msg)
                    subj = "PR " + str(prid) + " Одобрен. Готов к обработке"
                    msg = "<p>Здравствуйте,<br>Запрос на утверждение платежа в пользу " + article.vendorname + " сумма " + str(
                        article.amount) + " " + article.currency + "</p>"
                    msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
                    msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
                    msg += f"<p><b>был одобрен можно приступать к обработке</b></p>"
                    msg += '<p>Посмотреть подробности можно по ссылке <a href="'+parameters.get("webserver")+'/posts/' + str(prid) + '">Payment request</a></p>'
                    mail.sendmail(mailparams, parameters.get('accountingmail'), subj, msg)


            #                sql = text(f"update PaymentRequest set [requeststatus]='{article.requeststatus}' where id={prid}")

            sql = text(f"update task set taskstatus='Approved', acomment='{request.form['acomment']}' where id={taskid}")
            conn.execute(sql)
            conn.commit()
            return redirect(url_for('index'))
        if request.form['action'] == "Отказать":
            print("отказать!", taskid)
            #task.query.filter(task.id == taskid).update({'taskstatus': 'Refused'})
            #db.session.commit
            #task.query.filter(task.id == taskid).update({'acomment': request.form['acomment']})
            #db.session.commit
            sql = text(f"update task set taskstatus='Refused', acomment='{request.form['acomment']}' where id={taskid}")
            conn.execute(sql)
            conn.commit()

#            conn.close
#            conn = db.engine.connect()
            sql = text(f"update PaymentRequest set [status]='Отказано в утверждении' where id={prid}")
            PaymentRequest.query.filter(PaymentRequest.id == prid).update({'status': 'Отказано в утверждении'})
#            print(sql)
#            conn.execute(sql)
#            conn.commit
            db.session.commit()
            conn.close

#            sql = text(f"select email from PaymentRequest a  WITH(NOLOCK) join users b on responsible=login where a.id={prid}")
#            conn.execute(sql).first()
#            conn.commit

            user = User.query.filter(User.login == article.responsible).first()
            respmail = user.email

            subj = "PR " + str(prid) + " Rejected"
            msg = "<p>Здравствуйте,<br>Ваш запрос на утверждение платежа в пользу " + article.vendorname + " сумма " + str(
                article.amount) + " " + article.currency + "</p>"
            msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
            msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
            msg += f"<p><b>был отклонен</b> Комментарий: {request.form['acomment']}</p>"
            msg += '<p>Посмотреть подробности можно по ссылке <a href="'+parameters.get("webserver")+'/posts/' + str(prid) + '">Payment request</a></p>'
            mail.sendmail(mailparams, respmail, subj, msg)
            return redirect(url_for('index'))
    return render_template("approve.html", article=article, files=files, task=tasks)

@app.route('/process/<int:id>', methods=['POST', 'GET'])
def process(id):
    print('process')
    article = PaymentRequest.query.get(id)
#    files = department.query.filter(department.id == article.id)
    files =attachment.query.filter(attachment.prid == id)
    dept = department.query.filter(department.name == article.dept).first()
    print(dept)
    if request.method == 'POST':
        subj="PR "+str(id)+" Approve"
        msg ="<p>Здравствуйте,<br>Направляем Вам запрос на утверждение платежа в пользу "+article.vendorname+" сумма "+ str(article.amount)+" "+article.currency+"</p>"
        msg += "Заявитель "+getUserByLogin(current_user.get_login()).name+"<br>"
        msg +=f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
        msg +=f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
        msg +=f"<p>Комментарий заявителя: {request.form.get('scomment')}</p>"

        flagline='0'*5
        flag = True if request.form.get('std') == 'on' else False
        if flag:
            flagline = '1'+flagline[1:]
            task.query.filter(task.prid == id, task.tasktype == 'Approvement std').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(task.prid == id, task.tasktype == 'Approvement std', task.taskstatus == "Created", task.isactive == '1').all())
            if nrec == 0:
                tstd = task(prid=id, tasktype="Approvement std", taskstatus="Created", assignee=dept.approver, assigneemail=dept.approvermail)
                db.session.add(tstd)
                db.session.commit()

            taskid = task.query.filter(task.prid == id, task.tasktype == "Approvement std", task.taskstatus == "Created", task.assignee == dept.approver).order_by(task.id.desc()).first()
            print('taskid', taskid)
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(id) + '/' + \
                str(taskid.id) + '">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение через ответный имейл. Не отвечайте на это письмо, если не хотите отклонить, отправить на доработку заявку или оставить комментарий!</b>'

            mail.sendmail(mailparams, dept.approvermail, subj+' std', msg1)
        flag = True if request.form.get('m5')=='on' else False
        if flag:
            flagline = flagline[:1] +'1'+ flagline[:2]
            task.query.filter(task.prid == id, task.tasktype == 'Approvement m5').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(task.prid == id, task.tasktype == 'Approvement m5', task.taskstatus == "Created").all())
            if nrec == 0:
                tstd = task(prid=id, tasktype = "Approvement m5", taskstatus = "Created", assignee = dept.approver, assigneemail = dept.approvermail)
                db.session.add(tstd)
                db.session.commit()
            taskid = task.query.filter(task.prid == id, task.tasktype == "Approvement std", task.taskstatus == "Created", task.assignee == dept.approver).order_by(task.id.desc()).first()
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(id) + '/' + \
                str(taskid.id) + '">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение через ответный имейл. Не отвечайте на это письмо, если не хотите отклонить, отправить на доработку заявку или оставить комментарий!</b>'
            mail.sendmail(mailparams, dept.approvermail, subj+' >5m', msg1)

        if request.form.get('nondeduct'):
            flagline = flagline[:2] + '1'+ flagline[:3]
            task.query.filter(task.prid == id, task.tasktype == 'Approvement nondeduct').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(
                task.prid == id and task.tasktype == 'Approvement nondeduct' and task.taskstatus == "Created").all())
            if nrec == 0:
                tstd = task(prid = id, tasktype = "Approvement nondeduct", taskstatus = "Created", assignee=dept.approver, assigneemail=dept.approvermail)
                db.session.add(tstd)
                db.session.commit()
            taskid = task.query.filter(task.prid==id. task.tasktype == "Approvement nondeduct", task.taskstatus == "Created", task.assignee == dept.approver).order_by(task.id.desc()).first()
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(id) + '/' + \
                str(taskid.id) + '">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение через ответный имейл. Не отвечайте на это письмо, если не хотите отклонить, отправить на доработку заявку или оставить комментарий!</b>'
            mail.sendmail(mailparams, dept.approvermail, subj+' nondeduct', msg1)

        if request.form.get('adv'):
            flagline = flagline[:3] + '1' + flagline[:4]
            task.query.filter(task.prid == id, task.tasktype == 'Approvement adv').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(task.prid == id, task.tasktype == 'Approvement adv', task.taskstatus == "Created").all())
            if nrec == 0:
                tstd = task(prid = id, tasktype = "Approvement adv", taskstatus = "Created", assignee=dept.approver, assigneemail = dept.approvermail)
                db.session.add(tstd)
                db.session.commit()
            taskid = task.query.filter(task.prid==id, task.tasktype == "Approvement adv", task.taskstatus == "Created", task.assignee == dept.approver).order_by(task.id.desc()).first()
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(id) + '/' + \
                str(taskid.id) + '">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение через ответный имейл. Не отвечайте на это письмо, если не хотите отклонить, отправить на доработку заявку или оставить комментарий!</b>'
            mail.sendmail(mailparams, dept.approvermail, subj+' аванс', msg1)

        if request.form.get('noorg'):
            flagline = flagline[:4] + '1' + flagline[:5]
            task.query.filter(task.prid == id, task.tasktype == 'Approvement noorg').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(task.prid == id, task.tasktype == 'Approvement noorg', task.taskstatus == "Created").all())
            if nrec == 0:
                tstd = task(prid = id, tasktype="Approvement noorg", taskstatus="Created", assignee=dept.approver, assigneemail=dept.approvermail)
                db.session.add(tstd)
                db.session.commit()
            taskid = task.query.filter(task.prid==id, task.tasktype == "Approvement noorg", task.taskstatus == "Created", task.assignee == dept.approver).order_by(task.id.desc()).first()
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(id) + '/' + \
                str(taskid.id) + '">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение через ответный имейл. Не отвечайте на это письмо, если не хотите отклонить, отправить на доработку заявку или оставить комментарий!</b>'
            mail.sendmail(mailparams, dept.approvermail, subj+' нет оригиналов', msg1)

        article.status = "Ожидание утверждения"
        article.requested = flagline
        if article.requeststatus == None:
            article = "0" * 5
        elif len(article.requeststatus) < 5:
                article = "0"*5

        conn = db.engine.connect()
        sql = text(f"update task set scomment='{request.form['scomment']}' where id={taskid.id}")
        conn.execute(sql)
        conn.commit()
        db.session.commit()
        return redirect(url_for('index'))

    return render_template("process.html", article=article, files=files, managermail=dept.approvermail)

@app.route('/toaccounting/<int:id>', methods=['POST', 'GET'])
def toaccounting(id):
    article = PaymentRequest.query.get(id)
#    files = department.query.filter(department.id == article.id)
    if article.trno != "" or article.trno == None:
        PaymentRequest.query.filter(PaymentRequest.id == id).update({'status': 'Одобрено'})
    else:
        PaymentRequest.query.filter(PaymentRequest.id == id).update({'status': 'Передано в оплату'})

    db.session.commit()

    subj = "PR " + str(id) + " Одобрен. Готов к обработке"
    msg = "<p>Здравствуйте,<br>Запрос на утверждение платежа в пользу " + article.vendorname + " сумма " + str(
        article.amount) + " " + article.currency + "</p>"
    msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
    msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
    msg += f"<p><b>был одобрен можно приступать к обработке</b></p>"
    msg += '<p>Посмотреть подробности можно по ссылке <a href="' + parameters.get("webserver") + '/posts/' + str(
        id) + '">Payment request</a></p>'
    mail.sendmail(mailparams, parameters.get('accountingmail'), subj, msg)

#    return redirect(url_for('index'))

    return redirect(f"/posts/{id}")


@app.route('/accpost/<int:id>', methods=['POST', 'GET'])
def accpost(id):
    article = PaymentRequest.query.get(id)
#    files = department.query.filter(department.id == article.id)
    files =attachment.query.filter(attachment.prid == id)
    tasks = task.query.filter(task.prid == id)
    dept = department.query.filter(department.name == article.dept).first()
    if request.method == 'POST':
        user = User.query.filter(User.login == article.responsible).first()
        respmail = user.email
        if request.form['action'] == "Сохранить и передать в оплату":
            article.status = "Передано в оплату"
            article.trno = request.form.get('trno')
            article.trdate = request.form.get('trdate')
            article.plandate = request.form.get('plandate')
            db.session.commit()
            copyprfiles(id)
        if request.form['action'] == "Отправить на доработку":
            article.status = "Доработка"
            article.acomment = request.form.get("acomment")
            mail.sendmail(mailparams, respmail, f"PR {id}. Бухгалтерия вернула на доработку",
                          f'Здравствуйте,<br> PR вернули на доработку с коментарием {request.form["acomment"]} нет данных.')
            db.session.commit()

        return redirect(url_for('index'))
    return render_template("pr_accpost.html", article=article, files=files, managermail=dept.approvermail, tasks=tasks)


@app.route('/paymentpost/<int:id>', methods=['POST', 'GET'])
def paymentpost(id):
    article = PaymentRequest.query.get(id)
#    files = department.query.filter(department.id == article.id)
    files =attachment.query.filter(attachment.prid == id)
    tasks = task.query.filter(task.prid == id)
    dept = department.query.filter(department.name == article.dept).first()
    if request.method == 'POST':
        user = User.query.filter(User.login == article.responsible).first()
        respmail = user.email
        if request.form['action'] == "Оплачено":
            article.status = "Оплачено"
            article.pcomment = request.form.get("pcomment")
            article.paymentdate = request.form.get("pdate")
            db.session.commit()
            mail.sendmail(mailparams, respmail, f"PR {id}. Оплачено",
                      f'Здравствуйте,<br> PR оплачено. Дата оплаты {request.form["pdate"]}. Комментарий {request.form["pcomment"]}.')
        if request.form['action'] == "Отправить на доработку бухгалтеру":
            article.status = "Одобрено"
            article.pcomment = request.form.get("pcomment")
            mail.sendmail(mailparams, parameters.get('accountingmail'), f"PR {id}. Отклонено",
                          f'Здравствуйте,<br> Оплата PR была отклонена, требуется доработка бухгалтера. Комментарий {request.form["pcomment"]}.')
            db.session.commit()
        if request.form['action'] == "Отправить на доработку инициатору":
            article.status = "Доработка"
            article.pcomment = request.form.get("pcomment")
            mail.sendmail(mailparams, respmail, f"PR {id}. Бухгалтерия вернула из оплаты на доработку",
                              f'Здравствуйте,<br> PR вернули из оплаты на доработку с комментарием {request.form["pcomment"]}.')
            db.session.commit()
        if request.form['action'] == "Отправить на взаимозачет":
            article.status = "Взаимозачет"
            article.pcomment = request.form.get("pcomment")
            mail.sendmail(mailparams, parameters.get('accountingmail'), f"PR {id}. Взаимозачет",
                          f'Здравствуйте,<br> PR отправили на взаимозачет. Комментарий {request.form["pcomment"]}.')
            db.session.commit()
        if request.form['action'] == "Отменить оплату":
            article.status = "Передано в оплату"
            article.pcomment = request.form.get("pcomment")
            db.session.commit()
        return redirect(url_for('payments'))

    return render_template("pr_payment.html", article=article, files=files, managermail=dept.approvermail, tasks=tasks, pdate=datetime.date.today())


@app.route('/attachments/<int:prid>', methods=['POST','GET'])
def post_attach(prid):
    article = PaymentRequest.query.get(prid)
    files = attachment.query.filter(attachment.prid == prid)
    if request.method == 'POST':
        files = request.files.getlist("files")
        if not(os.path.isdir(os.path.join('archive', str(prid)))):
            os.mkdir(os.path.join('archive', str(prid)))

        for file in files:
            res = attachment.query.filter(attachment.filename == file.filename, attachment.path == str(prid)).first()
            if res is not None:
                db.session.delete(res)
                db.session.commit()

            att = attachment(prid=prid, filename=(file.filename), login=current_user.get_login(), path=str(prid))

            db.session.add(att)
            db.session.commit()

            file.save(os.path.join('archive', str(prid), file.filename))
            files = attachment.query.filter(attachment.prid == prid)

    return render_template("edit-attachements.html", article=article, files=files)


@app.route('/posts/<int:id>/del')
def post_delete(id):
    article = PaymentRequest.query.get_or_404(id)

    try:
        db.session.delete(article)
        db.session.commit()
        return redirect(url_for('index'))
    except:
        return "При удалении произошла ошибка"


@app.route('/posts/<int:id>/update', methods=['POST','GET'])
def pr_update(id):
    pr = PaymentRequest.query.get(id)
    form = PRForm()
    if form.validate_on_submit():
        pr.direction = form.direction.data
        pr.payer = form.payer.data
        pr.responsible = form.responsible.data
        pr.paymenttype = form.paymenttype.data
        pr.porderno = form.porderno.data
        pr.invoice = form.invoice.data
        pr.invdate = datetime.datetime.combine(form.invdate.data, datetime.datetime.min.time())
        pr.amount = form.amount.data
        pr.currency = form.currency.data
        pr.dept = form.dept.data
        pr.contract = form.contract.data
        pr.inn = form.inn.data
#        pr.vendorname = form.vendorname.data
        try:
            db.session.commit()
        except:
            return "При редактировании произошла ошибка"
#        for file in form.files.data:
#            att = attachment(prid=id, filename=secure_filename(file.filename))
##            db.session.add(att)
 #           db.session.commit()
 #           file.save(os.path.join('archive', secure_filename(file.filename)))


        return redirect(url_for('index'))
    else:
        form.direction.data=pr.direction
        form.payer.data = pr.payer
        form.responsible.data = pr.responsible
        form.paymenttype.data = pr.paymenttype
        form.porderno.data = pr.porderno
        form.invoice.data = pr.invoice
        form.invdate.data = pr.invdate
        form.amount.data = pr.amount
        form.currency.data = pr.currency
        form.dept.data = pr.dept
        form.contract.data = pr.contract
        form.inn.data = pr.inn
        #form.vendorname.data = pr.vendorname
        files = attachment.query.filter(attachment.prid == id)

        return render_template("pr_update.html", form=form,  files=files)


@app.route('/download/<int:id>/<path:filename>', methods=['GET', 'POST'])
def download(id, filename):
    uploads = os.path.join("archive", str(id))#app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads, filename)

@app.route('/delattach/<int:id>/<int:prid>', methods=['GET', 'POST'])
def delattach(id, prid):
    file = attachment.query.get_or_404(id)

    try:
        db.session.delete(file)
        db.session.commit()
    except:
        flash("ошибка удаления", "error")

    return redirect('/attachments/' + str(prid))


def getvendorbyinn(inn):
    return Vendor.query.filter(Vendor.INN == inn).limit(1).first()

@app.route('/create-pr', methods=['POST','GET'])
@app.route('/create_pr', methods=['POST','GET'])
@login_required
def pr_create():
    form = PRForm()
    if form.validate_on_submit():
        if request.form['action'] == "Найти":
            svendor = Vendor.query.filter(Vendor.INN == form.inn.data).limit(1).first()
            if svendor != None:
                form.vendorname.data = svendor.ShortName
            else:
                form.vendorname.data = ""
                flash("Клиент с этим ИНН не найден. Можно сохранить, уйдет письмо ответстенному за добавление.", "error")
            return render_template("create-pr.html", form=form)
        invdate = datetime.datetime.combine(form.invdate.data, datetime.datetime.min.time())
        vendorname=""#form.vendorname.data
        inn = form.inn.data
        if vendorname == "":
            svendor = getvendorbyinn(form.inn.data)#Vendor.query.filter(Vendor.INN == inn).limit(1).first()
            print('pr_create', svendor, type(svendor))
            if svendor != None:
                vendorname = svendor.ShortName
            else:
                user = User.query.filter(User.login == form.responsible.data).first()
                respmail = user.email
                resplist = []
                resplist.append(respmail)
                if parameters.get('supportmail') != None:
                    resplist.appern(parameters.get('supportmail'))
                else:
                    resplist.appern('v000529@stokov.ru')

                mail.sendmail(mailparams, resplist, "PR нет данных поставщика",f'Здравствуйте,<br> для инн {form.inn.data} нет данных.')

        pr = PaymentRequest(direction=form.direction.data, payer=form.payer.data, responsible=form.responsible.data,
                                 paymenttype=form.paymenttype.data, porderno=form.porderno.data, invoice=form.invoice.data, invdate=invdate,
                                 amount=form.amount.data, currency=form.currency.data, dept=form.dept.data, contract=form.contract.data,
                            inn=form.inn.data, vendorname=vendorname, status='Черновик')


#        try:
        db.session.commit()
        db.session.add(pr)
        db.session.commit()
        #for file in form.files:
        #    print(file.filename)
        #    file.save(file.filename)
        return redirect(url_for('index'))#redirect('/posts ')
#       except:
 #           flash("При добавлении произошла ошибка", "error")
 #           return "При добавлении произошла ошибка"

    else:
        form.responsible.data=current_user.get_login()

    return render_template("create-pr.html", form=form)


@app.route('/test', methods=['POST','GET'])
def test():
    sql = text("insert into dbo.users (name, email, pwd) values('test','','')")

    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(sql)
        trans.commit()
        return "добавили"
    except:
        trans.rollback()
        return "При добавлении произошла ошибка"
#    print(sql)
#    return redirect('/')


@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h

@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    print("upload")
    if request.method == 'POST':
        file = request.files['file']
#        if file and current_user.verifyExt(file.filename):
        if file:
            try:
                img = file.read()
                res = updateUserAvatar(img, current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара", "error")
                flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара!", "error")

    return redirect(url_for('profile'))


def updateUserAvatar(avatar, user_id):
    print("updateavatar.py")
    if not avatar:
        return False

    try:
        User.query.filter(User.id == user_id).update({'avatar': avatar})
        db.session.commit()
    except:
        print("UpdateUserAvatar Ошибка обновления аватара в БД: ")
        return False
    return True

@app.route('/greet', methods=['POST'])
def greet():
    if 'name' in request.form:
        name = request.form['name']
        return jsonify(message=f'Hello, {name}.')
    return '', 400

if __name__ == "__main__":
    app.run(debug=True, port=parameters.get('port'), host='0.0.0.0')
