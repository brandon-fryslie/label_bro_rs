import unittest
import json
from unittest.mock import patch, MagicMock
import base64
import io
from PIL import Image
from label_bro.app import app
from label_bro.utils import printer_utils

class TestLabelBroApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_index(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Label Bro", response.data)

    @patch('label_bro.utils.printer_utils.check_printer_connection', return_value=True)
    @patch('label_bro.utils.label_creation.process_label', return_value=None)
    def test_print_labels(self, mock_process_label, mock_check_printer_connection) -> None:
        # Test with valid input
        response = self.app.post('/printLabels', json={
            'data': {
                'text': 'Test Label',
                'shouldPrintFullLabel': True,
                'shouldPrintSmallLabel': True
            }
        })
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json['status'], "Labels processed successfully")

        # Test with invalid input
        response = self.app.post('/printLabels', json={
            'data': {
                'text': '',
                'shouldPrintFullLabel': True,
                'shouldPrintSmallLabel': True
            }
        })
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid input', response_json['error'])

        # Test with printer not connected
        mock_check_printer_connection.return_value = False
        response = self.app.post('/printLabels', json={
            'data': {
                'text': 'Test Label',
                'shouldPrintFullLabel': True,
                'shouldPrintSmallLabel': True
            }
        })
        response_json = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('Printer not connected', response_json['error'])

    @patch('label_bro.app.client.images.generate')
    def test_ai_generate(self, mock_generate):
        # Create a simple black square image for testing
        image = Image.new('RGB', (10, 10), color='black')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        mock_image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        mock_generate.return_value = {
            'data': [{'b64_json': mock_image_data}]
        }

        # Test with valid prompt
        response = self.app.post('/aiGenerate', json={'prompt': 'Test prompt'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('image', data)
        self.assertIn('dithered_image', data)

        # Test with empty prompt
        response = self.app.post('/aiGenerate', json={'prompt': ''})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid input', response.data)

        # Test the conversion and dithering logic
        image_data = base64.b64decode(mock_generate.return_value['data'][0]['b64_json'])
        image = Image.open(io.BytesIO(image_data))
        self.assertIsInstance(image, Image.Image)

        dithered_image = printer_utils.apply_dithering(image)
        self.assertIsInstance(dithered_image, Image.Image)

if __name__ == '__main__':
    unittest.main()
