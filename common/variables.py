"""Константы"""
import logging

# Порт по умолчанию для сетевого ваимодействия
DEFAULT_PORT = 7777
# DEFAULT_PORT = 77777              # bad port for debug

# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_ADDRESS = '127.0.0.1'
# DEFAULT_IP_ADDRESS = '192.168.3.8'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длинна сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# Кодировка проекта
ENCODING = 'utf-8'
# LOGGING_LEVEL = 'DEBUG'
LOGGING_LEVEL = logging.INFO

# База данных для хранения данных сервера:
SERVER_DB = 'sqlite:///server_base.db3'
SERVER_CONFIG = 'server.ini'

# Прококол JIM основные ключи:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'
DATA_BIN = 'bin'
PUBLIC_KEY = 'pubkey'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
DATA = 'data'
# DATA_LIST = 'data_list'
GET_CONTACTS = 'get_contacts'
# Комнады
# MESSAGE = 'message'
MESSAGE = 'm-'
HISTORY = 'history'
CONTACTS = 'contacts'
ADD_CONTACT = 'add'
REMOVE_CONTACT = 'remove'
USERS_REQUEST = 'get_users'
PUBLIC_KEY_REQUEST = 'pubkey_need'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'

# Словари - ответы:
# 200
RESPONSE_200 = {RESPONSE: 200}
# 202
RESPONSE_202 = {
    RESPONSE: 202,
    DATA: None
}
# 400
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
# 205
RESPONSE_205 = {
    RESPONSE: 205
}
# 511
RESPONSE_511 = {
    RESPONSE: 511,
    DATA_BIN: None
}
