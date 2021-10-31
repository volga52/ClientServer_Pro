import sys
import os
import logging
from common.variables import LOGGING_LEVEL
sys.path.append('../')


PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(os.path.split(PATH)[0], r'files\hosts.log')

LOG_HOSTS = logging.getLogger('hosts')
FORMATTER = logging.Formatter(
    '%(asctime)-27s %(levelname)-10s %(filename)-23s %(message)s')

# создаём потоки вывода логов
STREAM_HANDLER = logging.StreamHandler(sys.stderr)
STREAM_HANDLER.setFormatter(FORMATTER)
STREAM_HANDLER.setLevel(logging.ERROR)

LOG_FILE = logging.FileHandler(PATH, encoding='utf8')
LOG_FILE.setFormatter(FORMATTER)

# создаём регистратор и настраиваем его
LOG_HOSTS.addHandler(STREAM_HANDLER)
LOG_HOSTS.addHandler(LOG_FILE)
LOG_HOSTS.setLevel(LOGGING_LEVEL)

# отладка
if __name__ == '__main__':
    LOG_HOSTS.critical('Критическая ошибка')
    LOG_HOSTS.error('Ошибка')
    LOG_HOSTS.debug('Отладочная информация')
    LOG_HOSTS.info('Информационное сообщение')
