import logging.handlers
import os
import sys

sys.path.append('../')

from common.variables import LOGGING_LEVEL


PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(os.path.split(PATH)[0], r'files\server.log')

LOG_SERVER = logging.getLogger('server')

FORMATTER_FOR_SERVER = logging.Formatter('%(asctime)-27s %(levelname)-10s %(filename)-23s %(message)s')

STREAM_HANDLER = logging.StreamHandler(sys.stderr)
# STREAM_HANDLER = logging.StreamHandler(sys.stdout)
STREAM_HANDLER.setFormatter(FORMATTER_FOR_SERVER)

# STREAM_HANDLER.setLevel(logging.ERROR)
STREAM_HANDLER.setLevel(logging.WARNING)

# NAME_LOG_FILE = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='midnight')
NAME_LOG_FILE = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf-8', interval=1, when='midnight')
NAME_LOG_FILE.setFormatter(FORMATTER_FOR_SERVER)

LOG_SERVER.addHandler(STREAM_HANDLER)
LOG_SERVER.addHandler(NAME_LOG_FILE)
LOG_SERVER.setLevel(LOGGING_LEVEL)

if __name__ == '__main__':
    # print(PATH)
    LOG_SERVER.critical('Критическая ошибка')
    LOG_SERVER.error('Ошибка')
    LOG_SERVER.debug('Отладочная информация')
    LOG_SERVER.info('Информационное сообщение')
