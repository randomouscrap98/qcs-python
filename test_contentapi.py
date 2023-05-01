
import unittest
import contentapi
import logging

class TestContentapi(unittest.TestCase):

    def setUp(self) -> None:
        # MAYBE change this some time?
        self.api = contentapi.ApiContext("https://oboy.smilebasicsource.com/api", logging)

    def test_apistatus(self):
        result = self.api.api_status()
        self.assertTrue("version" in result)

    def test_is_token_valid_none(self):
        self.assertFalse(self.api.is_token_valid())

    def test_is_token_valid_garbage(self):
        self.api.token = "literalgarbage"
        self.assertFalse(self.api.is_token_valid())


if __name__ == '__main__':
    unittest.main()