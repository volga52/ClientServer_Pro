"""Программа-клиент
Запускается с параметрами-аргументами в виде
client.py -a 192.168.1.2 -p 8079
"""

import sys
import json
import socket
import time
import logging
import threading

from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER, \
    DESTINATION, EXIT
from common.utils import get_message, send_message
from config_network import SettingPortAddress as SPA
import logs.configs.config_client_log
import logs.configs.config_messages_log
from decos import Log, log_decor
from errors import ServerError, ReqFieldMissingError, IncorrectDataRecivedError


class Client:
    LOGGER = logging.getLogger('client')
    LOG_MESSAGES = logging.getLogger('messages')

    # def __init__(self, start_param):
    #     self.sys_params = start_param

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
        # self.LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        self.LOG_MESSAGES.debug(f'Сформирован словарь сообщения: {message_dict}.')
        try:
            send_message(sock, message_dict)
            self.LOGGER.info(f'Отправлено сообщение для пользователя {recipient}.')
        except:
            self.LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)
        # return message_dict

    @log_decor
    def message_from_server(self, sock, my_username):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            try:
                message = get_message(sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and MESSAGE_TEXT in message and message[DESTINATION] == my_username:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    self.LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                     f'\n{message[MESSAGE_TEXT]}')
                else:
                    self.LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                self.LOGGER.error('Не удалось декодировать полученное сообщение')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                self.LOGGER.error('Потеряно соединение с сервером')
                break

    @staticmethod
    def print_help():
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print(f'{MESSAGE} - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print(f'{EXIT} - выход из программы')

    """ Разделение """
    @log_decor
    def create_exit_message(self, account_name):
        """Функция создаёт словарь с сообщением о выходе"""
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: account_name
        }

    @log_decor
    def user_interactive(self, sock, username):
        """Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения"""
        self.print_help()
        while True:
            command = input('Введите команду: ')
            # if command == 'message':
            if command == MESSAGE:
                self.create_message(sock, username)
            elif command == 'help':
                self.print_help()
            # elif command == 'exit':
            elif command == EXIT:
                send_message(sock, self.create_exit_message(username))
                print('Завершение соединения.')
                self.LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробуйте еще. help - поддерживаемые команды.')

    @Log()
    def create_presence(self, account_name):
        """Функция генерирует запрос о присутствии клиента"""
        # {'action': 'presence', 'time': 1573760672.167031, 'user': {'account_name': 'Guest'}}
        ret_out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }

        self.LOG_MESSAGES.debug(f"Сформировано '{PRESENCE}' сообщение для пользователя '{account_name}'")
        return ret_out

    @log_decor
    def process_response_ans(self, message):
        """Функция разбирает ответ сервера на сообщение о присутствии,
            возращает 200 если все ОК или генерирует исключение при ошибке"""
        self.LOG_MESSAGES.debug(f'Приветственное сообщения от сервера: {message}, разбор.')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            elif message[RESPONSE] == 400:
                raise ServerError(f'400 : {message[ERROR]}')
        raise ReqFieldMissingError(RESPONSE)

    def connect(self):
        """Сообщаем о запуске"""
        print('Консольный месседжер. Клиентский модуль.')

        # param_network = SPA(create_arg_parser())              # 19.10.2021
        param_network = SPA(SPA.create_arg_parser())

        # server_address = param_network.get_address()
        server_address = param_network.address_return
        # server_port = param_network.get_port()
        server_port = param_network.port_return
        # client_name = param_network.get_client_name()
        client_name = param_network.client_name

        # Если имя пользователя не было задано, необходимо запросить пользователя.
        if not client_name:
            client_name = input('Введите имя пользователя: ')

        self.LOGGER.info(
            f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
            f'порт: {server_port}, имя пользователя: {client_name}')

        try:
            transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            transport.connect((server_address, server_port))
            send_message(transport, self.create_presence(client_name))

            answer = self.process_response_ans(get_message(transport))
            self.LOGGER.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
            print(f'Установлено соединение с сервером.')
        except json.JSONDecodeError:
            self.LOGGER.error('Не удалось декодировать полученную Json строку')
            sys.exit(1)
        except ServerError as error:
            self.LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            sys.exit(1)
        except ReqFieldMissingError as missing_error:
            self.LOGGER.error(f'В ответе сервера отсутствует необходимое поле {missing_error.missing_field}')
            sys.exit(1)
        except ConnectionRefusedError:
            self.LOGGER.critical(
                f'Не удалось подключиться к серверу {server_address}:{server_port}, '
                f'конечный компьютер отверг запрос на подключение.')
            sys.exit(1)
        else:
            # Если соединение с сервером установлено корректно,
            # запускаем клиенский процесс приёма сообщений

            capture = threading.Thread(target=self.message_from_server, args=(transport, client_name))
            capture.daemon = True
            capture.start()

            # затем запускаем отправку сообщений и взаимодействие с пользователем.
            user_communication = threading.Thread(target=self.user_interactive, args=(transport, client_name))
            user_communication.daemon = True
            user_communication.start()
            self.LOGGER.debug('Запущены процессы коммуникации')

            # Watchdog основной цикл, если один из потоков завершён,
            # то значит или потеряно соединение или пользователь
            # ввёл exit. Поскольку все события обработываются в потоках,
            # достаточно просто завершить цикл.
            while True:
                time.sleep(1)
                if capture.is_alive() and user_communication.is_alive():
                    continue
                break


if __name__ == "__main__":
    Client().connect()
