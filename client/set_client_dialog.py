from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel , qApp
from PyQt5.QtCore import QEvent


# Стартовый диалог с выбором имени пользователя
class UserNameDialog(QDialog):
    '''
    Класс реализующий стартовый диалог с запросом логина и пароля
    пользователя.
    '''

    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Привет!')
        self.setFixedSize(208, 189)

        self.label = QLabel('Введите имя пользователя:', self)
        self.label.move(20, 10)
        self.label.adjustSize()

        self.client_name = QLineEdit(self)          # Получение имени
        self.client_name.setFixedSize(164, 20)      # Хранится в атрубуте text
        self.client_name.move(20, 30)

        self.btn_ok = QPushButton('Начать', self)
        self.btn_ok.move(20, 104)
        self.btn_ok.setFixedSize(164, 30)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(20, 139)
        self.btn_cancel.setFixedSize(164, 30)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.label_passwd = QLabel('Введите пароль:', self)
        self.label_passwd.move(20, 55)
        self.label_passwd.adjustSize()

        self.client_passwd = QLineEdit(self)          # Получение имени
        self.client_passwd.setFixedSize(164, 20)      # Хранится в атрубуте text
        self.client_passwd.move(20, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)

        self.show()

    # Обработчик кнопки ОК, если поля ввода не пустые,
    # ставим флаг и завершаем приложение.
    def click(self):
        '''Метод обработки кнопки ОК'''
        if self.client_name.text() and self.client_passwd.text():
            self.ok_pressed = True
            qApp.exit()


if __name__ == '__main__':
    app = QApplication([])
    dial = UserNameDialog()
    app.exec_()
