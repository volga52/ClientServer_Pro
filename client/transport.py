import socket
import sys
import time
import logging
import json
import threading

from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../')
# import logs.configs.config_client_log
# import logs.configs.config_messages_log

from common.utils import get_message, send_message
from common.variables import *
from common.errors import ServerError, ReqFieldMissingError

logger = logging.getLogger('client')
log_messages = logging.getLogger('messages')

# Блокировка для сокета
socket_lock = threading.Lock()


# Класс - Транспорт, отвечает за взаимодействие с сервером
class ClientTransport(threading.Thread, QObject):
    # Создание своих собственных сигналов: новое сообщение и потеря соединения
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, ip_address, port, database, username):
        # Конструкторы предков
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        # Сокет для работы с сервером
        self.transport = None

        # Устанавливаем соединение:
        self.create_connect(ip_address, port)

        # Обновляем таблицы известных пользователей и контактов
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            # Флаг продолжения работы транспорта.
        self.running = True

    def create_connect(self, server_address, server_port):
        """
        Инициализация сокета и
        сообщение серверу о присутствии
        """
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут необходим для освобождения сокета.
        self.transport.settimeout(5)

        # Соединяемся, 3 попыток соединения, флаг успеха ставим в True если удалось
        connected = False
        for i in range(3):
            logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((server_address, server_port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        # Если соединится нет - исключение
        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        logger.debug('Установлено соединение с сервером')

        try:
            with socket_lock:
                send_message(self.transport, self.create_presence())
                self.process_server_ans(get_message(self.transport))
        except (OSError, json.JSONDecodeError):
            logger.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')
        else:
            # Соединение установлено
            logger.info('Соединение с сервером успешно установлено.')

    def create_presence(self):
        """Функция генерирует сообщение о присутствии клиента"""
        ret_out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username
            }
        }
        log_messages.debug(f"Сформировано '{PRESENCE}' сообщение пользователя '{self.username}'")
        return ret_out

    # *Функция обрабатывающяя сообщения от сервера. Ничего не возращает.
    # Генерирует исключение при ошибке.
    def process_server_ans(self, message):
        """
        Функция обрабатывающяя сообщения от сервера. Ничего не возращает.
        Генерирует исключение при ошибке.
        """
        log_messages.debug(f'Сервер принял, отправил сообщение: {message}')
        # Если это подтверждение
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            elif message[RESPONSE] == 400:
                raise ServerError(f'400 : {message[ERROR]}')
            else:
                logger.debug(f'Принят неизвестный код подтверждения {message[RESPONSE]}')

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о новом сообщении
        elif ACTION in message \
                and message[ACTION] == MESSAGE \
                and SENDER in message \
                and DESTINATION in message \
                and MESSAGE_TEXT in message \
                and message[DESTINATION] == self.username:
            print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                  f'\n{message[MESSAGE_TEXT]}')
            self.database.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message[SENDER])

        # raise ReqFieldMissingError(RESPONSE)

    # *Функция запрашивает список контактов с сервера и возвращает его
    def contacts_list_update(self):
        """Функция запрашивает список контактов с сервера и возвращает его"""
        logger.debug(f'Запрос контакт листа для пользователся {self.name}')
        request = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        logger.debug(f'Сформирован запрос {request}')
        with socket_lock:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        logger.debug(f'Получен ответ {answer}')
        if RESPONSE in answer and answer[RESPONSE] == 202:
            for contact in answer[DATA]:
                self.database.add_contact(contact)
        else:
            logger.error('Не удалось обновить список контактов.')

    # *Функция обновляет таблицу известных пользователей.
    def user_list_update(self):
        """Функция обновляет таблицу известных пользователей"""
        logger.debug(f'Запрос списка известных пользователей {self.username}')
        request = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            send_message(self.transport, request)
            answer = get_message(self.transport)
        if RESPONSE in answer and answer[RESPONSE] == 202:
            self.database.add_users(answer[DATA])
        else:
            logger.error('Не удалось обновить список известных пользователей.')

    # *Функция объявляет серверу новый контакт
    def add_contact(self, contact):
        """Функция объявляет серверу новый контакт"""
        logger.debug(f'Создание контакта {contact}')
        request = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, request)
            self.process_server_ans(get_message(self.transport))

    # *Функция удаления клиента на сервере
    def remove_contact(self, contact):
        """Фукция удаляет клиента на сервере"""
        logger.debug(f'Удаление контакта {contact}')
        request = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, request)
            self.process_server_ans(get_message(self.transport))

    # *Функция закрывает соединения, отправляет сообщение о выходе.
    def transport_shutdown(self):
        """
        Функция отправляет сообщение о выходе.
        Флаг работы ставит в False
        """
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        logger.debug(f"Поток клиента {self.username} завершил работу.")
        time.sleep(0.5)

    # Функция отправляет сообщения на сервер
    def send_message(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            logger.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        """Функция запускает основные процессы взаимодействия с сервером"""
        logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то отправка может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    logger.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
