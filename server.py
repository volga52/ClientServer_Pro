import configparser
import os
import select
import socket
import sys
import threading

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt

sys.path.append('../')
from common.variables import *
from common.utils import get_message, send_message
from config_startup import SettingsStartArguments as Ssa
from common.decos import log_decor
from common.metaclasses import ServerMaker
from server.server_db import ServerStorage
from server.core import MessageProcessor
from server.main_window import MainWindow
# from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model

logger = logging.getLogger('server')
log_messages = logging.getLogger('messages')


def config_load():
    '''Парсер конфигурационного ini файла.'''
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    # Если конфиг файл загружен правильно, запускаемся, иначе конфиг по
    # умолчанию.
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    logger.info(f"Запущен server.py")

    path = os.path.dirname(os.path.abspath(__file__))  # Путь без файла
    path = os.path.join(path, r'server_base.db3')

    data_base = ServerStorage( path)

    config = config_load()

    launch_params = Ssa(
        config['SETTINGS']['Listen_Address'],
        config['SETTINGS']['Default_port'])
    server = MessageProcessor(launch_params, data_base)
    server.daemon = True
    server.start()

    # Если  указан параметр без GUI то запускаем простенький обработчик
    # консольного ввода
    if launch_params.gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                # Если выход, то завршаем основной цикл сервера.
                server.running = False
                server.join()
                break
    else:
        # Создаём графическое окуружение для сервера:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(data_base, server, config)

        # Запускаем GUI
        server_app.exec_()

        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    main()
