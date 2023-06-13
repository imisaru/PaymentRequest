import logging
import mail
import json
import os
import shutil
import datetime
from flask import Flask, render_template, url_for, request, redirect, make_response
from flask import g, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy import create_engine, MetaData, Table, Column, Numeric, Integer, VARCHAR
# from sqlalchemy.engine import result
from sqlalchemy import text, or_, and_
from FDataBase import FDataBase

# from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from UserLogin import UserLogin
# from flask_login import UserMixin
from forms import PRForm, LoginForm
from flask import send_from_directory

errormsg = ""
app = Flask(__name__)
app.secret_key = 'fdgfh78@#5?>gfhf89dx,v06k'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
paramfile = open("params.json")
parameters = json.load(paramfile)
mailparams = {}
mailparams.setdefault('smtpserver', parameters.get("smtpserver"))
mailparams.setdefault("smtplogin", parameters.get("smtplogin"))
mailparams.setdefault("smtppassword", parameters.get("smtppassword"))
app.config['SQLALCHEMY_DATABASE_URI'] = parameters.get('connectionstring')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SECRET_KEY = 'fdgfh78@#5?>gfhf89dx,v06k'
MAX_CONTENT_LENGTH = 1024 * 1024
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"
dbase = None

db = SQLAlchemy(app)
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
level=logging.INFO, filename="pr.log",filemode="a",datefmt='%Y-%m-%d %H:%M:%S')
logging.info(f"started. webserver{parameters.get('webserver')}, connection string {parameters.get('connectionstring')}")
class attachment(db.Model):
    __tablename__ = 'attachment'
    id = db.Column(db.Integer, primary_key=True)
    prid = db.Column(db.Integer)
    filename = db.Column(db.String(256))
    path = db.Column(db.String(256))
   # CreateDate = db.Column(db.DateTime, default=datetime.datetime.today())
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
    approvedate = db.Column(db.Date)
    amount = db.Column(db.Numeric(20, 2))
    currency = db.Column(db.String(3))
    dept = db.Column(db.String(50))
    contract = db.Column(db.String(50))
    inn = db.Column(db.String(12))
    vendorname = db.Column(db.String(250))
    status = db.Column(db.String(20))
    requested = db.Column(db.String(10), default='00000')
    requeststatus = db.Column(db.String(10), default='00000')
    preapproved = db.Column(db.String(1), default='')
    acomment = db.Column(db.String(500), default='')
    pcomment = db.Column(db.String(500), default='')
    accountant_ap = db.Column(db.String(50))
    accountant_bank = db.Column(db.String(50))
#    CreateDate = db.Column(db.DateTime, default=datetime.datetime.today())


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
    approvedate = db.Column(db.DateTime)
    #  CreateDate = db.Column(db.DateTime, default=datetime.datetime.today())


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
    """Закрываем соединение с БД, если оно было установлено"""
    if hasattr(g, 'link_db'):
        g.link_db.close()


@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, dbase)


@app.route('/', methods=["POST", "GET"])
@app.route('/home', methods=["POST", "GET"])
def index():
    global errormsg
    dir = ''
    st = ''
    if request.method == "POST":
        args = []
        if request.form['direction'] > '' and request.form['direction'] != 'Все':
            args.append('dir=' + request.form['direction'])

        if request.form['status'] > '' and request.form['status'] != 'Все':
            args.append('st=' + request.form['status'])

        if len(args) > 0:
            args = '?' + '&'.join(args)
        else:
            args = ''
        print(request.form['status'], args)
        return redirect(url_for('index') + args)

    userrole = ''
    if current_user.is_authenticated:
        print('userrole', parameters.get('userrole'))
        try:
            userrole = getUserByLogin(current_user.get_login()).userrole
        except Exception as e:
            logging.error("index. getUserByLogin " + str(e))
            return redirect("bderror")
        #        if not(parameters.get('userrole')):
        #            userrole = getUserByLogin(current_user.get_login()).userrole
        #            print('home role', userrole, current_user.get_login())
        if userrole == 'accounting':
            sWhere = ""
            if request.args.get('dir') is not None:
                sWhere= f"(direction ='{ request.args.get('dir')}')"

            if request.args.get('st') is not None:
                if request.args.get('st') == 'own':
                    sWhere = f"upper(responsible)=upper('{current_user.get_login()}')"
                elif request.args.get('st') == 'waiting':
                    if sWhere > "":
                        sWhere += " and "
                    sWhere = sWhere + f" (PaymentRequest.status in ('Одобрено')) "

            if sWhere > "":
                sWhere = " where  "+sWhere
            print(sWhere)
            sql = text(f"""select top 100 * from PaymentRequest with(nolock) {sWhere} order by CreateDate desc """)
            try:
                conn = db.engine.connect()
                articles = conn.execute(sql).fetchall()
                conn.close()
            except Exception as e:
                errormsg = str(e)
                logging.error("index. articles. dir. " + str(e))
                return redirect('bderror')

            dir = request.args.get('dir')
            st = request.args.get('st')

        elif userrole == 'admin':
            try:
                articles = PaymentRequest.query.order_by(PaymentRequest.id.desc()).limit(100).all()
            except Exception as e:
                errormsg = str(e)
                logging.error("index. articles admin. " + str(e))
                return redirect('bderror')
        else:
            try:
                print('user ', current_user.get_login())
                articles = PaymentRequest.query.filter(
                    PaymentRequest.status != "Закрыто" and PaymentRequest.responsible == current_user.get_login()).order_by(
                    PaymentRequest.id.desc()).limit(1000).all()
            except Exception as e:
                errormsg = str(e)
                logging.error("index. articles. acc. " + str(e))
                return redirect('bderror')

        try:
            sql = text(f"""select  a.id, a.prid, descr, dept, paymenttype, amount, currency, vendorname, b.responsible, 
            c.name, substring(a.tasktype,charindex(' ',a.tasktype),100) as tasktype 
            from task a with(nolock) left join tasktypes t on a.tasktype=t.tasktype 
            join PaymentRequest b with(nolock) on a.prid=b.id left join users c on b.responsible=c.login 
             where a.taskstatus='Created' and isnull(a.isactive,'1')='1' and upper(a.assignee)=upper('{current_user.get_login()}')""")

            conn = db.engine.connect()
            tasks = conn.execute(sql).fetchall()
            conn.close()
        except Exception as e:
            errormsg = str(e)
            logging.error("index. tasks " + str(e))
            return redirect('/bddderror')
    else:
        articles = None
        tasks = None

    return render_template("index.html", articles=articles, tasks=tasks, userrole=userrole, dir=dir, st=st)


@app.route('/payments', methods=["POST", "GET"])
@login_required
def payments():
    if request.method == "POST":
        print("request.form['action']", request.form['action'])
        args = []
        if request.form['action'] != "Оплачено":

            if request.form['prno'] > '':
                args.append('prno=' + request.form['prno'])
            elif request.form['trno'] > '':
                args.append('trno=' + request.form['trno'])
            else:
                args.append('date1=' + request.form['date1'] + '&date2=' + request.form['date2'])

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
            if len(args) > 0:
                args = '?' + '&'.join(args)
            print(args)
        if request.form['action'] == "Ввести платеж по отмеченым":
            conn = db.engine.connect()
            payments = []
            for req in request.form:
                print(req, req[:5], req[5:])
                if req[:5] == 'check':
                    sql = text(f"""SELECT a.id, a.direction, a.payer, a.responsible, a.amount, a.currency, a.dept, 
                    a.inn, a.vendorname, a.trno, a.acomment, b.name, b.email
                    FROM PaymentRequest AS a LEFT OUTER JOIN users AS b ON a.responsible = b.login where a.id={req[5:]}""")
                    pmt = conn.execute(sql).first()
                    if pmt is not None:
                        d = {'id': req[5:], 'trno': pmt.trno, 'payer': pmt.payer, 'vendorname': pmt.vendorname, 'amount': pmt.amount, 'currency': pmt.currency}
                        payments.append(d)
            if len(payments) > 0:
                return render_template("masspayment.html", payments=payments)
        elif request.form['action'] == "Оплачено":
            print('Оплатчено!!')
            conn = db.engine.connect()
            for req in request.form:
                print(req, req[:4], req[4:])
                if req[:4] == 'prid':
                    sql = text(f"""update PaymentRequest set status='Оплачено', pcomment='{request.form['pcomment']}',
                     paymentdate='{request.form.get("pdate")}'
                     where id={req[4:]}""")
                    print(sql)
                    conn.execute(sql)
                    conn.commit()
                    sql = text(f"""SELECT a.vendorname, b.name, b.email FROM PaymentRequest AS a 
                    LEFT OUTER JOIN users AS b ON a.responsible = b.login where a.id={req[5:]}""")
                    pmt = conn.execute(sql).first()
                    if pmt is not None:
                        mail.sendmail(mailparams, pmt.email, f"PR {req[5:]}. Оплачено",
                                  f'Здравствуйте,<br> PR в пользу {pmt.vendorname} оплачено. Дата оплаты {request.form["pdate"]}. Комментарий {request.form["pcomment"]}.')
                        logging.info(
                            f"mail sent pr {req[5:]}. to {pmt.email}. subj: PR {req[5:]}. Оплачено")

        return redirect(url_for('payments') + args)

    fparams = {}
    if request.args.get('sort') == 'vendor':
        sOrderBy = "vendorname"
        fparams['OrderBy'] = "Получатель платежа"
    else:
        sOrderBy = "plandate desc"
        fparams['OrderBy'] = "Дата платежа планируемая"

    sWhere = f"status='Передано в оплату'"

    if request.args.get('prno') is not None:
        fparams['prno'] = request.args.get('prno')
        sWhere = f"a.id={str(request.args.get('prno'))}"

    if request.args.get('trno') is not None:
        fparams['trno'] = request.args.get('trno')
        print(fparams['trno'])
        sWhere = f"upper(a.trno) like upper('{str(request.args.get('trno'))}%')"

    if request.args.get('date1') is not None and request.args.get('date2') is not None and request.args.get('date1')!='' and request.args.get('date2')!='':
        print(f"request '{request.args.get('date1')}'")
        sdate1 = datetime.date.strftime(datetime.datetime.strptime(request.args.get('date1'), '%Y-%m-%d'), r'%m/%d/%Y')
        sdate2 = datetime.date.strftime(datetime.datetime.strptime(request.args.get('date2'), '%Y-%m-%d'), r'%m/%d/%Y')
        sWhere = f"status='Передано в оплату' and isnull(plandate,trdate)>='{sdate1}' and isnull(plandate,trdate)<='{sdate2}'"

    if request.args.get('le') is not None:
        if request.args.get('le') == 'SMO':
            fparams['le'] = "SMO"
            sWhere += f" and payer='Стоков Машинное Оборудование АО'"
        if request.args.get('le') == 'SK':
            fparams['le'] = "SK"
            sWhere += f" and payer='Стоков Компоненты ООО'"
        if request.args.get('le') == 'SST':
            fparams['le'] = "SST"
            sWhere += f" and payer='Стоков Конструкция ООО'"

    sql = text(f"""select a.id, a.direction, payer, responsible, b.name as respname, paymenttype, amount, currency, dept, 
    vendorname, trno, trdate, plandate, acomment, max(filename) as file1, min(filename) as file2, count(c.id) as nfiles 
    from PaymentRequest a left join users b on a.responsible=b.login left join attachment c on a.id=c.prid 
    where {sWhere}
    group by a.id, a.direction, payer, responsible, b.name, paymenttype, amount, currency, dept, 
    vendorname, trno, trdate, plandate, acomment
    order by {sOrderBy}""")
    #  print(sql)

    conn = db.engine.connect()
    articles = conn.execute(sql).fetchall()
    conn.close()
    print('request.args.get(date2)', request.args.get('date2'))
    date1 = request.args.get('date1')
    date2 = request.args.get('date2')
    if date2 is None:
        date2 = datetime.date.today() + timedelta(days=10)
    if date1 is None:
        date1 = datetime.date.today() - timedelta(days=90)
    return render_template("payments.html", articles=articles, date1=date1, date2=date2, fparams=fparams)


@app.route('/archive', methods=["POST", "GET"])
@login_required
def archive():
    global errormsg
    if request.method == "POST":
        args = []

        if request.form['prno'] > '':
            args.append('prno=' + request.form['prno'])
        elif request.form['trno'] > '':
            args.append('trno=' + request.form['trno'])
        else:
            args.append('date1=' + request.form['date1'] + '&date2=' + request.form['date2'])
            if request.form['pmtdate1'] is not None and request.form['pmtdate1'] != '':
                args.append('pmtdate1=' + request.form['pmtdate1'])
            if request.form['pmtdate2'] is not None and request.form['pmtdate2'] != '':
                args.append('pmtdate2=' + request.form['pmtdate2'])

        if request.form['status'] > '' and request.form['status'] !='Все':
            args.append('status=' + request.form['status'])
        if request.form['direction'] > '' and request.form['direction'] !='Все':
            args.append('direction=' + request.form['direction'])

        if request.form['requestor'] > '':
            args.append('requestor=' + request.form['requestor'])

        if request.form['payer'] == 'Стоков Машинное Оборудование АО':
            args.append('le=SMO')
        if request.form['payer'] == 'Стоков Компоненты ООО':
            args.append('le=SK')
        if request.form['payer'] == 'Стоков Конструкция ООО':
            args.append('le=SST')

        if request.form['vendor'] > '':
            args.append('vendor=' + request.form['vendor'])
        if request.form['inv'] > '':
            args.append('inv=' + request.form['inv'])

        if request.form['sorting'] == 'Дата планируемая платежа':
            args.append('sort=plandate')
        if request.form['sorting'] == 'Получатель платежа':
            args.append('sort=vendor')
        if request.form['sorting'] == 'Дата счета':
            args.append('sort=invdate')
        if len(args) > 0:
            args = '?' + '&'.join(args)
        return redirect(url_for('archive') + args)

    sWhere = ""
    fparams = {}
    if request.args.get('sort') == 'vendor':
        sOrderBy = "vendorname"
        fparams['OrderBy'] = "Получатель платежа"
    elif request.args.get('sort') == 'invdate':
        sOrderBy = "invdate"
        fparams['OrderBy'] = "Дата счета"
    else:
        sOrderBy = "plandate desc"
        fparams['OrderBy'] = "Дата платежа планируемая"

    if request.args.get('prno') is not None:
        fparams['prno'] = request.args.get('prno')
        sWhere = f"a.id={str(request.args.get('prno'))}"

    if request.args.get('trno') is not None:
        fparams['trno'] = request.args.get('trno')
        print(fparams['trno'])
        sWhere = f"upper(a.trno) like upper('{str(request.args.get('trno'))}%')"

    if request.args.get('date1') is not None and request.args.get('date2') is not None and request.args.get('date1')!='' and request.args.get('date2')!='':
        sdate1 = datetime.date.strftime(datetime.datetime.strptime(request.args.get('date1'), '%Y-%m-%d'), r'%m/%d/%Y')
        sdate2 = datetime.date.strftime(datetime.datetime.strptime(request.args.get('date2'), '%Y-%m-%d'), r'%m/%d/%Y')
        print(sdate2, type(sdate2))
        sWhere = f"isnull(plandate,'{sdate1}')>='{sdate1}' and isnull(plandate,'{sdate2}')<='{sdate2}'"

    if request.args.get('pmtdate1') is not None and request.args.get('pmtdate1') != '' :
        spmtdate1 = datetime.date.strftime(datetime.datetime.strptime(request.args.get('pmtdate1'), '%Y-%m-%d'), r'%m/%d/%Y')
    else:
        spmtdate1 = None
    print(request.args.get('pmtdate2'))
    if request.args.get('pmtdate2') is not None:
        spmtdate2 = datetime.date.strftime(datetime.datetime.strptime(request.args.get('pmtdate2'), '%Y-%m-%d'), r'%m/%d/%Y')
    else:
        spmtdate2 = None

    if spmtdate1 is not None and spmtdate2 is not None:
        sWhere = f"isnull(paymentdate,'01/01/2000')>='{spmtdate1}' and isnull(paymentdate,'01/01/2000')<='{spmtdate2}'"
    elif spmtdate1 is not None and spmtdate2 is None:
        sWhere = f"isnull(paymentdate,'01/01/2000')='{spmtdate1}'"
    elif spmtdate2 is not None and spmtdate1 is None:
        sWhere = f"isnull(paymentdate,'01/01/2000')='{spmtdate2}'"

    if request.args.get('le') is not None:
        if request.args.get('le') == 'SMO':
            fparams['le'] = "SMO"
            if sWhere != '':
                sWhere += ' and '
            sWhere += f"payer='Стоков Машинное Оборудование АО'"
        if request.args.get('le') == 'SK':
            fparams['le'] = "SK"
            if sWhere != '':
                sWhere += ' and '
            sWhere += f"payer='Стоков Компоненты ООО'"
        if request.args.get('le') == 'SST':
            if sWhere != '':
                sWhere += ' and '
            fparams['le'] = "SST"
            sWhere += f"payer='Стоков Конструкция ООО'"

    statuses = ["Черновик", "Доработка", "Ожидание утверждения", "Отказано в утверждении", "Одобрено", "Передано в оплату",
                "Оплачено", "Взаимозачет", "Закрыто"]

    fparams['status'] = "Все"
    if request.args.get('status') is not None:
        for st in statuses:
            if request.args.get('status') == st:
                fparams['status'] = st
                if sWhere != '':
                    sWhere += ' and '
                sWhere += f"status='{st}'"

    fparams['direction'] = "Все"
    if request.args.get('direction') is not None:
        fparams['direction'] = request.args.get('direction')
        if sWhere != '':
            sWhere += ' and '
        sWhere += f"a.direction='{request.args.get('direction')}'"

    if request.args.get('requestor') is not None and request.args.get('requestor') != "":
        fparams['requestor'] = request.args.get('requestor')
        if sWhere != '':
            sWhere += ' and '
        sWhere += f"upper(a.responsible+b.name) like upper('%{request.args.get('requestor')}%')"

    if request.args.get('vendor') is not None and request.args.get('vendor') != "":
        fparams['vendor'] = request.args.get('vendor')
        if sWhere != '':
            sWhere += ' and '
        sWhere += f"upper(a.inn+a.vendorname) like upper('%{request.args.get('vendor')}%')"

    if request.args.get('inv') is not None and request.args.get('inv') != "":
        fparams['inv'] = request.args.get('inv')
        if sWhere != '':
            sWhere += ' and '
        sWhere += f"upper(invoice) like upper('%{request.args.get('inv')}%')"

    sql = f"""select top 1000 a.id, a.direction, payer, responsible, b.name as respname, paymenttype, amount, currency, dept, 
    vendorname, trno, trdate, plandate, acomment, a.inn, a.invoice, cast(a.invdate as date) as invdate, max(filename) as file1, min(filename) as file2, count(c.id) as nfiles,
    b.name AS respname, status, approvedate  from PaymentRequest a 
    left join users b on a.responsible=b.login left join attachment c on a.id=c.prid """
    if sWhere != "":
        sql += f"where {sWhere}"
    sql = text(sql + f""" group by a.id, a.direction, status, payer, responsible, b.name, paymenttype, amount, currency, dept, 
    vendorname, trno, trdate, plandate, acomment, a.inn, a.invoice, a.invdate, approvedate
    order by {sOrderBy}""")

    try:
        conn = db.engine.connect()
        articles = conn.execute(sql).fetchall()
        conn.close()
    except Exception as e:
        errormsg = str(e)
        logging.error(str(e))
        return redirect('bderror')

    print('request.args.get(date2)', request.args.get('date2'))
    date1 = request.args.get('date1')
    date2 = request.args.get('date2')
    #if date2 is None:
    #    date2 = datetime.date.today() + timedelta(days=10)
    #if date1 is None:
    #    date1 = datetime.date.today() - timedelta(days=90)
    return render_template("archive.html", articles=articles, date1=date1, date2=date2, fparams=fparams)


@app.route('/about')
def about():
    return render_template("about.html")


@app.route("/login1", methods=["POST", "GET"])
def login1():
    global errormsg
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        # user = db.session.query(User).filter(User.login == request.form['login']).first()
        try:
            user = User.query.filter(User.login == request.form['login']).first()
        except Exception as e:
            errormsg = str(e)
            logging.error(str(e))
            return redirect("bderror")
        # user = getUserByLogin(request.form['login'])
        if user and check_password_hash(user.pwd, request.form['psw']):
            userlogin = UserLogin().create(user)
            rm = True if request.form.get('remainme') else False
            # parameters['userrole'] = getUserByLogin(current_user.get_login()).userrole
            login_user(userlogin, remember=rm)
            #            return redirect(url_for('index'))
            return redirect(request.args.get("next") or url_for("index"))
        flash("Неверная пара логин/пароль", "error")
    return render_template("login.html")


@app.route('/testf', methods=['POST', 'GET'])
def testf():
    return copyprfiles(22)


def copyprfiles(prid):
    pr = PaymentRequest.query.filter(PaymentRequest.id == prid).first()
    files = attachment.query.filter(attachment.prid == prid).all()
    print('copyprfiles', pr.trno)
    trno = pr.trno if pr.trno is not None else ''
    trno += '_' + str(prid)

    rstr = 'nothing'
    dpath = parameters.get('archivepath')
    if dpath is None:
        dpath = 'prarchive'
    if not os.path.exists(os.path.join(dpath, trno)):
        os.makedirs(os.path.join(dpath, trno))
    for f in files:
        sfilepath = os.path.join('archive', str(prid), f.filename)
        dfilepath = os.path.join(dpath, trno, f.filename)

        if os.path.isfile(sfilepath):
            shutil.copy2(sfilepath, dfilepath)

            rstr = "copied from " + sfilepath + " into " + dfilepath

    return rstr


@app.route("/login", methods=["POST", "GET"])
def login():
    global errormsg
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    print('login 1')
    form = LoginForm()

    if form.validate_on_submit():
        try:
            # user = dbase.getUserByEmail(form.email.data)
            user = User.query.filter(User.login == request.form['login']).first()
            print('login user', request.form['login'], user.name)
            if user.pwd != "" and user.pwd is not None:
                if user and check_password_hash(user.pwd, form.psw.data):
                    userlogin = UserLogin().create(user)
                    rm = form.remember.data
                    login_user(userlogin, remember=rm)
                    # parameters['userrole'] = getUserByLogin(current_user.get_login()).userrole
                    return redirect(request.args.get("next") or url_for("index"))
            else:
                return redirect(f"changepass?u={request.form['login']}")
        except Exception as e:
            errormsg = str(e)
            logging.error("login. user. " + str(e))
            return redirect("bderror")

        flash("Неверная пара логин/пароль", "error")
        return render_template("login1.html", form=form)
    else:
        print('novalid user')
    return render_template("login1.html", form=form)


@app.route('/bderror')
def bderror():
    global errormsg
    print('errormsg',errormsg)
    return render_template("bderror.html", msg=errormsg)


@app.route('/logout')
@login_required
def logout():
    # parameters['userrole'] = ""
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile', methods=["POST", "GET"])
@login_required
def profile():
    #    return f"""<p><a href="{url_for('logout')}">Выйти из профиля</a><p>user info: {current_user.get_id()}"""
    uid = current_user.get_id()
    sql = text(f"select * from users where id={uid}")
    conn = db.engine.connect()
    rec = conn.execute(sql).fetchone()
    if request.method == "POST":
        teluser = request.form['teluser']
        if teluser[0] == '@':
            teluser = teluser [1:]
        sql = text(f"update users set teluser='{teluser}' where id={uid}")
        conn.execute(sql)
        conn.commit()
        sql = text(f"select * from users where id={uid}")
        conn = db.engine.connect()
        rec = conn.execute(sql).fetchone()
    conn.close()

    return render_template("profile.html", fparams=rec)


@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        if len(request.form['login']) != 7 or request.form['login'].upper()[0] != 'V':
            flash("Логин должен начинаться с v и быть длинной 7 символов", "error")
            return render_template("register.html")
        # if len(request.form['psw'])<4:
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
        phash = generate_password_hash(request.form['psw'])
        res = addUser(request.form['name'], request.form['login'], email, phash)
        if res:
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))
        else:
            flash("Ошибка при добавлении в БД", "error")

    return render_template("register.html")


@app.route('/changepass', methods=["POST", "GET"])
def changepass():
    if request.method == "POST":
        if request.form['psw1'] != request.form['psw2']:
            flash("Пароль не совпадает с контролем", "error")
            return render_template("changepass.html")
        else:
            if current_user.is_authenticated:
                userlogin = current_user.get_login()
            else:
                userlogin = request.args.get('u')
                if userlogin == '' or userlogin is None:
                    return redirect(url_for('login'))

            userpass = selectfield("users","pwd","login", userlogin)

            print(userlogin, userpass, type(userpass), request.form['oldpsw'])
            if userpass!="" and userpass is not None:
                if not(check_password_hash(userpass, request.form['oldpsw'])):
                    flash("не верный пароль", "error")
                    return render_template("changepass.html")

            phash = generate_password_hash(request.form['psw1'])
            conn = db.engine.connect()
            sql = text(f"update users set pwd='{phash}' where login='{userlogin}'")
            conn.execute(sql)
            conn.commit()
            flash("Пароль изменен", "success")

        return redirect(url_for('index'))

    return render_template("changepass.html")


@app.route('/test3', methods=['POST', 'GET'])
def test3():
    name = "n2sf"
    email = "emareil"
    sql = text(f"select count(*) from dbo.users where name = '{name}' or email='{email}'       ")
    conn = db.engine.connect()
    res = conn.execute(sql)
    for row in res:
        break
    return "test3 finished" + str(row[0])


# def getUser(user_id):
#    try:
#        sql = text(f"select top 1 login, email, name, pwd, userrole from dbo.users where id = {user_id} ")
#        conn = db.engine.connect()
#        res = conn.execute(sql)
#        for row in res:
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


def getUserByLogin(userlogin):
    global errormsg
    try:
        user = User.query.filter(User.login == userlogin).first()
        return user
    except Exception as e:
        errormsg = str(e)
        logging.error('getUserByLogin '+str(e))
        return redirect("/bderror")

    return False


def addUser(name, userlogin, email, hpsw):
    global errormsg
    sql = text(
        f"select count(*) from dbo.users where upper(login) = upper('{userlogin}') or upper(email)=upper('{email}')")
    conn = db.engine.connect()
    res = conn.execute(sql)
    for row in res:
        break
    if row[0] > 0:
        print("Пользователь с таким login|email уже существует")
        return False

    sql = text(f"insert into dbo.users (name, login, email, pwd) values('{name}', '{userlogin}', '{email}','{hpsw}')")
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(sql)
        trans.commit()
        print("adduser добавили")
    except Exception as e:
        errormsg = str(e)
        logging.error("adduser " + str(e))
        trans.rollback()
        print("adduser При добавлении произошла ошибка")
        return False

    return True


@app.route('/test1', methods=['GET'])
def test1():
#    a = getUserByLogin('v000529')  # addUser("u","p","h")
    return redirect("/bderror") #  "test1 finished" + a.userrole


@app.route('/posts/<int:postid>')
def post_detail(postid):
    #  article = PaymentRequest.query.get(postid)
    conn = db.engine.connect()
    #article = PaymentRequest.query.get(prid)
    sql = text(f"""SELECT a.id, a.direction, a.payer, a.responsible, a.paymenttype, a.porderno, a.invoice, 
    a.invdate, a.amount, a.currency, a.dept, a.contract, a.inn, a.CreateDate, a.vendorname, a.uuid, a.status, 
    a.requested, a.requeststatus, a.trno, a.trdate, a.paymentdate, a.acomment, a.pcomment, a.plandate, a.isfinished, 
    a.preapproved, b.name, b.email
    FROM PaymentRequest AS a LEFT OUTER JOIN users AS b ON a.responsible = b.login where a.id={postid}""")
    article = conn.execute(sql).first()

    tasks = task.query.filter(task.prid == postid).order_by(task.id.desc()).all()
    files = attachment.query.filter(attachment.prid == postid)
    return render_template("post_detail.html", article=article, tasks=tasks, files=files)

@app.route('/testa25', methods=['GET'])
def testa25():
    approvepr(25)


@app.route('/testa18', methods=['GET'])
def testa18():
    approvepr(18)

def approvepr(prid):
    conn = db.engine.connect()
    sql = text(f"""SELECT id FROM task where prid={prid}""")
    tasks = conn.execute(sql).all()
    for t in tasks:
        approvetask(prid, t.id)

def approvetask(prid, taskid):
    global errormsg
    conn = db.engine.connect()
    sql = text(f"""SELECT a.id, a.direction, a.payer, a.responsible, a.paymenttype, a.porderno, a.invoice, 
    a.invdate, a.amount, a.currency, a.dept, a.contract, a.inn, a.CreateDate, a.vendorname, a.uuid, a.status, 
    a.requested, a.requeststatus, a.trno, a.trdate, a.paymentdate, a.acomment, a.pcomment, a.plandate, a.isfinished, 
    a.preapproved, b.name, b.email
    FROM PaymentRequest AS a LEFT OUTER JOIN users AS b ON a.responsible = b.login where a.id={prid}""")
    article = conn.execute(sql).first()
    print(len(article), article.id)
    sql = text(f"""select  a.id, a.prid, b.responsible, c.name as requestorname, a.scomment, a.acomment, a.tasktype, 
    descr from task a left join tasktypes t on a.tasktype=t.tasktype join PaymentRequest b on a.prid=b.id 
    left join users c on b.responsible=c.login 
    where a.id='{taskid}'""")
    tasks = conn.execute(sql).first()

    sql = text(f"update task set taskstatus='Approved', approvedate=getdate() where id={taskid}")
    conn.execute(sql)
    conn.commit()
    n = -1
    if tasks.tasktype == 'Approvement std':
        n = 0
    if tasks.tasktype == 'Approvement m5':
        n = 1
    if tasks.tasktype == 'Approvement nondeduct':
        n = 2
    if tasks.tasktype == 'Approvement adv':
        n = 3
    if tasks.tasktype == 'Approvement noorg':
        n = 4
    if n > -1:
        if article.requeststatus is None:
            article.requeststatus = '0' * 5
        print(type(article), article.requeststatus, article.requeststatus[:n] + "+" + article.requeststatus[n + 1:])
        #article.requeststatus = article.requeststatus[:n] + "+" + article.requeststatus[n + 1:]
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
            msg = "<p>Здравствуйте,<br>Ваш запрос на утверждение платежа в пользу " + article.vendorname + \
                  " сумма " + str(article.amount) + " " + article.currency + "</p>"
            msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
            msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
            msg += f"<p><b>был одобрен и будет передан в бухгалтерию</b></p>"
            msg += '<p>Посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/posts/' + str(prid) + '">Payment request</a></p>'
            print('mail1', respmail[0])
            try:
                mail.sendmail(mailparams, respmail, subj, msg)
            except Exception as e:
                errormsg = str(e)
                logging.error("sendmail Oдобрено " + str(e))
                return redirect("bderror", msg=str(e))

            logging.info(f"mail sent pr {prid}. to {respmail}. subj: {subj}")
            if parameters.get('accountingmail') is not None and parameters.get('accountingmail') > '':
                subj = "PR " + str(prid) + " Одобрен. Готов к обработке"
                msg = "<p>Здравствуйте,<br>Запрос на утверждение платежа в пользу " + article.vendorname \
                      + " сумма " + str(article.amount) + " " + article.currency + "</p>"
                msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
                msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
                msg += f"<p><b>был одобрен можно приступать к обработке</b></p>"
                msg += '<p>Посмотреть подробности можно по ссылке <a href="' + parameters.get(
                    "webserver") + '/posts/' + str(prid) + '">Payment request</a></p>'
                mail.sendmail(mailparams, parameters.get('accountingmail'), subj, msg)
                logging.info(f"mail sent pr {prid}. to {parameters.get('accountingmail')}. subj: {subj}")

    sql = text(
        f"update task set taskstatus='Approved' where id={taskid}")
    conn.execute(sql)
    conn.commit()


@app.route('/approve/<int:prid>/<int:taskid>', methods=['GET', 'POST'])
def approve(prid, taskid):
    ulogin = current_user.get_login()
    conn = db.engine.connect()
    #article = PaymentRequest.query.get(prid)
    sql = text(f"""SELECT a.id, a.direction, a.payer, a.responsible, a.paymenttype, a.porderno, a.invoice, 
    a.invdate, a.amount, a.currency, a.dept, a.contract, a.inn, a.CreateDate, a.vendorname, a.uuid, a.status, 
    a.requested, a.requeststatus, a.trno, a.trdate, a.paymentdate, a.acomment, a.pcomment, a.plandate, a.isfinished, 
    a.preapproved, b.name, b.email
    FROM PaymentRequest AS a LEFT OUTER JOIN users AS b ON a.responsible = b.login where a.id={prid}""")
    article = conn.execute(sql).first()
    files = attachment.query.filter(attachment.prid == prid)
    #    tasks =task.query.filter(task.id == taskid).first()
    sql = text(f"""select  a.id, a.prid, b.responsible, c.name as requestorname, a.scomment, a.acomment, a.tasktype, 
    descr, assignee from task a left join tasktypes t on a.tasktype=t.tasktype join PaymentRequest b on a.prid=b.id 
    left join users c on b.responsible=c.login 
    where a.id='{taskid}'""")
    tasks = conn.execute(sql).first()
    if ulogin != tasks.assignee and ulogin != 'v000529':
        flash("Вы не можете это одобрять", "error")
        print(ulogin, tasks.assignee)
        return redirect(url_for('index'))
    if request.method == 'POST':
        print('approve', request.form['action'])
        if request.form['action'] == "Утвердить":
            sql = text(f"update task set taskstatus='Approved', approvedate=getdate(), approvetype='web' where id={taskid}")
            conn.execute(sql)
            conn.commit()
            n = -1
            if tasks.tasktype == 'Approvement std':
                n = 0
            if tasks.tasktype == 'Approvement m5':
                n = 1
            if tasks.tasktype == 'Approvement nondeduct':
                n = 2
            if tasks.tasktype == 'Approvement adv':
                n = 3
            if tasks.tasktype == 'Approvement noorg':
                n = 4
            if n > -1:
                rstatus = article.requeststatus
                if rstatus is None or len(rstatus) == 0:
                    rstatus = '0' * 5

                rstatus = rstatus[:n] + "+" + rstatus[n + 1:]
                sql = text(f"update PaymentRequest set requeststatus='{rstatus}' where id={prid}")
                conn.execute(sql)
                conn.commit()

                isclosed = True
                for i in range(5):
                    if article.requested[i] != '0':
                        if rstatus[i] != "+":
                            isclosed = False
                            break

                if isclosed:
                    sql = text(f"update PaymentRequest set status='Одобрено', approvedate=getdate() where id={prid}")
                    conn.execute(sql)
                    conn.commit()

                    user = User.query.filter(User.login == article.responsible).first()
                    respmail = user.email

                    subj = "PR " + str(prid) + " Одобрено"
                    msg = "<p>Здравствуйте,<br>Ваш запрос на утверждение платежа в пользу " + article.vendorname + \
                          " сумма " + str(article.amount) + " " + article.currency + "</p>"
                    msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
                    msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
                    msg += f"<p><b>был одобрен и будет передан в бухгалтерию</b></p>"
                    msg += '<p>Посмотреть подробности можно по ссылке <a href="' + parameters.get(
                        "webserver") + '/posts/' + str(prid) + '">Payment request</a></p>'
                    print('mail1', respmail[0])
                    mail.sendmail(mailparams, respmail, subj, msg)
                    if parameters.get('accountingmail') is not None and parameters.get('accountingmail') > '':
                        subj = "PR " + str(prid) + " Одобрен. Готов к обработке"
                        msg = "<p>Здравствуйте,<br>Запрос на утверждение платежа в пользу " + article.vendorname \
                              + " сумма " + str(article.amount) + " " + article.currency + "</p>"
                        msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
                        msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
                        msg += f"<p><b>был одобрен можно приступать к обработке</b></p>"
                        msg += '<p>Посмотреть подробности можно по ссылке <a href="' + parameters.get(
                            "webserver") + '/posts/' + str(prid) + '">Payment request</a></p>'
                        mail.sendmail(mailparams, parameters.get('accountingmail'), subj, msg)

            sql = text(
                f"update task set taskstatus='Approved', acomment='{request.form['acomment']}' where id={taskid}")
            conn.execute(sql)
            conn.commit()
            return redirect(url_for('index'))
        if request.form['action'] == "Отказать":
            print("отказать!", taskid)
            # task.query.filter(task.id == taskid).update({'taskstatus': 'Refused'})
            # db.session.commit
            # task.query.filter(task.id == taskid).update({'acomment': request.form['acomment']})
            # db.session.commit
            sql = text(f"update task set taskstatus='Refused', acomment='{request.form['acomment']}' where id={taskid}")
            conn.execute(sql)
            conn.commit()

            #            conn.close
            #            conn = db.engine.connect()
            #            sql = text(f"update PaymentRequest set [status]='Отказано в утверждении' where id={prid}")
            PaymentRequest.query.filter(PaymentRequest.id == prid).update({'status': 'Отказано в утверждении'})
            #            print(sql)
            #            conn.execute(sql)
            #            conn.commit
            db.session.commit()
            conn.close()

            user = User.query.filter(User.login == article.responsible).first()
            respmail = user.email

            subj = "PR " + str(prid) + " Rejected"
            msg = "<p>Здравствуйте,<br>Ваш запрос на утверждение платежа в пользу " + article.vendorname + " сумма " + \
                  str(article.amount) + " " + article.currency + "</p>"
            msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
            msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
            msg += f"<p><b>был отклонен</b> Комментарий: {request.form['acomment']}</p>"
            msg += '<p>Посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/posts/' + str(prid) + '">Payment request</a></p>'
            mail.sendmail(mailparams, respmail, subj, msg)
            return redirect(url_for('index'))
    return render_template("approve.html", article=article, files=files, task=tasks)


@app.route('/process/<int:prid>', methods=['POST', 'GET'])
def process(prid):
    print('process')
    article = PaymentRequest.query.get(prid)
    #    files = department.query.filter(department.id == article.id)
    files = attachment.query.filter(attachment.prid == prid)
    dept = department.query.filter(department.name == article.dept).first()
    print(dept)
    if request.method == 'POST':
        if article.preapproved:
            conn = db.engine.connect()
            sql = text(f"update PaymentRequest set status='Одобрено' where id={prid}")
            conn.execute(sql)
            conn.commit()
            return redirect(url_for('index'))
        subj = "PR " + str(prid) + " Approve"
        msg = "<p>Здравствуйте,<br>Направляем Вам запрос на утверждение платежа в пользу " + article.vendorname + \
              " сумма " + str(article.amount) + " " + article.currency + "</p>"
        msg += "Заявитель " + getUserByLogin(current_user.get_login()).name + "<br>"
        msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
        msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
        msg += f"<p>Комментарий заявителя: {request.form.get('scomment')}</p>"
        curtask = None
        flagline = '0' * 5
        flag = True if request.form.get('std') == 'on' else False
        if flag:
            flagline = '1' + flagline[1:]
            task.query.filter(task.prid == prid, task.tasktype == 'Approvement std').update({'isactive': '0'})
            db.session.commit()
            nrec = len(
                task.query.filter(task.prid == prid, task.tasktype == 'Approvement std', task.taskstatus == "Created",
                                  task.isactive == '1').all())
            if nrec == 0:
                tstd = task(prid=prid, tasktype="Approvement std", taskstatus="Created", assignee=dept.approver,
                            assigneemail=dept.approvermail, scomment=request.form['scomment'])
                db.session.add(tstd)
                db.session.commit()

            curtask = task.query.filter(task.prid == prid, task.tasktype == "Approvement std",
                                       task.taskstatus == "Created", task.assignee == dept.approver).order_by(
                task.id.desc()).first()
            print('taskid', curtask.id)
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(prid) + '/' + str(curtask.id) + \
                   '''">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение через ответный имейл. 
                Не отвечайте на это письмо, если хотите отклонить, отправить на доработку заявку или оставить 
                комментарий!</b>'''

            mail.sendmail(mailparams, dept.approvermail, subj + ' std', msg1)
        flag = True if request.form.get('m5') == 'on' else False
        if flag:
            flagline = flagline[:1] + '1' + flagline[:2]
            task.query.filter(task.prid == prid, task.tasktype == 'Approvement m5').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(task.prid == prid, task.tasktype == 'Approvement m5',
                                         task.taskstatus == "Created").all())
            if nrec == 0:
                tstd = task(prid=prid, tasktype="Approvement m5", taskstatus="Created", assignee=dept.approver,
                            assigneemail=dept.approvermail, scomment=request.form['scomment'])
                db.session.add(tstd)
                db.session.commit()
            curtask = task.query.filter(task.prid == prid, task.tasktype == "Approvement std",
                                       task.taskstatus == "Created", task.assignee == dept.approver).order_by(
                task.id.desc()).first()
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(prid) + '/' + \
                   str(curtask.id) + '''">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение через 
                ответный имейл. Не отвечайте на это письмо, если хотите отклонить, отправить на доработку заявку или 
                оставить комментарий!</b>'''
            mail.sendmail(mailparams, dept.approvermail, subj + ' >5m', msg1)

        if request.form.get('nondeduct'):
            flagline = flagline[:2] + '1' + flagline[:3]
            task.query.filter(task.prid == prid, task.tasktype == 'Approvement nondeduct').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(
                task.prid == prid and task.tasktype == 'Approvement nondeduct' and task.taskstatus == "Created").all())
            if nrec == 0:
                tstd = task(prid=prid, tasktype="Approvement nondeduct", taskstatus="Created", assignee=dept.approver,
                            assigneemail=dept.approvermail, scomment=request.form['scomment'])
                db.session.add(tstd)
                db.session.commit()
            curtask = task.query.filter(task.prid == prid, task.tasktype == "Approvement nondeduct",
                                       task.taskstatus == "Created", task.assignee == dept.approver).order_by(
                task.id.desc()).first()
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(prid) + '/' + \
                   str(curtask.id) + '''">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение через 
                ответный имейл. Не отвечайте на это письмо, если хотите отклонить, отправить на доработку заявку или 
                оставить комментарий!</b>'''
            mail.sendmail(mailparams, dept.approvermail, subj + ' nondeduct', msg1)

        if request.form.get('adv'):
            flagline = flagline[:3] + '1' + flagline[:4]
            task.query.filter(task.prid == prid, task.tasktype == 'Approvement adv').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(task.prid == prid, task.tasktype == 'Approvement adv',
                                         task.taskstatus == "Created").all())
            if nrec == 0:
                tstd = task(prid=prid, tasktype="Approvement adv", taskstatus="Created", assignee=dept.approver,
                            assigneemail=dept.approvermail, scomment=request.form['scomment'])
                db.session.add(tstd)
                db.session.commit()
            curtask = task.query.filter(task.prid == prid, task.tasktype == "Approvement adv",
                                       task.taskstatus == "Created", task.assignee == dept.approver).order_by(
                task.id.desc()).first()
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(prid) + '/' + \
                   str(curtask.id) + '''">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение 
                через ответный имейл. Не отвечайте на это письмо, если хотите отклонить, отправить на доработку 
                заявку или оставить комментарий!</b>'''
            mail.sendmail(mailparams, dept.approvermail, subj + ' аванс', msg1)

        if request.form.get('noorg'):
            flagline = flagline[:4] + '1' + flagline[:5]
            task.query.filter(task.prid == prid, task.tasktype == 'Approvement noorg').update({'isactive': '0'})
            db.session.commit()
            nrec = len(task.query.filter(task.prid == prid, task.tasktype == 'Approvement noorg',
                                         task.taskstatus == "Created").all())
            if nrec == 0:
                tstd = task(prid=prid, tasktype="Approvement noorg", taskstatus="Created", assignee=dept.approver,
                            assigneemail=dept.approvermail, scomment=request.form['scomment'])
                db.session.add(tstd)
                db.session.commit()
            assignee = selectfield("users", "email", "name", request.form.get('approvernoorg'))
            curtask = task.query.filter(task.prid == prid, task.tasktype == "Approvement noorg",
                                        task.taskstatus == "Created",
                                        task.assignee == dept.approver).order_by(task.id.desc()).first()
            msg1 = msg + '<p>Одобрить и посмотреть подробности можно по ссылке <a href="' + parameters.get(
                "webserver") + '/approve/' + str(prid) + '/' + \
                   str(curtask.id) + '''">Payment reques approval</a></p><p><b>В тестовом режиме работает одобрение 
                через ответный имейл. Не отвечайте на это письмо, если хотите отклонить, отправить на доработку 
                заявку или оставить комментарий!</b>'''
            mail.sendmail(mailparams, dept.approvermail, subj + ' нет оригиналов', msg1)

        if flagline == '00000':
            article.status = "Одобрено"
        else:
            article.status = "Ожидание утверждения"
        article.requested = flagline
        #        if article.requeststatus is None:
        #            article.requeststatus = "0" * 5
        #        elif len(article.requeststatus) < 5:
        #            article.requeststatus = "0"*5

        #if curtask.prid is not None:
        #    conn = db.engine.connect()
        #    sql = text(f"update task set scomment='{request.form['scomment']}' where prid={curtask.prid}")
        #    print(sql)
        #    conn.execute(sql)
        #    conn.commit()
        #    db.session.commit()
        return redirect(url_for('index'))

    return render_template("process.html", article=article, files=files, managermail=dept.approvermail)


@app.route('/toaccounting/<int:prid>', methods=['POST', 'GET'])
def toaccounting(prid):
    article = PaymentRequest.query.get(prid)
    #    files = department.query.filter(department.id == article.id)
    if article.trno == "" or article.trno is None:
        PaymentRequest.query.filter(PaymentRequest.id == prid).update({'status': 'Одобрено'})
    else:
        PaymentRequest.query.filter(PaymentRequest.id == prid).update({'status': 'Передано в оплату'})

    db.session.commit()

    if parameters.get('accountingmail') is not None and parameters.get('accountingmail') > '':
        subj = "PR " + str(prid) + " Одобрен. Готов к обработке"
        msg = "<p>Здравствуйте,<br>Запрос на утверждение платежа в пользу " + article.vendorname + " сумма " + str(
            article.amount) + " " + article.currency + "</p>"
        msg += f"<p>Отдел: {article.dept}, плательщик: {article.payer}, офис: {article.direction}</p>"
        msg += f"<p>Договор: {article.contract}, номер счета: {article.invoice}, дата счета: {article.invdate}</p>"
        msg += f"<p><b>был одобрен можно приступать к обработке</b></p>"
        msg += '<p>Посмотреть подробности можно по ссылке <a href="' + parameters.get("webserver") + '/posts/' + str(
            prid) + '">Payment request</a></p>'
        mail.sendmail(mailparams, parameters.get('accountingmail'), subj, msg)

    #    return redirect(url_for('index'))

    return redirect(f"/posts/{prid}")


@app.route('/accpost/<int:prid>', methods=['POST', 'GET'])
def accpost(prid):
    article = PaymentRequest.query.get(prid)
    #    files = department.query.filter(department.id == article.id)
    files = attachment.query.filter(attachment.prid == prid)
    tasks = task.query.filter(task.prid == prid)
    dept = department.query.filter(department.name == article.dept).first()
    requestor = User.query.filter(User.login == article.responsible).first()
    if request.method == 'POST':
        user = User.query.filter(User.login == article.responsible).first()
        respmail = user.email
        if request.form['action'] == "Сохранить и передать в оплату":
 #           PaymentRequest.query.filter(PaymentRequest.id == prid).update({'status': 'Одобрено'})
            if article.trno == "" and article.trno is None:
                article.status = "Одобрено"
            else:
                article.status = "Передано в оплату"

            article.trno = request.form.get('trno')
            article.trdate = request.form.get('trdate')
            article.plandate = request.form.get('plandate')
            article.accountant_ap = current_user.get_login()
            mail.sendmail(mailparams, respmail, f"PR {prid}. Бухгалтерия передала в оплату",
                          f'Здравствуйте,<br> бухгалтерия обработала и передала PR в оплату. Срок оплаты {article.plandate}.<br>Поставщик {article.vendorname}, счет {article.invoice} от {article.invdate}, сумма {article.amount}')
            db.session.commit()
            copyprfiles(prid)
        if request.form['action'] == "Отправить на доработку":
            article.status = "Доработка"
            article.acomment = request.form.get("acomment")
            mail.sendmail(mailparams, respmail, f"PR {prid}. Бухгалтерия вернула на доработку",
                          f'Здравствуйте,<br> PR вернули на доработку с коментарием {request.form["acomment"]}.')
            db.session.commit()

        return redirect(url_for('index'))
    return render_template("pr_accpost.html", article=article, files=files, managermail=dept.approvermail, tasks=tasks, requestor=requestor)


@app.route('/paymentpost/<int:prid>', methods=['POST', 'GET'])
def paymentpost(prid):
    article = PaymentRequest.query.get(prid)
    #    files = department.query.filter(department.id == article.id)
    files = attachment.query.filter(attachment.prid == prid)
    tasks = task.query.filter(task.prid == prid)
    dept = department.query.filter(department.name == article.dept).first()
    if request.method == 'POST':
        user = User.query.filter(User.login == article.responsible).first()
        respmail = user.email
        if request.form['action'] == "Оплачено":
            article.status = "Оплачено"
            article.pcomment = request.form.get("pcomment")
            article.paymentdate = request.form.get("pdate")
            db.session.commit()
            mail.sendmail(mailparams, respmail, f"PR {prid}. Оплачено",
                          f'Здравствуйте,<br> PR в пользу {article.vendorname} оплачено. Дата оплаты {request.form["pdate"]}. Комментарий {request.form["pcomment"]}.')
        if request.form['action'] == "Отправить на доработку бухгалтеру":
            article.status = "Одобрено"
            article.pcomment = request.form.get("pcomment")
            if parameters.get('accountingmail') is not None and parameters.get('accountingmail') > '':
                mail.sendmail(mailparams, parameters.get('accountingmail'), f"PR {prid}. Отклонено",
                          f'Здравствуйте,<br> Оплата PR  в пользу {article.vendorname} была отклонена, требуется доработка бухгалтера. Комментарий {request.form["pcomment"]}.')
            db.session.commit()
        if request.form['action'] == "Отправить на доработку инициатору":
            article.status = "Доработка"
            article.pcomment = request.form.get("pcomment")
            mail.sendmail(mailparams, respmail, f"PR {prid}. Бухгалтерия вернула из оплаты на доработку",
                          f'Здравствуйте,<br> PR  в пользу {article.vendorname} вернули из оплаты на доработку с комментарием {request.form["pcomment"]}.')
            db.session.commit()
        if request.form['action'] == "Отправить на взаимозачет":
            article.status = "Взаимозачет"
            article.pcomment = request.form.get("pcomment")
            if parameters.get('accountingmail') is not None and parameters.get('accountingmail') > '':
                mail.sendmail(mailparams, parameters.get('accountingmail'), f"PR {prid}. Взаимозачет",
                          f'Здравствуйте,<br> PR  в пользу {article.vendorname} отправили на взаимозачет. Комментарий {request.form["pcomment"]}.')
            db.session.commit()
        if request.form['action'] == "Отменить оплату":
            article.status = "Передано в оплату"
            article.pcomment = request.form.get("pcomment")
            db.session.commit()
        return redirect(url_for('payments'))

    return render_template("pr_payment.html", article=article, files=files, managermail=dept.approvermail, tasks=tasks,
                           pdate=datetime.date.today())


@app.route('/attachments/<int:prid>', methods=['POST', 'GET'])
def post_attach(prid):
    article = PaymentRequest.query.get(prid)
    files = attachment.query.filter(attachment.prid == prid)
    if request.method == 'POST':
        files = request.files.getlist("files")
        if not (os.path.isdir(os.path.join('archive', str(prid)))):
            os.mkdir(os.path.join('archive', str(prid)))

        for file in files:
            res = attachment.query.filter(attachment.filename == file.filename, attachment.path == str(prid)).first()
            if res is not None:
                db.session.delete(res)
                db.session.commit()

            att = attachment(prid=prid, filename=file.filename.replace(',', '_'), login=current_user.get_login(), path=str(prid))

            db.session.add(att)
            db.session.commit()

            file.save(os.path.join('archive', str(prid), file.filename.replace(',','_')))
            files = attachment.query.filter(attachment.prid == prid)

    return render_template("edit-attachements.html", article=article, files=files)


@app.route('/posts/<int:prid>/del')
def post_delete(prid):
    global errormsg
    article = PaymentRequest.query.get_or_404(prid)
    try:
        db.session.delete(article)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        errormsg = str(e)
        logging.error("del post " + str(e))
        return "При удалении произошла ошибка"


@app.route('/posts/<int:prid>/update', methods=['POST', 'GET'])
def pr_update(prid):
    global errormsg
    pr = PaymentRequest.query.get(prid)

    sql = text(f"select name from department with(nolock) order by name")
    conn = db.engine.connect()
    depts = conn.execute(sql).all()
    dept_list = [i.name for i in depts]

    form = PRForm()
    form.dept.choices = dept_list
    if form.validate_on_submit():
        if request.form['action'] == "Найти":
            svendor = Vendor.query.filter(Vendor.INN == form.inn.data).limit(1).first()
            if svendor is not None:
                form.vendorname.data = svendor.ShortName
            else:
                form.vendorname.data = ""
                flash("Клиент с этим ИНН не найден. Можно сохранить, уйдет письмо ответстенному за добавление.",
                      "error")
            return render_template("pr_update.html", form=form)
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
        except Exception as e:
            errormsg = str(e)
            logging.error("edit " + str(e))
            return "При редактировании произошла ошибка"
        #        for file in form.files.data:
        #            att = attachment(prid=prid, filename=secure_filename(file.filename))
        #            db.session.add(att)
        #           db.session.commit()
        #           file.save(os.path.join('archive', secure_filename(file.filename)))

        return redirect(url_for('index'))
    else:
        form.direction.data = pr.direction
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
        # form.vendorname.data = pr.vendorname
        files = attachment.query.filter(attachment.prid == prid)

        return render_template("pr_update.html", form=form, files=files)


@app.route('/download/<int:prid>/<path:filename>', methods=['GET', 'POST'])
def download(prid, filename):
    uploads = os.path.join("archive", str(prid))  # app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads, filename)


@app.route('/delattach/<int:attid>/<int:prid>', methods=['GET', 'POST'])
def delattach(attid, prid):
    global errormsg
    file = attachment.query.get_or_404(attid)

    try:
        db.session.delete(file)
        db.session.commit()
    except Exception as e:
        errormsg = str(e)
        logging.error("dell attach " + str(e))
        flash("ошибка удаления", "error")

    return redirect('/attachments/' + str(prid))


def getvendorbyinn(inn):
    return Vendor.query.filter(Vendor.INN == inn).limit(1).first()


@app.route('/create-pr', methods=['POST', 'GET'])
@app.route('/create_pr', methods=['POST', 'GET'])
@login_required
def pr_create():
    global errormsg
    sql = text(f"select name from department with(nolock) order by name")
    conn = db.engine.connect()
    depts = conn.execute(sql).all()
    dept_list = [i.name for i in depts]

    form = PRForm()
    form.dept.choices = dept_list
    if form.validate_on_submit():
        if request.form['action'] == "Найти":
            svendor = Vendor.query.filter(Vendor.INN == form.inn.data).limit(1).first()
            if svendor is not None:
                form.vendorname.data = svendor.ShortName
            else:
                form.vendorname.data = ""
                flash("Клиент с этим ИНН не найден. Можно сохранить, уйдет письмо ответстенному за добавление.",
                      "error")
            return render_template("create-pr.html", form=form)
        invdate = datetime.datetime.combine(form.invdate.data, datetime.datetime.min.time())
        vendorname = ""  # form.vendorname.data
        if vendorname == "":
            svendor = getvendorbyinn(form.inn.data)  # Vendor.query.filter(Vendor.INN == inn).limit(1).first()
            print('pr_create', svendor, type(svendor))
            if svendor is not None:
                vendorname = svendor.ShortName
            else:
                user = User.query.filter(User.login == form.responsible.data).first()
                respmail = user.email
                resplist = [respmail]
                # resplist.append(respmail)
                if parameters.get('supportmail') is not None:
                    resplist.append(parameters.get('supportmail'))
                else:
                    resplist.append('v000529@stokov.ru')

                mail.sendmail(mailparams, resplist, "PR нет данных поставщика",
                              f'Здравствуйте,<br> для инн {form.inn.data} нет данных.')
        if form.preapproved is not None:
            preapproved = form.preapproved.data
        else:
            preapproved = ''

        pr = PaymentRequest(direction=form.direction.data, payer=form.payer.data, responsible=form.responsible.data,
                            paymenttype=form.paymenttype.data, porderno=form.porderno.data, invoice=form.invoice.data,
                            invdate=invdate,
                            amount=form.amount.data, currency=form.currency.data, dept=form.dept.data,
                            contract=form.contract.data,
                            inn=form.inn.data, preapproved=preapproved, vendorname=vendorname, status='Черновик')

        #        try:
        db.session.commit()
        db.session.add(pr)
        db.session.commit()
        # for file in form.files:
        #    print(file.filename)
        #    file.save(file.filename)

        conn = db.engine.connect()
        sql = text("""update PaymentRequest.dbo.PaymentRequest set legalcode = b.code 
            from PaymentRequest.dbo.PaymentRequest a join PaymentRequest.dbo.legalcompanies b on a.payer = b.legalname
            where isnull(legalcode, '') = ''""")
        conn.execute(sql)
        conn.commit()

        return redirect(url_for('index'))  # redirect('/posts ')
    #       except:
    #           flash("При добавлении произошла ошибка", "error")
    #           return "При добавлении произошла ошибка"

    else:
        try:
            form.responsible.data = current_user.get_login()
        except Exception as e:
            errormsg = str(e)
            return redirect("bderror")
        # копировать
        if request.args.get('cpy') is not None and request.args.get('cpy') != "":
            try:
                pr = PaymentRequest.query.filter(PaymentRequest.id == request.args.get('cpy')).first()
            except Exception as e:
                errormsg = str(e)
                return redirect("bderror")
            print(pr,request.args.get('cpy'))
            if pr is not None:
                print(pr.direction)
                form.direction.data = pr.direction
                form.payer.data = pr.payer
                form.paymenttype.data = pr.paymenttype
                form.porderno.data = pr.porderno
                form.invoice.data = pr.invoice
                form.invdate.data = pr.invdate
                form.amount.data = pr.amount
                form.currency.data = pr.currency
                form.dept.data = pr.dept
                form.preapproved.data = pr.preapproved
                form.contract.data = pr.contract
                form.inn.data = pr.inn
                form.vendorname.data = pr.vendorname
        else:
            direction = selectfield("users", "direction", "login", form.responsible.data)
            if direction is not None:
                form.direction.data = direction

    return render_template("create-pr.html", form=form)


def selectfield(table, field, idname, idvalue):
    global errormsg
    conn = db.engine.connect()
    sql = text(f"select {field} from {table} where upper(cast({idname} as varchar(50))) = upper('{idvalue}')")
    try:
        res = conn.execute(sql).first()
    except Exception as e:
        errormsg = str(e)
        logging.error("selectfield " + str(e))
        return None
    return res[0]


@app.route('/test', methods=['POST', 'GET'])
def test():
    global errormsg
    sql = text("insert into dbo.users (name, email, pwd) values('test','','')")

    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(sql)
        trans.commit()
        return "добавили"
    except Exception as e:
        errormsg = str(e)
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
            except FileNotFoundError:
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
