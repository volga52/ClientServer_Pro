import sys
import logging

from PyQt5.QtWidgets import QApplication

import logs.configs.config_client_log
import logs.configs.config_messages_log
from client.transport import ClientTransport
from common.variables import *
from config_network import SettingPortAddress as Spa
from common.utils import get_message, send_message
from common.errors import ServerError
from common.decos import log_decor
from client.database import ClientDatabase
from client.set_client_dialog import UserNameDialog


logs_client = logging.getLogger('client')
logs_message = logging.getLogger('messages')


def main():
    param_connect = Spa(Spa.create_arg_parser())
    server_address = param_connect.address_return
    server_port = param_connect.port_return
    client_name = param_connect.client_name

    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке то запросим его
    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    logs_client.info(
        f'\nЗапущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    # Соответствует client.py_old линия 393

    # Создание базы данных
    database = False

    # Создание транспортного потока между сервером и клиентом.
    # Запуск потока
    try:
        transport = ClientTransport(server_address, server_port, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    # После закрытия графичесой оболочки закрывается все остальное
    transport.transport_shutdown()
    transport.join()


# if __name__ == '__main__':
#     main()
