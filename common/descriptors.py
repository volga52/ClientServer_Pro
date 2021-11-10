import logging


class ValidPort:
    LOGGER = logging.getLogger('hosts')

    def __set__(self, instance, value):
        # if not isinstance(type(value), int):
        if value < 1024 or value > 65535:
            self.LOGGER.critical(f"Порт {value} не соответсвует параметрам"
                                 f"Значение должно быть числом больше 1024 и меньше 65535")
            raise ValueError(f'Значение должно быть числом больше 1024 и меньше 65535')
        instance.__dict__[self.my_attr] = value

    def __set_name__(self, owner, my_attr):
        self.my_attr = my_attr
