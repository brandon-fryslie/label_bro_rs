from unittest.mock import patch
import unittest
from flask.testing import FlaskClient
from PIL import Image
import io
import base64
from label_bro.app import app

class TestPrinterDiscoveryIntegration(unittest.TestCase):

    def setUp(self) -> None:
        self.app: FlaskClient = app.test_client()
        self.app.testing = True

    @patch('brother_ql.backends.helpers.discover')
    def test_discover_printers(self, mock_discover) -> None:
        # Mock the discover function to return a list of printers
        mock_discover.side_effect = [
            [{'identifier': 'usb://0x04f9:0x209b', 'instance': None}],
            [{'identifier': 'tcp://192.168.7.150:9100', 'instance': None}]
        ]

        response = self.app.get('/discoverPrinters')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('printers', data)
        self.assertEqual(len(data['printers']), 2)

class TestPrintImageIntegration(unittest.TestCase):

    def setUp(self) -> None:
        self.app: FlaskClient = app.test_client()
        self.app.testing = True

    @patch('brother_ql.backends.helpers.send')
    def test_print_image(self, mock_send) -> None:
        # Mock the send function to simulate successful printing
        mock_send.return_value = {'status': 'success'}

        # Create a simple black square image for testing
        image = Image.new('RGB', (10, 10), color='black')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        response = self.app.post('/printImage', json={'image_data': image_data})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'Image printed successfully')
        mock_send.assert_called_once()

class TestPrintLabelsIntegration(unittest.TestCase):

    def setUp(self) -> None:
        self.app: FlaskClient = app.test_client()
        self.app.testing = True

    @patch('brother_ql.backends.helpers.send')
    def test_print_labels(self, mock_send) -> None:
        # Mock the send function to simulate successful printing
        mock_send.return_value = {'status': 'success'}

        response = self.app.post('/printLabels', json={
            'data': {
                'text': 'Test Label',
                'shouldPrintFullLabel': True,
                'shouldPrintSmallLabel': True
            }
        })
        self.assertEqual(response.status_code, 200)
        response_json = response.get_json()
        self.assertEqual(response_json['status'], "Labels processed successfully")
        mock_send.assert_called()

if __name__ == '__main__':
    unittest.main()
