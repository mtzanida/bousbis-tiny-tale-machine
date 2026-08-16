import json
import unittest

from lambda_function import lambda_handler


class StoryFunctionTests(unittest.TestCase):
    def test_creates_personalised_story(self):
        event = {
            "body": json.dumps({
                "name": "Anastasia",
                "animal": "tiny blue elephant",
                "place": "the Castle Above the Clouds",
                "mood": "magical",
            })
        }
        result = lambda_handler(event, None)
        payload = json.loads(result["body"])
        self.assertEqual(result["statusCode"], 200)
        self.assertIn("Anastasia", payload["story"])
        self.assertIn("tiny blue elephant", payload["story"])

    def test_invalid_json_returns_400(self):
        result = lambda_handler({"body": "{"}, None)
        self.assertEqual(result["statusCode"], 400)


if __name__ == "__main__":
    unittest.main()
