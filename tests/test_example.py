import unittest
from unittest.mock import patch, Mock
from jm_networking import JmNetwork
from example_model import ExampleModel


class TestJmNetworkDeserialization(unittest.TestCase):

    @patch('jm_networking.requests.get')
    def test_get_deserialized(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "userId": 1,
            "id": 1,
            "title": "delectus aut autem",
            "completed": False
        }
        mock_get.return_value = mock_response

        status, deserialized = JmNetwork.get_deserialized(
            "https://jsonplaceholder.typicode.com/todos/1",
            ExampleModel
        )

        self.assertEqual(status, 200)
        self.assertIsInstance(deserialized, ExampleModel)
        self.assertEqual(deserialized.id, 1)
        self.assertEqual(deserialized.userId, 1)
        self.assertEqual(deserialized.completed, False)

        mock_get.assert_called_once_with(
            "https://jsonplaceholder.typicode.com/todos/1",
            None
        )


if __name__ == '__main__':
    unittest.main()
