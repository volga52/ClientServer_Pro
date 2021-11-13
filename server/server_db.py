import os
import logging

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Text
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import *
import datetime
from logs.configs import cofig_server_log

logger = logging.getLogger('server')


# Серверная база данных
class ServerStorage:
    """
    Класс - оболочка для работы с базой данных сервера.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется классический подход.
    """
    # Таблица всех пользователей
    class AllUsers:
        '''Класс - отображение таблицы всех пользователей.'''

        def __init__(self, username, password_hash):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.password_hash = password_hash
            self.pubkey = None
            self.id = None

    # Таблица активных пользователей
    class ActiveUsers:
        '''Класс - отображение таблицы активных пользователей.'''

        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    # Таблица истории посещений
    class LoginHistory:
        '''Класс - отображение таблицы истории входов.'''

        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    # Таблица контактов пользователей
    class UsersContact:
        def __init__(self, user, contact):
            '''Класс - отображение таблицы контактов пользователей.'''
            self.id = None
            self.user = user
            self.contact = contact

    # История Общения клиента
    class HistoryCommunication:
        '''Класс - отображение таблицы истории действий.'''

        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        # Движок дазы данных

        # Рабочий вариант 'определение пути внутри'
        # _path = os._path.dirname(os._path.abspath(__file__))     # Путь без файла
        # _path = os._path.join(_path, r'server_bd.db3')

        # self.database_engine = create_engine(f"sqlite:///{_path}/{'server_base.db3'}", echo=False, pool_recycle=7200,
        # connect_args={'check_same_thread': False})
        self.database_engine = create_engine(
            f"sqlite:///{path}",
            echo=False,
            pool_recycle=7200,
            connect_args={'check_same_thread': False}
        )

        # SERVER_DB - sqlite:///server_db.db3
        # echo=False - отключаем ведение лога (вывод sql-запросов)
        # pool_recycle - По умолчанию соединение с БД через 8 часов простоя обрывается.
        # Чтобы это не случилось pool_recycle = 7200 (перезагрузка соединения через 2 часа)
        # connect_args={'check_same_thread': False} - Работа с несколькими потоками. По умолчанию True
        # self.database_engine = create_engine(SERVER_DB+'?check_same_thread=False', echo=False, pool_recycle=7200)

        # Объект MetaData
        self.metadata = MetaData()

        # Таблица пользователей
        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime),
                            Column('password_hash', String),
                            Column('pubkey', Text)
                            )

        # Таблица активных поьзователей
        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        # Таблица истории посещений
        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )
        # Таблица Контактов пользователей
        contacts_table = Table('UsersContact', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('user', ForeignKey('Users.id')),
                               Column('contact', ForeignKey('Users.id'))
                               )

        # Таблица истории общения клиента
        users_history_com = Table('HistoryCommunication', self.metadata,
                                  Column('id', Integer, primary_key=True),
                                  Column('user', ForeignKey('Users.id')),
                                  Column('sent', Integer),
                                  Column('accepted', Integer)
                                  )

        # Создание таблиц
        self.metadata.create_all(self.database_engine)

        # Создание отображения
        # Связывание класса в ORM с таблицей
        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UsersContact, contacts_table)
        mapper(self.HistoryCommunication, users_history_com)

        # Создание сессии
        SESSION = sessionmaker(bind=self.database_engine)
        self.session = SESSION()

        # На старте очищаем таблицу активных пользователей
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    # Функция записывает в базу факт входа пользователя
    def user_login(self, username, ip_address, port, key):
        '''
        Метод выполняется при входе пользователя, записывает в базу факт входа
        Обновляет открытый ключ пользователя при его изменении.
        '''

        # Запрос в таблицу пользователей на наличие
        # в ней пользователя с таким именем
        res_query = self.session.query(self.AllUsers).filter_by(name=username)

        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        # и проверяем корректность ключа. Если клиент прислал новый ключ,
        # сохраняем его.

        if res_query.count():                           # Прорверяем пользовватель присутствует в таблице,
            user = res_query.first()                    # Получаем пользователя
            user.last_login = datetime.datetime.now()   # обновляем время последнего входа
            if user.pubkey != key:
                user.pubkey = key
        # Если нет, генерируем исключение
        else:
            raise ValueError('Пользователь не зарегистрирован.')
        # else:  # Если нет, то создаздаём нового пользователя
        #     user = self.AllUsers(username)  # Подготовка данных к отпрваке в таблицу: создаём экземпляра класса
        #     self.session.add(user)  # Отправляем подготовленный элемент Сессия добавляет его в таблицу
        #     self.session.commit()  # Подтверждаем                  После комита присваивается ID
        #     # Создаем первую запись в таблице HistoryCommunication
        #     user_in_history = self.HistoryCommunication(user.id)
        #     self.session.add(user_in_history)

        # Запись в таблицу активных пользователей
        new_active_user = self.ActiveUsers(
            user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        # Запись в таблицу истории входов
        fact = self.LoginHistory(
            user.id,
            datetime.datetime.now(),
            ip_address,
            port)
        self.session.add(fact)

        # Сохраняем изменения
        self.session.commit()

    def add_user(self, name, password_hash):
        '''
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        '''
        user_row = self.AllUsers(name, password_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.HistoryCommunication(user_row.id)
        self.session.add(history_row)
        self.session.commit()

    def remove_user(self, name):
        '''Метод удаляет пользователя из базы.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(name=user.id).delete()
        self.session.query(self.UsersContact).filter_by(user=user.id).delete()
        self.session.query(
            self.UsersContact).filter_by(
            contact=user.id).delete()
        self.session.query(
            self.HistoryCommunication).filter_by(
            user=user.id).delete()
        self.session.query(self.AllUsers).filter_by(name=name).delete()
        self.session.commit()

    def get_hash(self, name):
        '''Метод создает хэша пароля пользователя.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        return user.password_hash

    def get_pubkey(self, name):
        '''Метод получает публичноый ключ пользователя.'''
        user = self.session.query(self.AllUsers).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        '''Метод проверяет существование пользователя.'''
        if self.session.query(self.AllUsers).filter_by(name=name).count():
            return True
        else:
            return False

    # Функция фиксирующая отключение пользователя
    def user_logout(self, username):
        '''Метод фиксирует отключение пользователя.'''
        # Запрос пользователя, что покидает нас, получаем запись из таблицы
        # AllUsers
        user = self.session.query(
            self.AllUsers).filter_by(
            name=username).first()

        # Удаление записи из таблицы ActiveUsers
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        # Применяем изменения
        self.session.commit()

    # Функция возвращает список известных пользователей и время последнего
    # входа.
    def users_list(self):
        '''Метод возвращает список известных пользователей.'''
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
        )
        return query.all()  # Возвращаем список кортежей

    # Функция возвращает список активных пользователей
    def active_users_list(self):
        '''Метод возвращает список активных пользователей.'''
        # Запрос из таблиц пользователей (имя, адрес, порт, время) и
        # объединение кортежей.
        query = self.session.query(  # --- Поменять имя после проверки рс ---
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()  # Возвращает список кортежей

    # Функция возвращает историю входов по пользователю или всем пользователям
    def login_history(self, username=None):
        '''Метод возврает историю входов.'''
        # Запрос истории входов
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()  # Возвращает список кортежей

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в
    # БД
    def process_message(self, sender, recipient):
        '''Метод записывает в таблицу статистики факт передачи сообщения.'''
        # Получаем id отправителя и получателя
        sender = self.session.query(
            self.AllUsers).filter_by(
            name=sender).first().id
        recipient = self.session.query(
            self.AllUsers).filter_by(
            name=recipient).first().id

        # Меняем значения счетчиков
        data_sender = self.session.query(
            self.HistoryCommunication).filter_by(
            user=sender).first()
        data_sender.sent += 1
        data_recipient = self.session.query(
            self.HistoryCommunication).filter_by(
            user=recipient).first()
        data_recipient.accepted += 1

        self.session.commit()

    # Функция добавляет контакт в таблицу. Если известен контактер и не было
    # такого контакта
    def add_contact(self, user, contact):
        '''Метод добавляет контакта для пользователя.'''
        # Информация о пользователях
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(
            self.AllUsers).filter_by(
            name=contact).first()

        # Проверка условия
        if not contact or self.session.query(self.UsersContact).filter_by(
                user=user.id, contact=contact.id).count():
            return

        # Неучтенный контакт - Добавляем запись в таблицу
        users_contact = self.UsersContact(user.id, contact.id)
        self.session.add(users_contact)
        self.session.commit()

    # Функция удаляет контакт
    def remove_contact(self, user, client):
        '''Метод удаляет контакт пользователя.'''
        # Информация о пользователях
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        client = self.session.query(
            self.AllUsers).filter_by(
            name=client).first()

        if not client:  # Если контакта нет выход
            return

        string_info = self.session.query(self.UsersContact).filter(
            self.UsersContact.user == user.id,
            self.UsersContact.contact == client.id
        ).delete()
        # Требуется Запись в 'журнал'
        print(string_info)

        self.session.commit()

    # Функция возвращает список контактов
    def get_contact(self, user):
        '''Метод возвращает список контактов пользователя.'''
        # Пользователь
        user = self.session.query(self.AllUsers).filter_by(name=user).one()

        # Список контактов
        selection = self.session.query(
            self.UsersContact, self.AllUsers.name).\
            filter_by(user=user.id). \
            join(self.AllUsers, self.UsersContact.contact == self.AllUsers.id
                 )
        # Список 'знакомых' только имена
        list_contacts = [friend[1] for friend in selection.all()]

        return list_contacts

    # Функция возвращает количество сообщений
    def get_quantity_message(self):
        '''Метод возвращает статистику сообщений.'''
        selection = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.HistoryCommunication.sent,
            self.HistoryCommunication.accepted
        ).join(self.AllUsers)
        # Возвращается список кортежй
        return selection.all()
