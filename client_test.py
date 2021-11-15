import os
import sys

from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication

sys.path.append('../')
from client.main_window import ClientMainWindow
from client.transport import ClientTransport
from common.variables import *
from common.config_startup import SettingsStartArguments as Ssa
from common.errors import ServerError
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
    client_passwd = connection_params.password

    client_app = QApplication(sys.argv)

    # Если имя пользователя не было указано в командной строке то запросим его
    start_dialog = UserNameDialog()

    if not client_name or client_passwd:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем
        # объект, иначе выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            logs_client.debug(
                f"Имя клиента: '{client_name}', password: '{client_passwd}'")
        else:
            exit(0)

    logs_client.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    # Создание базы данных
    database = ClientDatabase(client_name)

    # Запуск транспортного потока между сервером и клиентом.
    try:
        transport = ClientTransport(
            server_address,
            server_port,
            database,
            client_name,
            client_passwd,
            keys)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    del start_dialog

    # Создаём GUI
    main_window = ClientMainWindow(database, transport, keys)
    # Здесь происходит проброс сигналов из transport
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Программа Чат - в эфире {client_name}')
    client_app.exec_()

    # После закрытия графичесой оболочки закрывается все остальное
    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
