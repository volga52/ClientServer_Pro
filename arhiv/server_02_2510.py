import select
import socket
import sys
import json
import logging
import time

from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, MESSAGE, MESSAGE_TEXT, SENDER, RESPONSE_200, RESPONSE_400, DESTINATION, EXIT
from common.utils import get_message, send_message

from config_network import SettingPortAddress as SPA
import logs.configs.cofig_server_log
import logs.configs.config_messages_log
from decos import log_decor
from metaclasses import ServerMaker
# from server_db import ServerStorage   # Запуск с консолью невозможен


class Server(metaclass=ServerMaker):
    LOGGER = logging.getLogger('server')
    LOG_MESSAGES = logging.getLogger('messages')

    # @log_decor
    def process_client_message(self, message, messages_list, client, clients, names):
        """
        Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости.
        :param message:
        :param messages_list:
        :param client:
        :param clients:
        :param names:
        :return:
        """
        self.LOG_MESSAGES.debug(f"Разбор сообщения от клиента: '{message}'")
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если такой пользователь ещё не зарегистрирован,
            # регистрируем, иначе отправляем ответ и завершаем соединение.
            if message[USER][ACCOUNT_NAME] not in names.keys():
                names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Это имя уже используется.'
                send_message(client, response)
                clients.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений. Ответ не требуется.
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            messages_list.append(message)
            return
        # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            clients.remove(names[message[ACCOUNT_NAME]])
            names[message[ACCOUNT_NAME]].close()
            del names[message[ACCOUNT_NAME]]
            return
        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    # @log_decor
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

    # Новая функция (14,10,2021) по организации socket для соединения
    def set_socket(self):
        param_network = SPA(SPA.create_arg_parser())        # 19.10.2021 16:23
        listen_address = param_network.address_return
        listen_port = param_network.port_return

        self.LOGGER.info(
            f'Запущен сервер, порт для подключений: {listen_port}, '
            f'адрес с которого принимаются подключения: {listen_address}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((listen_address, listen_port))
        transport.settimeout(0.5)

        # Слушаем порт
        transport.listen(MAX_CONNECTIONS)

        return transport

    def start(self):
        transport = self.set_socket()   # создание socket (14,10,2021)

        # список клиентов , очередь сообщений
        clients_list = []
        messages = []

        # Словарь, содержащий имена пользователей и соответствующие им сокеты.
        names = dict()

        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = transport.accept()
            except OSError:
                pass
            else:
                self.LOGGER.info(f'Установлено соедение с ПК {client_address}')
                clients_list.append(client)

            recv_data_list = []
            send_data_list = []
            err_list = []

            # Проверяем наличие ждущих клиентов
            try:
                if clients_list:
                    recv_data_list, send_data_list, err_list = select.select(clients_list, clients_list, [], 0)
            except OSError:
                pass

            # принимаем сообщения, если возникает ошибка, исключаем клиента
            if recv_data_list:
                for client_with_message in recv_data_list:
                    try:
                        self.process_client_message(get_message(client_with_message), messages,
                                                    client_with_message, clients_list, names)
                    except:
                        self.LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                          f'отключился от сервера.')
                        clients_list.remove(client_with_message)

            # Если есть сообщения, обрабатываем каждое.
            for mess in messages:
                try:
                    self.process_message(mess, names, send_data_list)
                except:
                    self.LOGGER.info(f"Связь с клиентом по имени '{mess[DESTINATION]}' была потеряна")
                    clients_list.remove(names[mess[DESTINATION]])
                    del names[mess[DESTINATION]]
            messages.clear()


def main():
    server = Server()
    server.start()


if __name__ == '__main__':
    main()
