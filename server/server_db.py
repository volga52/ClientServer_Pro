# Запуск с консолью невозможен
import os
import logging

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import *
import datetime
from logs.configs import config_client_log


logger = logging.getLogger('server')

# Серверная база данных
class ServerStorage:
    # Таблица всех пользователей
    class AllUsers:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

    # Таблица активных пользователей
    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    # Таблица истории посещений
    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    # Таблица контактов пользователей
    class UsersContact:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # История Общения клиента
    class HistoryCommunication:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        # Движок дазы данных

        # Рабочий вариант 'определение пути внутри'
        # path = os.path.dirname(os.path.abspath(__file__))     # Путь без файла
        # path = os.path.join(path, r'server_bd.db3')

        # self.database_engine = create_engine(f"sqlite:///{path}/{'server_base.db3'}", echo=False, pool_recycle=7200,
        #                                      connect_args={'check_same_thread': False})
        self.database_engine = create_engine(f"sqlite:///{path}", echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

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
                            Column('last_login', DateTime)
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
        mapper(self.AllUsers, users_table)  # Связывание класса в ORM с таблицей
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.UsersContact, contacts_table)
        mapper(self.HistoryCommunication, users_history_com)

        # Создание сессии
        SESSION = sessionmaker(bind=self.database_engine)
        self.session = SESSION()

        self.session.query(self.ActiveUsers).delete()  # На старте очищаем таблицу активных пользователей
        self.session.commit()

    # Функция записывает в базу факт входа пользователя
    def user_login(self, username, ip_address, port):
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        res_query = self.session.query(self.AllUsers).filter_by(name=username)

        if res_query.count():  # Если имя пользователя уже присутствует в таблице,
            user = res_query.first()  # Получаем пользователя
            user.last_login = datetime.datetime.now()  # обновляем время последнего входа

        else:  # Если нет, то создаздаём нового пользователя
            user = self.AllUsers(username)  # Подготовка данных к отпрваке в таблицу: создаём экземпляра класса
            self.session.add(user)  # Отправляем подготовленный элемент Сессия добавляет его в таблицу
            self.session.commit()  # Подтверждаем                  После комита присваивается ID
            # Создаем первую запись в таблице HistoryCommunication
            user_in_history = self.HistoryCommunication(user.id)
            self.session.add(user_in_history)

        # Запись в таблицу активных пользователей
        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        # Запись в таблицу истории входов
        fact = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(fact)

        # Сохраняем изменения
        self.session.commit()

    # Функция фиксирующая отключение пользователя
    def user_logout(self, username):
        # Запрос пользователя, что покидает нас, получаем запись из таблицы AllUsers
        user = self.session.query(self.AllUsers).filter_by(name=username).first()

        # Удаление записи из таблицы ActiveUsers
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        # Применяем изменения
        self.session.commit()

    # Функция возвращает список известных пользователей и время последнего входа.
    def users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
        )
        return query.all()  # Возвращаем список кортежей

    # Функция возвращает список активных пользователей
    def active_users_list(self):
        # Запрос из таблиц пользователей (имя, адрес, порт, время) и объединение кортежей.
        query = self.session.query(  # --- Поменять имя после проверки рс ---
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()  # Возвращает список кортежей

    # Функция возвращает историю входов по пользователю или всем пользователям
    def login_history(self, username=None):
        # Запрос истории входов
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()              # Возвращает список кортежей

    # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
    def process_message(self, sender, recipient):
        # Получаем id отправителя и получателя
        sender = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(name=recipient).first().id

        # Меняем значения счетчиков
        data_sender = self.session.query(self.HistoryCommunication).filter_by(user=sender).first()
        data_sender.sent += 1
        data_recipient = self.session.query(self.HistoryCommunication).filter_by(user=recipient).first()
        data_recipient.accepted += 1

        self.session.commit()

    # Функция добавляет контакт в таблицу. Если известен контактер и не было такого контакта
    def add_contact(self, user, contact):
        # Информация о пользователях
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        # Проверка условия
        if not contact or self.session.query(self.UsersContact).filter_by(user=user.id, contact=contact.id).count():
            return

        # Неучтенный контакт - Добавляем запись в таблицу
        users_contact = self.UsersContact(user.id, contact.id)
        self.session.add(users_contact)
        self.session.commit()

    # Функция удаляет контакт
    def remove_contact(self, user, client):
        # Информация о пользователях
        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        client = self.session.query(self.AllUsers).filter_by(name=client).first()

        if not client:              # Если контакта нет выход
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
        # Пользователь
        # logger.info(f"Запущена функция get_contact аргумент {user}")
        user = self.session.query(self.AllUsers).filter_by(name=user).one()
        # logger.info(f"get_contact user={user}")

        # Список контактов
        selection = self.session.query(self.UsersContact, self.AllUsers.name). \
            filter_by(user=user.id). \
            join(self.AllUsers,
                 self.UsersContact.contact == self.AllUsers.id
                 )
        # logger.info(f"get_contact selection {selection}")
        # Список 'знакомых' только имена
        list_contacts = [friend[1] for friend in selection.all()]
        # logger.info(f"get_contact list {list_contacts}")

        return list_contacts

    # Функция возвращает количество сообщений
    def get_quantity_message(self):
        selection = self.session.query(
            self.AllUsers.name,
            self.AllUsers.last_login,
            self.HistoryCommunication.sent,
            self.HistoryCommunication.accepted
        ).join(self.AllUsers)
        # Возвращается список кортежй
        return selection.all()


# Отладка                                                   # Запуск с консолью невозможен
if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))  # Путь без файла
    path = os.path.join(path, r'../server_base.db3')

    test_db = ServerStorage(path)

    test_db.user_login('client_1', '192.168.1.4', 8888)  # выполняем 'подключение' пользователя
    test_db.user_login('client_2', '192.168.1.5', 7777)
    print(test_db.users_list())
    print(test_db.active_users_list())  # выводим список кортежей - активных пользователей

    # test_db.user_logout('McG')
    print(test_db.login_history('re'))
    test_db.add_contact('client_2', 'client_1')
    test_db.add_contact('client_1', 'client_3')
    test_db.add_contact('client_1', 'client_6')
    test_db.remove_contact('client_1', 'client_3')

    test_db.user_logout('client_1')     # выполянем 'отключение' пользователя
    print(test_db.active_users_list())  # выводим список активных пользователей

    test_db.login_history('client_1')   # запрашиваем историю входов по пользователю
    print(test_db.users_list())         # выводим список известных пользователей
