Client module documentation
=================================================
Клиентское приложение для обмена сообщениями. Поддерживает
отправку сообщений пользователям которые находятся в сети, сообщения шифруются
с помощью алгоритма RSA с длинной ключа 2048 bit.

Поддерживает аргументы коммандной строки:

``python client.py -a {имя сервера} -p {порт} -n или --name {пользователь} -psw или --password {пароль}``

1. -a {имя сервера} - адрес сервера сообщений.
2. -p {порт} - порт по которому принимаются подключения
3. -n или --name - имя пользователя с которым произойдёт вход в систему.
4. -psw или --password - пароль пользователя.

Все опции командной строки являются необязательными, но имя пользователя и пароль необходимо использовать в паре.

Примеры использования:

* ``python client.py``

*Запуск приложения с параметрами по умолчанию.*

* ``python client.py -a ip_address -p some_port``

*Запуск приложения с указанием подключаться к серверу по адресу ip_address:some_port*

* ``python client.py -n test1 -p 123``

*Запуск приложения с пользователем test1 и паролем 123*

* ``python client.py -a ip_address -p some_port -n test1 -p 123``

*Запуск приложения с пользователем test1 и паролем 123 и указанием подключаться к серверу по адресу ip_address:some_port*

client.py
~~~~~~~~~

Запускаемый модуль содержит главный функционал программы.
Инициализация приложения заложена в основную функцию main

database.py
~~~~~~~~~~~~~~

.. autoclass:: client.database.ClientDatabase
    :members:

transport.py
~~~~~~~~~~~~~~

.. autoclass:: client.transport.ClientTransport
    :members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: client.main_window.ClientMainWindow
    :members:

set_client_dialog.py
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: client.set_client_dialog.UserNameDialog
    :members:

add_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client.add_contact.AddContactDialog
    :members:

del_contact.py
~~~~~~~~~~~~~~

.. autoclass:: client.del_contact.DelContactDialog
    :members:
