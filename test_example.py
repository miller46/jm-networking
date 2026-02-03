import unittest
from unittest.mock import patch, Mock
from jm_networking import ObjectNetworking
from tests.example_model import ExampleModel


class TestObjectNetworking(unittest.TestCase):

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

        status, deserialized = ObjectNetworking.get(
            "https://jsonplaceholder.typicode.com/todos/1",
            ExampleModel
        )

        self.assertEqual(status, 200)
        self.assertIsInstance(deserialized, ExampleModel)
        self.assertEqual(deserialized.id, 1)
        self.assertEqual(deserialized.userId, 1)
        self.assertEqual(deserialized.title, "delectus aut autem")
        self.assertEqual(deserialized.completed, False)

        mock_get.assert_called_once_with(
            "https://jsonplaceholder.typicode.com/todos/1",
            None
        )

    @patch('jm_networking.requests.post')
    def test_post_serialized(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        test_obj = ExampleModel(id=1, userId=1, title="Test todo", completed=False)

        response = ObjectNetworking.post(
            test_obj,
            "https://jsonplaceholder.typicode.com/todos",
            params=None
        )

        self.assertEqual(response.status_code, 201)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        self.assertIn('json', call_kwargs)
        self.assertEqual(call_kwargs['json']['id'], 1)
        self.assertEqual(call_kwargs['json']['userId'], 1)
        self.assertEqual(call_kwargs['json']['title'], "Test todo")
        self.assertEqual(call_kwargs['json']['completed'], False)

    @patch('jm_networking.requests.put')
    def test_put_serialized(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        test_obj = ExampleModel(id=1, userId=1, title="Updated todo", completed=True)

        response = ObjectNetworking.cosimo_put(
            test_obj,
            "https://jsonplaceholder.typicode.com/todos/1",
            params=None
        )

        self.assertEqual(response.status_code, 200)

        mock_put.assert_called_once()
        call_kwargs = mock_put.call_args.kwargs
        self.assertIn('json', call_kwargs)
        self.assertEqual(call_kwargs['json']['title'], "Updated todo")
        self.assertEqual(call_kwargs['json']['completed'], True)

    @patch('jm_networking.requests.delete')
    def test_delete_serialized(self, mock_delete):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        test_obj = ExampleModel(id=1)

        response = ObjectNetworking.cosimo_delete(
            test_obj,
            "https://jsonplaceholder.typicode.com/todos/1",
            params=None
        )

        self.assertEqual(response.status_code, 204)

        mock_delete.assert_called_once()


if __name__ == '__main__':
    unittest.main()
