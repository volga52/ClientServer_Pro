# Запуск с консолью невозможен
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import *
import datetime


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

    def __init__(self):
        # Движок дазы данных
        # SERVER_DB - sqlite:///server_db.db3
        # echo=False - отключаем ведение лога (вывод sql-запросов)
        # pool_recycle - По умолчанию соединение с БД через 8 часов простоя обрывается.
        # Чтобы это не случилось pool_recycle = 7200 (перезагрузка соединения через 2 часа)
        self.database_engine = create_engine(SERVER_DB, echo=False, pool_recycle=7200)
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

        # Создание таблицы

        self.metadata.create_all(self.database_engine)

        # Создание отображения
        mapper(self.AllUsers, users_table)              # Связывание класса в ORM с таблицей
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)

        # Создание сессии
        SESSION = sessionmaker(bind=self.database_engine)
        self.session = SESSION()

        self.session.query(self.ActiveUsers).delete()   # На старте очищаем таблицу активных пользователей
        self.session.commit()

    # Функция записывает в базу факт входа пользователя
    def user_login(self, username, ip_address, port):
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        res_query = self.session.query(self.AllUsers).filter_by(name=username)

        # print(type(res_query)) -> # <class 'sqlalchemy.orm.query.Query'>
        # print(res_query)       -> # SELECT "Users".id AS "Users_id", "Users".name AS "Users_name", "Users".last_login
        #                                                   AS "Users_last_login" FROM "Users" WHERE "Users".name = ?

        if res_query.count():                   # Если имя пользователя уже присутствует в таблице,
            user = res_query.first()            # Получаем пользователя
            user.last_login = datetime.datetime.now()   # обновляем время последнего входа

        else:                       # Если нет, то создаздаём нового пользователя
            user = self.AllUsers(username)      # Подготовка данных к отпрваке в таблицу: создаём экземпляра класса
            self.session.add(user)              # Отправляем подготовленный элемент Сессия добавляет его в таблицу
            self.session.commit()               # Подтверждаем                  После комита присваивается ID

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
        return query.all()          # Возвращаем список кортежей

    # Функция возвращает список активных пользователей
    def active_users_list(self):
        # Запрос из таблиц пользователей (имя, адрес, порт, время) и объединение кортежей.
        query = self.session.query(                 # --- Поменять имя после проверки рс ---
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
            ).join(self.AllUsers)
        return query.all()          # Возвращаем список кортежей

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
        return query.all()


# Отладка
# Запуск с консолью невозможен
if __name__ == '__main__':
    test_db = ServerStorage()

    test_db.user_login('client_1', '192.168.1.4', 8888)     # выполняем 'подключение' пользователя
    test_db.user_login('client_2', '192.168.1.5', 7777)
    print(test_db.active_users_list())                      # выводим список кортежей - активных пользователей

    test_db.user_logout('client_1')                         # выполянем 'отключение' пользователя
    print(test_db.active_users_list())                      # выводим список активных пользователей

    test_db.login_history('client_1')                       # запрашиваем историю входов по пользователю
    print(test_db.users_list())                             # выводим список известных пользователей
