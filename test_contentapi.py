
import unittest
import contentapi
import logging

class TestContentapi(unittest.TestCase):

    def setUp(self) -> None:
        # MAYBE change all these some time? Should connect to a local instance!!
        self.api = contentapi.ApiContext("https://oboy.smilebasicsource.com/api", logging)
        self.known_content_id = 384
        self.known_name = "Megathread"

    def test_apistatus(self):
        result = self.api.api_status()
        self.assertIn("version", result)

    def test_is_token_valid_none(self):
        self.assertFalse(self.api.is_token_valid())

    def test_is_token_valid_garbage(self):
        self.api.token = "literalgarbage"
        self.assertFalse(self.api.is_token_valid())
    
    def test_get_by_id_notfound(self):
        try:
            self.api.get_by_id("content", 0)
        except contentapi.NotFoundError:
            return

        self.assertFalse(True, "Didn't throw expected exception!")

    def test_get_by_id_known(self):
        result = self.api.get_by_id("content", self.known_content_id)
        self.assertIn("id", result)
        self.assertEqual(result["id"], self.known_content_id)

    def test_basic_search(self):
        result = self.api.basic_search(self.known_name)
        self.assertIn("content", result["objects"])
        self.assertTrue(len(result["objects"]["content"]) >= 1)
        self.assertTrue(any(self.known_name in item["name"] for item in result["objects"]["content"]))

if __name__ == '__main__':
    unittest.main()