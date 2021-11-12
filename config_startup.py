import argparse
import sys
import logging

sys.path.append('../')
from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS
from common.descriptors import ValidPort
from logs.configs import config_host_log

LOGGER = logging.getLogger('hosts')


class SettingsStartArguments:
    # LOGGER = logging.getLogger('hosts')

    port_return = ValidPort()

    def __init__(self, default_address=None, default_port=None):
        self.name_file_run = None
        self.address_return = default_address
        self.port_return = DEFAULT_PORT if default_port == None \
            else int(default_port)
        self.client_name = None
        self.password = None
        self.gui_flag = None

        self.init_class()

    def init_class(self):
        parser_ = SettingsStartArguments.create_arg_parser(
            self.address_return,
            self.port_return)

        self.name_file_run, \
        self.address_return, \
        self.port_return, \
        self.client_name, \
        self.password, \
        self.gui_flag = parser_

    @staticmethod
    def create_arg_parser(ip_address, port_return):
        LOGGER.debug(f"Зупущена config_startup c параметрами {sys.argv}")
        """Предопределение адреса для сервера или клиента """
        name_file_run = 'server' if (sys.argv[0].find('client') == -1) else 'client'
        #  = DEFAULT_IP_ADDRESS if name_file_run == 'client' else ''
        if ip_address == None:
            ip_address = '' if name_file_run == 'server' \
                else DEFAULT_IP_ADDRESS

        """Создаём парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', default=ip_address, nargs='?')
        parser.add_argument('-p', default=port_return, type=int, nargs='?')
        parser.add_argument('-n', '--name', default=None, nargs='?')
        parser.add_argument('-psw', '--password', default='', nargs='?')
        parser.add_argument('--no_gui', action='store_true')

        namespace = parser.parse_args()

        address_return = namespace.a
        port_return = namespace.p
        client_name = namespace.name
        password = namespace.password
        gui_flag = namespace.no_gui

        LOGGER.debug(f"Выходящие значения '{namespace}'")

        return name_file_run, address_return, int(port_return), \
               client_name, password, gui_flag
