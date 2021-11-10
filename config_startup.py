import argparse
import sys
import logging

from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS
# from common.decos import log_decor
from common.descriptors import ValidPort

LOGGER = logging.getLogger('hosts')


class SettingsStartArguments:
    LOGGER = logging.getLogger('hosts')

    port_return = ValidPort()

    def __init__(self):
        self.name_file_run = None
        self.address_return = None
        self.port_return = DEFAULT_PORT
        self.client_name = None

        self.init_class()

    def init_class(self):
        parser_ = SettingsStartArguments.create_arg_parser()
        self.name_file_run, self.address_return, self.port_return, self.client_name = parser_

    @staticmethod
    def create_arg_parser():
        """Предопределение адреса для сервера или клиента """
        name_file_run = 'server' if (sys.argv[0].find('client') == -1) else 'client'
        set_ip_address = DEFAULT_IP_ADDRESS if name_file_run == 'client' else ''

        """Создаём парсер аргументов коммандной строки"""
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', default=set_ip_address, nargs='?')
        parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-n', '--name', default=None, nargs='?')

        namespace = parser.parse_args()
        address_return = namespace.a
        port_return = namespace.p
        client_name = namespace.name

        LOGGER.debug(f"Выходящие значения '{namespace}'")

        return name_file_run, address_return, int(port_return), client_name
