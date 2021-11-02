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

# from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
#     RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, \
#     DESTINATION, EXIT
from common.variables import *
from common.utils import get_message, send_message
from config_network import SettingPortAddress as SPA
import logs.configs.config_client_log
import logs.configs.config_messages_log
from decos import log_decor
from errors import ServerError, ReqFieldMissingError, IncorrectDataRecivedError
from metaclasses import ClientMaker

logs_client = logging.getLogger('client')
logs_message = logging.getLogger('messages')



# Класс получения и обработки сообщений
class ClientReception(threading.Thread, metaclass=ClientMaker):
    # logs_client = logging.getLogger('client')

    def __init__(self, sock, username):
        self.socket = sock
        self.username = username
        super().__init__()

    def run(self):
        """Функция - обработчик сообщений поступающих с сервера"""
        while True:
            try:
                message = get_message(self.socket)

            except IncorrectDataRecivedError:
                logs_client.error('Не удалось декодировать полученное сообщение')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logs_client.error('Потеряно соединение с сервером')
                break

            else:
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and MESSAGE_TEXT in message and message[DESTINATION] == self.username:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    logs_client.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                          f'\n{message[MESSAGE_TEXT]}')

                elif ACTION in message and message[ACTION] == GET_CONTACTS and message[DESTINATION] == self.username:
                    data = message[DATA]
                    print(data)
                    """****************************************************************************"""
                    pass
                else:
                    logs_client.error(f'Получено некорректное сообщение с сервера: {message}')


# Класс взаимодействия с пользователем и отправки сообщений
class ClientManage(threading.Thread):
    # logs_client = logging.getLogger('client')
    # logs_message = logging.getLogger('messages')

    def __init__(self, sock, username):
        self.sock = sock
        self.username = username
        super().__init__()

    @staticmethod
    def print_help():
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print(f'{MESSAGE} - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print(f'{HISTORY} - получить историю сообщений')
        print(f'{GET_CONTACTS} - получить список контактов')
        print(f'edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print(f'{EXIT} - выход из программы')

    # Функция изменеия контактов
    # def edit_contacts(self):
    #     ans = input('Для удаления введите del, для добавления add: ')
    #     if ans == 'del':
    #         edit = input('Введите имя удаляемного контакта: ')
    #         with database_lock:
    #             if self.database.check_contact(edit):
    #                 self.database.del_contact(edit)
    #             else:
    #                 logger.error('Попытка удаления несуществующего контакта.')
    #     elif ans == 'add':
    #         # Проверка на возможность такого контакта
    #         edit = input('Введите имя создаваемого контакта: ')
    #         if self.database.check_user(edit):
    #             with database_lock:
    #                 self.database.add_contact(edit)
    #             with sock_lock:
    #                 try:
    #                     add_contact(self.sock , self.account_name, edit)
    #                 except ServerError:
    #                     logger.error('Не удалось отправить информацию на сервер.')

    @log_decor
    def create_message(self, sock, account_name='Guest'):
        """Функция запрашивает текст сообщения и возвращает его.
        Так же завершает работу при вводе подобной комманды
        """
        recipient = input('Введите имя получателя: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: account_name,
            DESTINATION: recipient,
            TIME: time.time(),
            MESSAGE_TEXT: message,
        }
        logs_message.debug(f'Сформирован словарь сообщения: {message_dict}.')
        try:
            send_message(sock, message_dict)
            logs_client.info(f'Отправлено сообщение для пользователя {recipient}.')
        except:
            logs_client.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    @log_decor
    def create_exit_message(self, account_name):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: account_name
        }

    @log_decor
    def run(self):
        self.print_help()
        while True:
            print(f'Пользователь {self.username}')
            command = input(f"Введите команду: ")

            # Сообщение
            if command == MESSAGE:
                self.create_message(self.sock, self.username)

            # Вывод команд
            elif command == 'help':
                self.print_help()

            # Получение списка контактов
            elif command == GET_CONTACTS:
                answer = get_contacts_list(self.sock, self.username)
                print(answer)

            elif command == ADD_CONTACT:
                # Команда подлежит исправлению
                add_contact_server(self.sock, self.username, 'contact_temp')

            # Редактирование контактов
            elif command == 'edit':
                # ---------------------------------------------
                self.edit_contacts()


            elif command == EXIT:
                send_message(self.sock, self.create_exit_message(self.username))
                print('Завершение соединения.')
                logs_client.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробуйте еще. help - поддерживаемые команды.')


@log_decor
def create_presence(account_name):
    """Функция генерирует запрос о присутствии клиента"""
    # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
    ret_out = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }

    logs_message.debug(f"Сформировано '{PRESENCE}' сообщение для пользователя '{account_name}'")
    return ret_out


@log_decor
def process_response_ans(message):
    """Функция разбирает ответ сервера на сообщение о присутствии,
        возращает 200 если все ОК или генерирует исключение при ошибке"""
    logs_message.debug(f'Приветственное сообщения от сервера: {message}, разбор.')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log_decor
def create_connect_client():
    """Функция устанавливает соединение с сервером"""
    # Установка параметров соединения
    param_connect = SPA(SPA.create_arg_parser())
    server_address = param_connect.address_return
    server_port = param_connect.port_return
    client_name = param_connect.client_name

    if not client_name:
        client_name = input('Введите имя пользователя: ')

    logs_client.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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


def main():
    socket_work, account_name = create_connect_client()

    module_receiver = ClientReception(socket_work, account_name)
    module_receiver.daemon = True
    module_receiver.start()

    module_manage = ClientManage(socket_work, account_name)
    module_manage.daemon = True
    module_manage.start()
    logs_client.debug('Клиентские процессы запущены')

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
