import json

import sys
import os
import unittest

sys.path.append(os.path.join(os.getcwd(), '..'))

from common.variables import ENCODING, ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, RESPONSE, ERROR
from common.utils import get_message


class SocketSpoof:
    def __init__(self, test_dict):
        self.info = test_dict
        self.encoded_message = None
        self.received_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.info)
        # кодирует сообщение в байты
        self.encoded_message = json_test_message.encode(ENCODING)
        # сохраняем что должно было отправлено в сокет
        self.received_message = message_to_send

    def recv(self, max_len):
        json_test_message = json.dumps(self.info)
        return json_test_message.encode(ENCODING)


class TestMessageFunc(unittest.TestCase):
    test_dict_send = {
        ACTION: PRESENCE,
        TIME: 111111.111111,
        USER: {
            ACCOUNT_NAME: 'test_name'
        }
    }
    positive_response = {RESPONSE: 200}
    negative_response = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_get_message(self):
        sock_positive = SocketSpoof(self.positive_response)
        sock_negative = SocketSpoof(self.negative_response)

        self.assertEqual(get_message(sock_positive), self.positive_response)
        self.assertEqual(get_message(sock_negative), self.negative_response)


if __name__ == '__main__':
    unittest.main()
