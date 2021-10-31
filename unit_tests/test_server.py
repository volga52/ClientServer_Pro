# import sys
# import os
# import unittest
import unittest
# sys.path.append(os.path.join(os.getcwd(), '..'))

from server import Server
from common.variables import RESPONSE, ERROR, TIME, USER, ACCOUNT_NAME, ACTION, PRESENCE


class TestServerCase(unittest.TestCase):
    return_dict = {
        RESPONSE: 400,
        ERROR: 'Bad Request'
    }

    def test_no_action(self):
        self.assertEqual(Server.process_client_message({TIME: '', USER: {ACCOUNT_NAME: 'Guest'}}),
                         self.return_dict)

    def test_wrong_action(self):
        self.assertEqual(Server.process_client_message(
            {ACTION: 'Wrong', TIME: '', USER: {ACCOUNT_NAME: 'Guest'}}), self.return_dict)

    def test_no_time(self):
        self.assertEqual(Server.process_client_message(
            {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.return_dict)

    def test_no_user(self):
        self.assertEqual(Server.process_client_message(
            {ACTION: PRESENCE, TIME: ''}), self.return_dict)

    def test_unknown_user(self):
        self.assertEqual(Server.process_client_message(
            {ACTION: PRESENCE, TIME: '', USER: {ACCOUNT_NAME: 'I'}}), self.return_dict)


if __name__ == '__main__':
    unittest.main()
