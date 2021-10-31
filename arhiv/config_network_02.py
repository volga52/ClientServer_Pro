import argparse
import sys

import logging
import logs.configs.config_host_log

from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS
from decos import log_decor


class ValidPort:
    LOGGER = logging.getLogger('hosts')

    def __set__(self, instance, value):
        # if not isinstance(type(value), int):
        if value < 1024 or value > 65535:
            raise ValueError(f'Значение должно быть числом больше 1024 и меньше 65535')
        instance.__dict__[self.my_attr] = value

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr


class SettingNetWork:
    port_return = ValidPort()

    def __init__(self):
        self.name_file_run
        self.address
        self.port
        self.name_client

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
        return [name_file_run, address_return, int(port_return), client_name]

