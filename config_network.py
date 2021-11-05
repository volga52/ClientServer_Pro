import argparse
import sys

import logging
import logs.configs.config_host_log

from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS
from decos import log_decor
from descriptors import ValidPort


LOGGER = logging.getLogger('hosts')


class SettingPortAddress:
    LOGGER = logging.getLogger('hosts')
    # logger.info(f"Входящие параметры '{' '.join(sys.argv)}'")

    port_return = ValidPort()

    def __init__(self, parser_):
        self.name_file_run = parser_[0]
        self.address_return = parser_[1]
        self.port_return = parser_[2]
        self.client_name = parser_[3]

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

        return [name_file_run, address_return, int(port_return), client_name]
