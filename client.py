"""Программа-клиент
Запускается с параметрами-аргументами в виде
client.py -a 192.168.1.2 -p 8079 [-n Name]
[-n Name] - необязательный параметр
"""

import sys
import json
import socket
import time
import logging
import threading

from common.variables import *
from common.utils import get_message, send_message
from config_network import SettingPortAddress as SPA
import logs.configs.config_client_log
import logs.configs.config_messages_log
from common.decos import log_decor
from errors import ServerError, ReqFieldMissingError, IncorrectDataRecivedError
from metaclasses import ClientMaker
from client.client_db import ClientDatabase

logs_client = logging.getLogger('client')
logs_message = logging.getLogger('messages')

# Объект блокировки сокета и работы с базой данных
sock_lock = threading.Lock()
database_lock = threading.Lock()


# Класс получающий и обрабатывающий сообщения
class ClientReception(threading.Thread, metaclass=ClientMaker):

    def __init__(self, sock, username, database):
        self.socket = sock
        self.username = username
        self.database = database
        super().__init__()

    # Функция - обработчик сообщений поступающих с сервера
    def run(self):
        # Основной цикл приёмника сообщений, принимает сообщения, выводит в консоль. Завершается при потере соединения.
        while True:
            # Будем захватывать поток. Делаем перерыв, освобождая сокет для других потоков
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.socket)
                    print('****')

                except IncorrectDataRecivedError:
                    logs_client.error('Не удалось декодировать полученное сообщение')
                # Вышел таймаут соединения если errno = None, иначе обрыв соединения.
                except OSError as error:
                    if error.errno:
                        logs_client.critical('Потеряно соединение с сервером')
                        break
                # Нет соединения
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    logs_client.error('Потеряно соединение с сервером')
                    break
                # Если пакет корретно получен выводим в консоль и записываем в базу.
                else:
                    if ACTION in message \
                            and message[ACTION] == MESSAGE \
                            and SENDER in message \
                            and DESTINATION in message\
                            and MESSAGE_TEXT in message \
                            and message[DESTINATION] == self.username:
                        print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                              f'\n{message[MESSAGE_TEXT]}')

                        # Захватываем работу с базой данных и сохраняем в неё сообщение
                        with database_lock:
                            try:
                                self.database.save_message(message[SENDER], self.username, message[MESSAGE_TEXT])
                            except:
                                logs_client.error('Ошибка взаимодействия с базой данных')

                        logs_client.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                         f' {message[MESSAGE_TEXT].split()[0]}...')
                        logs_message.info(f'от пользователя {message[SENDER]}:'
                                          f'{message[MESSAGE_TEXT]}')

                    else:
                        logs_client.error(f'Получено некорректное сообщение с сервера: {message}')


# Класс взаимодействия с пользователем и отправки сообщений
class ClientManage(threading.Thread):
    # logs_client = logging.getLogger('client')
    # logs_message = logging.getLogger('messages')

    def __init__(self, sock, username, database):
        self.sock = sock
        self.username = username
        self.database = database
        super().__init__()

    @staticmethod
    def print_help():
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print(f'{MESSAGE} - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print(f'{HISTORY} - получить историю сообщений')
        print(f'{CONTACTS} - получить список контактов')
        print(f'edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print(f'{EXIT} - выход из программы')

    # Функция изменеия контактов
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logs_client.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact_server(self.sock, self.username, edit)
                    except ServerError:
                        logs_client.error('Не удалось отправить информацию на сервер.')

    @log_decor
    def create_message(self):
        """Функция запрашивает текст сообщения и возвращает его.
        Так же завершает работу при вводе подобной комманды
        """
        recipient = input('Введите имя получателя: ')
        # Проверим, что получаетль существует
        with database_lock:
            if not self.database.check_user(recipient):
                logs_client.error(f'Получатель {recipient} не зарегистрирован.')
                print('Получатель не зарегистрирован.')
                return

        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: recipient,
            TIME: time.time(),
            MESSAGE_TEXT: message,
        }
        logs_message.debug(f'Сформирован словарь сообщения: {message_dict}.')

        # Сохранение сообщения
        with database_lock:
            self.database.save_message(self.username, recipient, message)
            logs_client.debug('Запись в таблицу сообщений осуществлена')

        # Ожидаем освобождения сокета для отправки сообщения
        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                logs_client.info(f'Отправлено сообщение для пользователя {recipient}.')
            except OSError as err:
                if err.errno:
                    logs_client.critical('Потеряно соединение с сервером.')
                    exit(1)
                else:
                    logs_client.error('Не удалось передать сообщение. Таймаут соединения')

    @log_decor
    def create_exit_message(self):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }

    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_whom=self.username)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_whom=self.username)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(
                        f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}'
                        f'\n{message[2]}')

    @log_decor
    def run(self):
        self.print_help()
        while True:
            print(f'* Пользователь {self.username} *')
            command = input(f"Введите команду: ")

            # Сообщение
            if command == MESSAGE:
                self.create_message()

            # Вывод команд
            elif command == 'help':
                self.print_help()

            # Получение списока контактов из DB-client
            elif command == CONTACTS:
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            # история сообщений.
            elif command == HISTORY:
                self.print_history()

            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()

            elif command == EXIT:
                with sock_lock:
                    try:
                        send_message(self.sock, self.create_exit_message())
                    except:
                        pass
                    else:
                        print('Завершение соединения.')
                        logs_client.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break

            else:
                print('Команда не распознана, попробуйте еще. help - поддерживаемые команды.')


# Функция генерирует сообщение о присутствии клиента
@log_decor
def create_presence(account_name):
    ret_out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }

    logs_message.debug(f"Сформировано '{PRESENCE}' сообщение для пользователя '{account_name}'")
    return ret_out


# Функция разбирает ответ сервера на сообщение о присутствии,
# возращает 200 если все ОК или генерирует исключение при ошибке
@log_decor
def process_response_ans(message):
    logs_message.debug(f'Сервер подключился, отправил сообщение: {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


# Функция запрашивает список контактов и возвращает его, если все хорошо
def get_contacts_list(sock, name):
    logs_client.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        ACTION: GET_CONTACTS,
        TIME: time.time(),
        ACCOUNT_NAME: name
    }
    logs_client.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    logs_client.debug(f'Получен ответ {ans}')
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[DATA]
    else:
        raise ServerError


# Функция добавления пользователя в контакт лист
def add_contact_server(sock, username, contact):
    logs_client.debug(f'Создание контакта {contact}')
    req = {
        ACTION: ADD_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Сервер отметил контакт')


# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    logs_client.debug(f'Запрос списка известных пользователей {username}')
    req = {
        ACTION: USERS_REQUEST,
        TIME: time.time(),
        ACCOUNT_NAME: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 202:
        return ans[DATA]
    else:
        raise ServerError


# Функция удаления пользователя из контакт листа
def remove_contact(sock, username, contact):
    logs_client.debug(f'Удаление контакта {contact}')
    req = {
        ACTION: REMOVE_CONTACT,
        TIME: time.time(),
        USER: username,
        ACCOUNT_NAME: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if RESPONSE in ans and ans[RESPONSE] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


# Функция инициализатор базы данных. Запускается при запуске,
# загружает данные в базу с сервера.
def database_load(sock, database, username):
    # Список пользователей
    try:
        users_list = user_list_request(sock, username)
        # logs_client.debug(f"Список всех пользователей получен {users_list} ")
        logs_client.debug(f"Список всех пользователей получен.")
    except ServerError:
        logs_client.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    # Список контактов
    try:
        contacts_list = get_contacts_list(sock, username)
    except ServerError:
        logs_client.error('Ошибка запроса списка контактов.')
    else:
        logs_client.debug(f"Список контактов полчен {contacts_list}")
        for contact in contacts_list:
            database.add_contact(contact)


# Функция устанавливает соединение с сервером.
# Возвращает рабочий сокет и имя клиента (аккаунт)
@log_decor
def create_connect_client():
    # Установка параметров соединения
    param_connect = SPA(SPA.create_arg_parser())
    server_address = param_connect.address_return
    server_port = param_connect.port_return
    client_name = param_connect.client_name

    if not client_name:
        client_name = input('Введите имя пользователя: ')

    logs_client.info(
        f'\nЗапущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут 1 секунда, необходим для освобождения сокета.
        transport.settimeout(1)

        transport.connect((server_address, server_port))
        send_message(transport, create_presence(client_name))

        answer = process_response_ans(get_message(transport))
        logs_client.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')

    except json.JSONDecodeError:
        logs_client.error('Не удалось декодировать полученную Json строку')
        sys.exit(1)
    except ServerError as error:
        logs_client.error(f'При установке соединения сервер вернул ошибку: {error.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        logs_client.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
        sys.exit(1)
    except ConnectionRefusedError:
        logs_client.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
        # Если соединение с сервером установлено корректно,
        # Можно запустить клиенский процесс приёма сообщений
        # Возвращаем рабочий сокет и имя клиента (аккаунт)

        return transport, client_name


def main():
    socket_work, account_name = create_connect_client()

    # Инициализация БД
    database = ClientDatabase(account_name)
    database_load(socket_work, database, account_name)

    # Запускаем поток взаимодействия с пользователем
    module_manage = ClientManage(socket_work, account_name, database)
    module_manage.daemon = True
    module_manage.start()
    logs_client.debug('Клиентские процессы запущены')

    # Запускаем поток принимающий сообщения
    module_receiver = ClientReception(socket_work, account_name, database)
    module_receiver.daemon = True
    module_receiver.start()

    # Watchdog основной цикл, если один из потоков завершён,
    # то значит или потеряно соединение или пользователь
    # ввёл exit. Поскольку все события обработываются в потоках,
    # достаточно просто завершить цикл.
    while True:
        time.sleep(1)
        if module_receiver.is_alive() and module_manage.is_alive():
            continue
        break


if __name__ == "__main__":
    main()
