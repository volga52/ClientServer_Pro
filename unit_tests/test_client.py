# import sys
# import os
import unittest
# sys.path.append(os.path.join(os.getcwd(), '..'))
from client import Client
from common.variables import RESPONSE, ERROR


class TestClientCase(unittest.TestCase):
    def test_create_presence_noNone(self):
        test_object = Client.create_presence()
        self.assertIsNotNone(test_object)

    def test_create_presence_instance(self):
        self.assertIsInstance(Client.create_presence(), type({}))

    def test_process_ans_equal(self):
        self.assertEqual(Client.process_ans({RESPONSE: 200}), '200 : OK')

    def test_process_ans_equal_message(self):
        self.assertNotEqual(Client.process_ans({RESPONSE: 1, ERROR: '2'}), '200 : OK')

    def test_process_ans_valueException(self):
        with self.assertRaises(Exception):
            Client.process_ans({})

    def test_400_ans(self):
        self.assertEqual(Client.process_ans({RESPONSE: 400, ERROR: 'error'}), '400 : error')

if __name__ == '__main__':
    unittest.main()
