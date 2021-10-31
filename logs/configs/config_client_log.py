import sys
import os
import logging
from common.variables import LOGGING_LEVEL
sys.path.append('../')


FORMATTER_FOR_CLIENT = logging.Formatter(
    '%(asctime)-27s %(levelname)-10s %(filename)-23s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(os.path.split(PATH)[0], r'files\client.log')

# создаём потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMATTER_FOR_CLIENT)
STREAM_HANDLER.setLevel(logging.ERROR)

LOG_FILE = logging.FileHandler(PATH, encoding='utf8')
LOG_FILE.setFormatter(FORMATTER_FOR_CLIENT)

# создаём регистратор и настраиваем его
LOG_CLIENT = logging.getLogger('client')
LOG_CLIENT.addHandler(STREAM_HANDLER)
LOG_CLIENT.addHandler(LOG_FILE)
LOG_CLIENT.setLevel(LOGGING_LEVEL)

# отладка
if __name__ == '__main__':
    LOG_CLIENT.critical('Критическая ошибка')
    LOG_CLIENT.error('Ошибка')
    LOG_CLIENT.debug('Отладочная информация')
    LOG_CLIENT.info('Информационное сообщение')
