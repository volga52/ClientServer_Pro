"""Рабочее состояние на 19.10.21 11:00"""
import argparse
import sys

import logging
import logs.configs.config_host_log

from common.variables import DEFAULT_PORT, DEFAULT_IP_ADDRESS
from decos import log_decor


@log_decor
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


class SettingPortAddress:
    LOGGER = logging.getLogger('hosts')
    LOGGER.info(f"Входящие параметры '{' '.join(sys.argv)}'")

    def __init__(self, parser_):
        self.name_file_run = parser_[0]
        self.address_return = parser_[1]
        self.port_return = parser_[2]
        # self.client_mode_return = parser_[3]
        self.client_name = parser_[3]

    @log_decor
    def get_port(self):
        self.LOGGER.debug(f'Обрабатывается порт {self.port_return}')
        if self.port_return < 1024 or self.port_return > 65535:
            self.LOGGER.critical(f"Неподходящий порт {self.port_return} Допустимы адреса с 1024 до 65535.")
            sys.exit(1)

        return self.port_return

    @log_decor
    def get_address(self):
        self.LOGGER.debug(f'Адес соединения {self.address_return}')
        return self.address_return


    @log_decor
    def get_client_name(self):
        self.LOGGER.debug(f"Поьзователь '{self.client_name}'")
        return self.client_name
