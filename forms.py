from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, DecimalField, PasswordField, SelectField, DateField, FileField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class PRForm(FlaskForm):
    responsible = StringField("Ответственный: ", validators=[DataRequired("Обязательное поле"), Length(min=7, max=7,
                                                                                                       message="Длинна логина 7. начинается с v")])
    direction = SelectField("Направление счета (Калуга / Химки): ", coerce=str, choices=['Калуга', 'Химки'])
    payer = SelectField("Компания плательщик: ", coerce=str, choices=['Стоков Машинное Оборудование АО',
                                                                      'Стоков Компоненты ООО',
                                                                      'Стоков Конструкция ООО'])
    paymenttype = SelectField("Вид оплаты: ", coerce=str, choices=['постоплата', 'предоплата'])
    porderno = StringField("Номер заказа на закупку: ")
    invoice = StringField("номер счета: ")
    invdate = DateField("Дата счета :")
    amount = DecimalField("Сумма счета с НДС: ")
    currency = SelectField("Валюта: ", coerce=str, choices=['РУБ', 'EUR'])
#    dept = SelectField("Отдел (центр затрат): ", coerce=str,
#                       choices=['GTO Logistic', 'GTO Prod & Maintn', 'GTO HR/Labor safety', 'GTO Quality', 'GTO VLS',
#                                'HR', 'IT', 'Legal', 'RE', 'SEC', 'TC', 'VFS'])
    dept = SelectField("Отдел (центр затрат): ", coerce=str)
    preapproved = BooleanField("Заранее одобрено: ", default=False)
    contract = StringField("Номер зарегистрированного контракта: ")
    inn = StringField("Поставщик ИНН: ",
                      validators=[DataRequired(), Length(min=10, max=12, message="Неверная длинна Инн")])
    searchbtn = SubmitField("Найти", name='action')
    vendorname = StringField("Наименование поставщика", render_kw={'style': 'width: 80ch', 'readonly': True})
    #    files = MultipleFileField("Вложения")
    submit = SubmitField(label="Сохранить", name='action')
    
class LoginForm(FlaskForm):
    login = StringField("Login: ", validators=[DataRequired(), Length(min=7, max=7, message="Длинна логина 7. начинается с v")])#[Email("Некорректный email")])
    psw = PasswordField("Пароль: ")
    remember = BooleanField("Запомнить", default = False)
    submit = SubmitField("Войти")

class RegisterForm(FlaskForm):
    name = StringField("Имя: ", validators=[Length(min=4, max=100, message="Имя должно быть от 4 до 100 символов")])
    email = StringField("Email: ", validators=[Email("Некорректный email")])
    psw = PasswordField("Пароль: ", validators=[DataRequired(),
                                                Length(min=4, max=100, message="Пароль должен быть от 4 до 100 символов")])

    psw2 = PasswordField("Повтор пароля: ", validators=[DataRequired(), EqualTo('psw', message="Пароли не совпадают")])
    submit = SubmitField("Регистрация")