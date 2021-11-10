import sys
import logging

from PyQt5.QtWidgets import QApplication

sys.path.append('../')
from client.main_window import ClientMainWindow
from client.transport import ClientTransport
from common.variables import *
from config_startup import SettingsStartArguments as Ssa
from common.utils import get_message, send_message
from common.errors import ServerError
from common.decos import log_decor
from client.database import ClientDatabase
from client.set_client_dialog import UserNameDialog


# клиентские логеры
logs_client = logging.getLogger('client')
logs_message = logging.getLogger('messages')


def main():
    connection_params = Ssa()
    server_address = connection_params.address_return
    server_port = connection_params.port_return
    client_name = connection_params.client_name

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
    database = ClientDatabase(client_name)

    # Запуск транспортного потока между сервером и клиентом.
    try:
        transport = ClientTransport(server_address, server_port, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)  # Здесь происходит проброс сигналов из transport
    main_window.setWindowTitle(f'Чат Программа  - {client_name}')
    client_app.exec_()

    # После закрытия графичесой оболочки закрывается все остальное
    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
