Common package
=================================================

Пакет общих утилит, использующихся в разных модулях проекта.

config_startup.py
~~~~~~~~~~~~~~~~~

.. autoclass:: common.config_startup.SettingsStartArguments
    :members:

Скрипт decos.py
---------------

.. automodule:: common.decos
    :members:

Скрипт descriptors.py
---------------------

.. autoclass:: common.descriptors.ValidPort
    :members:

Скрипт errors.py
---------------------

.. autoclass:: common.errors.IncorrectDataRecivedError
    :members:

.. autoclass:: common.errors.ServerError
    :members:

.. autoclass:: common.errors.NonDictInputError
    :members:

.. autoclass:: common.errors.ReqFieldMissingError
    :members:

Скрипт metaclasses.py
-----------------------

.. autoclass:: common.metaclasses.ServerMaker
    :members:

.. autoclass:: common.metaclasses.ClientMaker
    :members:

Скрипт utils.py
---------------------

common.utils. **get_message** (client)


    Утилита принимает и декодирует сообщения JSON. Принимает байты
    выдаёт словарь, если принято что-то другое отдаёт ошибку значения


common.utils. **send_message** (sock, message)


    Функция отправки словарей через сокет. Кодирует словарь в формат JSON и отправляет через сокет.


Скрипт variables.py
---------------------

Содержит разные глобальные переменные проекта.
