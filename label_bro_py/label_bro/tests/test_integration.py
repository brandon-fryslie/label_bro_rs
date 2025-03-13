import json
import unittest
from unittest.mock import patch
from flask.testing import FlaskClient
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from label_bro.app import app

class TestLabelPreviewIntegration(unittest.TestCase):

    def setUp(self) -> None:
        self.app: FlaskClient = app.test_client()
        self.app.testing = True

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
        # Send a request to generate a label preview
        response = self.app.post('/previewLabels', json={
            'data': {
                'text': 'Test Label',
                'shouldPrintFullLabel': True,
                'shouldPrintSmallLabel': False
            }
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        # Check that the full label image is returned
        self.assertIn('full_labels', data)
        self.assertGreater(len(data['full_labels']), 0)

        # Decode the base64 image
        image_data = base64.b64decode(data['full_labels'][0].split(',')[1])
        image = Image.open(io.BytesIO(image_data))

        # Check that the text is not cut off
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("Impact.ttf", 10)
        except IOError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), 'Test Label', font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        self.assertLessEqual(text_width, image.width)
        self.assertLessEqual(text_height, image.height)

if __name__ == '__main__':
    unittest.main()
