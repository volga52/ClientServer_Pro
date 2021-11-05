"""Декораторы"""

import sys
import logging
import logs.configs.cofig_server_log
import logs.configs.config_client_log
# import logs.configs.config_messages_log
import logs.configs.config_host_log
# import traceback
# import inspect

# метод определения модуля, источника запуска.

if sys.argv[0].find('client') == -1:
    # если не клиент то сервер!
    LOGGER = logging.getLogger('server')
else:
    # ну, раз не сервер, то клиент
    LOGGER = logging.getLogger('client')


# Реализация в виде функции
def log_decor(func_inside):
    def log_startup(*args, **kwargs):
        run = func_inside(*args, **kwargs)
        LOGGER.debug(f"Была вызвана функция '{func_inside.__name__}' c параметрами {args}, {kwargs}. "
                     f'Вызов из модуля {func_inside.__module__}.', stacklevel=2)
                     # f"Вызов из функции '{traceback.format_stack()[0].strip().split()[-1]}'."
                     # f'Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
        return run
    return log_startup


# Реализация в виде класса
class Log:
    """Класс-декоратор"""
    def __call__(self, func_inside):
        def log_startup(*args, **kwargs):
            """Обертка"""
            run = func_inside(*args, **kwargs)
            LOGGER.debug(f'Была вызвана функция {func_inside.__name__} c параметрами {args}, {kwargs}. '
                         f'Вызов из модуля {func_inside.__module__}.', stacklevel=2)
                         # f'Вызов из функции {traceback.format_stack()[0].strip().split()[-1]}.'
                         # f'Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
            return run
        return log_startup
