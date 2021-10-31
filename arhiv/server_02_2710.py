import select
import socket
import sys
import json
import logging
import time
import threading

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, MESSAGE, MESSAGE_TEXT, SENDER, RESPONSE_200, RESPONSE_400, DESTINATION, EXIT
from common.utils import get_message, send_message
from common import var_server_manage as ser_commands

from config_network import SettingPortAddress as SPA
import logs.configs.cofig_server_log
import logs.configs.config_messages_log
from decos import log_decor
from metaclasses import ServerMaker
from server_db import ServerStorage


class Server(threading.Thread, metaclass=ServerMaker):
    LOGGER = logging.getLogger('server')
    LOG_MESSAGES = logging.getLogger('messages')

    def __init__(self, sys_params, database):
        self.database = database
        self.param_network = sys_params
        self.names = dict()  # Словарь, содержащий имена пользователей и соответствующие им сокеты.
        self.clients_list = []  # Список клиентов
        self.messages_list = []  # Список сообщений

        super().__init__()

    # @log_decor
    def process_client_message(self, message, client):
        """
        Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости.
        :param message:
        :param client:
        :return:
        """
        self.LOG_MESSAGES.debug(f"Разбор сообщения от клиента: '{message}'")
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если такой пользователь ещё не зарегистрирован,
            # регистрируем, иначе отправляем ответ и завершаем соединение.
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client  # client (socket) Системный элемент (ОС)
                client_ip, client_port = client.getpeername()  # Вызов функци socket.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Это имя уже используется.'
                send_message(client, response)
                self.clients_list.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages_list.append(message)
            return
        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            self.clients_list.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            return
        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    @log_decor
    def process_message(self, message, names, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
        список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
        :param message:
        :param names:
        :param listen_socks:
        :return:
        """
        if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
            send_message(names[message[DESTINATION]], message)
            self.LOGGER.info(f"Отправлено сообщение пользователю '{message[DESTINATION]}' "
                             f"от пользователя '{message[SENDER]}'")
        elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            self.LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    # Функция возвращает socket для соединения

    def set_socket_server(self):
        listen_address = self.param_network.address_return  # Получение ip-адреса и порта
        listen_port = self.param_network.port_return

        self.LOGGER.info(
            f'Запущен сервер, порт для подключений: {listen_port}, '
            f'адрес с которого принимаются подключения: {listen_address}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((listen_address, listen_port))
        transport.settimeout(0.5)

        # Слушаем порт
        # transport.listen(MAX_CONNECTIONS)
        transport.listen()

        return transport

    # def start(self):
    def run(self):
        transport = self.set_socket_server()  #

        # список клиентов , очередь сообщений
        # clients_list = []
        # messages = []

        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = transport.accept()
            except OSError:
                pass
            else:
                self.LOGGER.info(f'Установлено соедение с ПК {client_address}')
                self.clients_list.append(client)

            recv_data_list = []
            send_data_list = []
            err_list = []

            # Проверяем наличие ждущих клиентов
            try:
                if self.clients_list:
                    recv_data_list, send_data_list, err_list = select.select(self.clients_list, self.clients_list, [],
                                                                             0)
            except OSError:
                pass

            # принимаем сообщения, если возникает ошибка, исключаем клиента
            if recv_data_list:
                for client_with_message in recv_data_list:
                    try:
                        self.process_client_message(get_message(client_with_message),
                                                    client_with_message)
                    except OSError:
                        self.LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                         f'отключился от сервера.')
                        self.clients_list.remove(client_with_message)

                        # Удаляем клиента из self.names по значению его сокета client_with_message
                        client_out = {value: key for key, value in self.names.items()}.get(client_with_message)
                        # del self.names[client_out]

                        # Удаляем выпавшего клиента из базы активных
                        self.database.user_logout(client_out)

            # Если есть сообщения, обрабатываем каждое.
            for mess in self.messages_list:
                try:
                    self.process_message(mess, self.names, send_data_list)
                except OSError:
                    self.LOGGER.info(f"Связь с клиентом по имени '{mess[DESTINATION]}' была потеряна")
                    self.clients_list.remove(self.names[mess[DESTINATION]])
                    client_out = self.names[mess[DESTINATION]]
                    # del self.names[mess[DESTINATION]]
                    del self.names[client_out]

                    # Удаляем выпавшего клиента из базы активных
                    self.database.user_logout(client_out)
            self.messages_list.clear()


def print_help():
    print('Поддерживаемые комманды:')
    print(f'{ser_commands.USERS_ALL} - список известных пользователей')
    print(f'{ser_commands.USERS_Connect} - список подключенных пользователей')
    print(f'{ser_commands.HISTORY_LOGS} - история входов пользователя')
    print(f'{ser_commands.EXIT} - завершение работы сервера.')
    print(f'{ser_commands.HELP} - вывод справки по поддерживаемым командам')


def main():
    data_base = ServerStorage()

    server = Server(SPA(SPA.create_arg_parser()), data_base)
    server.daemon = True
    server.start()

    # Печатаем справку:
    print_help()

    while True:
        command = input('Введите комманду: ')
        if command == ser_commands.HELP:
            print_help()
        elif command == ser_commands.EXIT:
            break
        elif command == ser_commands.USERS_ALL:
            for user in sorted(data_base.users_list()):
                print(f'Пользователь {user[0]}, последний вход: {user[1]}')
        elif command == ser_commands.USERS_Connect:
            a = sorted(data_base.active_users_list())
            if a:
                # for user in sorted(data_base.active_users_list()):
                for user in a:
                    print(f'Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, '
                          f'время установки соединения: {user[3]}')
            else:
                print('Подключений нет')
        elif command == ser_commands.HISTORY_LOGS:
            name = input('Введите имя пользователя для просмотра истории. '
                         'Для вывода всей истории, просто нажмите Enter: ')
            for user in sorted(data_base.login_history(name)):
                print(f'Пользователь: {user[0]} время входа: {user[1]}. Вход с: {user[2]}:{user[3]}')
        else:
            print('Команда не распознана.')


if __name__ == '__main__':
    main()
