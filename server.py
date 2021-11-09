import os
import select
import socket
import logging
import sys
import threading

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

sys.path.append('../')
from common.variables import *
from common.utils import get_message, send_message
from config_network import SettingPortAddress as SPA
from common.decos import log_decor
from metaclasses import ServerMaker
from server_db import ServerStorage
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model

logger = logging.getLogger('server')
log_messages = logging.getLogger('messages')

new_connection = False
conflag_lock = threading.Lock()


class Server(threading.Thread, metaclass=ServerMaker):

    def __init__(self, sys_params, database):
        self.database = database
        self.param_network = sys_params
        self.names = dict()  # Словарь, содержащий имена пользователей и соответствующие им сокеты.
        self.clients_list = []  # Список клиентов
        self.messages_list = []  # Список сообщений
        self.sock = None

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
        global new_connection
        log_messages.debug(f"Разбор сообщения от клиента: '{message}'")

        # Если сообщение о присутствии
        if ACTION in message \
                and message[ACTION] == PRESENCE\
                and TIME in message \
                and USER in message:
            # Если такой пользователь ещё не зарегистрирован,
            # регистрируем, иначе отправляем ответ и завершаем соединение.
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client        # client (socket) Системный элемент (ОС)
                client_ip, client_port = client.getpeername()           # Вызов функци socket.getpeername()
                self.database.user_login(message[USER][ACCOUNT_NAME], client_ip, client_port)
                send_message(client, RESPONSE_200)
                with conflag_lock:
                    new_connection =True
            else:
                response = RESPONSE_400
                response[ERROR] = 'Это имя уже используется.'
                send_message(client, response)
                self.clients_list.remove(client)
                client.close()
            return

        # Если это сообщение, то добавляем его в очередь сообщений. И отвечаем
        elif ACTION in message and message[ACTION] == MESSAGE\
                and DESTINATION in message \
                and TIME in message \
                and SENDER in message \
                and MESSAGE_TEXT in message\
                and self.names[message[SENDER]] == client:
            self.messages_list.append(message)
            self.database.process_message(message[SENDER], message[DESTINATION])
            send_message(client, RESPONSE_200)
            return

        # Сообщение содержит запрос на 'список котактов'
        elif ACTION in message \
                and message[ACTION] == GET_CONTACTS \
                and USER in message \
                and self.names[message[USER]] == client:
            response = RESPONSE_202

            # Присоединение к ответу Данных из БД
            response[DATA] = self.database.get_contact(message[USER])
            send_message(client, response)
            return

        # Сообщение добавить контакт
        elif ACTION in message \
                and message[ACTION] == ADD_CONTACT\
                and ACCOUNT_NAME in message \
                and USER in message and \
                self.names[message[USER]] == client:
            self.database.add_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)
            return

        # Если это запрос известных пользователей
        elif ACTION in message \
                and message[ACTION] == USERS_REQUEST \
                and ACCOUNT_NAME in message \
                and self.names[message[ACCOUNT_NAME]] == client:
            response = RESPONSE_202
            response[DATA] = [user[0] for user in self.database.users_list()]
            send_message(client, response)
            return

        # Если это удаление контакта
        elif ACTION in message \
                and message[ACTION] == REMOVE_CONTACT \
                and ACCOUNT_NAME in message \
                and USER in message \
                and self.names[message[USER]] == client:
            self.database.remove_contact(message[USER], message[ACCOUNT_NAME])
            send_message(client, RESPONSE_200)
            return

        # Если клиент выходит
        elif ACTION in message \
                and message[ACTION] == EXIT \
                and ACCOUNT_NAME in message:
            self.database.user_logout(message[ACCOUNT_NAME])
            logger.info(f"Клиент '{message[ACCOUNT_NAME]}' отключился.")
            self.clients_list.remove(self.names[message[ACCOUNT_NAME]])
            self.names[message[ACCOUNT_NAME]].close()
            del self.names[message[ACCOUNT_NAME]]
            with conflag_lock:
                new_connection = True
            return

        # Иначе отдаём Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return

    # Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
    # список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
    @log_decor
    def process_message(self, message, listen_socks):
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            logger.info(f"Отправлено сообщение пользователю '{message[DESTINATION]}' "
                        f"от пользователя '{message[SENDER]}.'")
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    # Функция возвращает socket для соединения
    def set_socket_server(self):
        listen_address = self.param_network.address_return  # Получение ip-адреса и порта
        listen_port = self.param_network.port_return

        # self.logger.info(
        logger.info(
            f'Запущен сервер, порт для подключений: {listen_port}, '
            f'адрес с которого принимаются подключения: {listen_address}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((listen_address, listen_port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen()

        # Слушаем порт
        # transport.listen(MAX_CONNECTIONS)
        # transport.listen()

    def run(self):
        global new_connection
        self.set_socket_server()  #

        # список клиентов , очередь сообщений
        # clients_list = []
        # messages = []

        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                # self.logger.warning(f'Установлено соедение с ПК {client_address}')
                logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients_list.append(client)

            recv_data_list = []
            send_data_list = []
            err_list = []

            # Проверяем наличие ждущих клиентов
            try:
                if self.clients_list:
                    recv_data_list, send_data_list, err_list = \
                        select.select(self.clients_list, self.clients_list, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err}')

            # принимаем сообщения, если возникает ошибка, исключаем клиента
            if recv_data_list:
                for client_with_message in recv_data_list:
                    try:
                        self.process_client_message(get_message(client_with_message),
                                                    client_with_message)
                    except OSError:
                        logger.error(f'Клиент {client_with_message.getpeername()} '
                                     f'отключился от сервера.')
                        self.clients_list.remove(client_with_message)

                        # Удаляем клиента из self.names по значению его сокета client_with_message
                        client_out = {value: key for key, value in self.names.items()}.get(client_with_message)
                        del self.names[client_out]

                        # Удаляем выпавшего клиента из базы активных
                        self.database.user_logout(client_out)
                        with conflag_lock:
                            new_connection = True

            # Если есть сообщения, обрабатываем каждое.
            for mess in self.messages_list:
                try:
                    self.process_message(mess, send_data_list)
                except OSError:
                    # self.logger.info(f"Связь с клиентом по имени '{mess[DESTINATION]}' была потеряна")
                    logger.info(f"Связь с клиентом по имени '{mess[DESTINATION]}' была потеряна")
                    self.clients_list.remove(self.names[mess[DESTINATION]])
                    client_out = self.names[mess[DESTINATION]]
                    # del self.names[mess[DESTINATION]]
                    del self.names[client_out]

                    # Удаляем выпавшего клиента из базы активных
                    self.database.user_logout(client_out)
                    with conflag_lock:
                        new_connection = True
            self.messages_list.clear()


def main():
    logger.info(f"Запущен server.py")

    path = os.path.dirname(os.path.abspath(__file__))  # Путь без файла
    path = os.path.join(path, r'server_base.db3')

    data_base = ServerStorage(path)

    server = Server(SPA(SPA.create_arg_parser()), data_base)
    server.daemon = True
    server.start()

    # Создаём графическое окуружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна           # таблица отображения
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(data_base))
    main_window.active_clients_table.setModel(gui_create_model(data_base))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Функция обновляющяя список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(data_base))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(data_base))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    # def server_config():
    #     global config_window
    #     # Создаём окно и заносим в него текущие параметры
    #     config_window = ConfigWindow()
    #     config_window.db_path.insert(config['SETTINGS']['Database_path'])
    #     config_window.db_file.insert(config['SETTINGS']['Database_file'])
    #     config_window.port.insert(config['SETTINGS']['Default_port'])
    #     config_window.ip.insert(config['SETTINGS']['Listen_Address'])
    #     config_window.save_btn.clicked.connect(save_server_config)

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    # main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()


if __name__ == '__main__':
    main()
