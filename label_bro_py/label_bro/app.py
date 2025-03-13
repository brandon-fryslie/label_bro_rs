import dataclasses
import functools
import logging
import os
import traceback
from datetime import datetime
from typing import List, Tuple, Union, Dict, Any

import flask
import io
import base64
from dotenv import load_dotenv
from PIL import Image
import openai

import usb.core
from label_bro.utils import label_creation, printer_utils, discover_printers_backend

load_dotenv()  # take environment variables from .env.

# Initialize the OpenAI client
client = openai.OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)

if not client.api_key:
    print("Warning: OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

app = flask.Flask(__name__)

LABEL_WIDTH = 696


@dataclasses.dataclass
class ErrorResult:
    error: str
    error_long: str
    filename: str
    line_number: int
    stack_trace: str


@app.context_processor
def inject_common_data():
    return {
        'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'app_name': 'Label Bro 😎',  # Example of additional common data
    }


def format_error_response(exception: Exception, error_type: str) -> ErrorResult:
    tb = exception.__traceback__
    repo_root = os.path.dirname(os.path.abspath(__file__))
    filename = str(os.path.relpath(tb.tb_frame.f_code.co_filename, start=repo_root))
    line_number = tb.tb_lineno
    stack_trace = traceback.format_exc()

    error_long = f"{error_type} in {filename} at line {line_number}:\n{stack_trace}"

    result = ErrorResult(
        error=f'{error_type}: {str(exception)}',
        error_long=error_long,
        filename=filename,
        line_number=line_number,
        stack_trace=stack_trace,
    )

    return result


@app.route('/')
def index():
    return flask.render_template(
        'index.html',
        custom_message="Yo. I'm your label Bro. Fist bump Bro."
    )


def error_handler(func: Any) -> Any:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return flask.jsonify(format_error_response(e, 'Error')), 500
    return wrapper

@app.route('/printLabels', methods=['POST'])
@error_handler
def print_labels_endpoint() -> Tuple[flask.Response, int]:
    data = flask.request.json.get('data', {})
    text_content = data.get('text', '')
    should_print_full = data.get('shouldPrintFullLabel', True)
    should_print_small = data.get('shouldPrintSmallLabel', True)


    if not text_content:
        return flask.jsonify({'error': 'Invalid input'}), 400

    if not isinstance(should_print_full, bool) or not isinstance(should_print_small, bool):
        return flask.jsonify({'error': 'Invalid input: shouldPrintFullLabel and shouldPrintSmallLabel must be boolean'}), 400

    if not printer_utils.check_printer_connection():
        return flask.jsonify({'error': 'Printer not connected'}), 400

    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        split_line = line.split(';')
        label_text = split_line[0]
        repeat_times = int(split_line[1]) if len(split_line) > 1 else 1

        if repeat_times > 5:
            return flask.jsonify({'error': f"{repeat_times} labels? Too many!"}), 400

        for i in range(repeat_times):
            if should_print_full:
                status = label_creation.process_label(label_text, LABEL_WIDTH, 'full')
                if status:
                    return flask.jsonify({'error': str(status)}), 500

            if should_print_small:
                status = label_creation.process_label(label_text, LABEL_WIDTH, 'small')
                if status:
                    return flask.jsonify({'error': str(status)}), 500

    return flask.jsonify({'status': 'Labels processed successfully'}), 200


@app.route('/previewLabels', methods=['POST'])
def preview_labels_endpoint() -> Tuple[flask.Response, int]:
    data = flask.request.json.get('data', {})
    text_content = data.get('text', '')
    should_print_full: bool = data.get('shouldPrintFullLabel', True)
    should_print_small: bool = data.get('shouldPrintSmallLabel', True)

    if not text_content:
        raise ValueError("Input is empty!")

    full_images = []
    small_images = []

    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        split_line = line.split(';')
        label_text = split_line[0]

        if should_print_full:
            full_image, error = label_creation.create_full_width_label_image(label_text, LABEL_WIDTH)
            if error:
                raise error
            full_images.append(full_image)

        if should_print_small:
            small_image, error = label_creation.create_small_label_image(label_text, LABEL_WIDTH)
            if error:
                raise error
            small_images.append(small_image)

    full_labels_base64 = [label_creation.img_to_base64(img) for img in full_images]
    small_labels_base64 = [label_creation.img_to_base64(img) for img in small_images]

    return flask.jsonify({
        'full_labels': full_labels_base64,
        'small_labels': small_labels_base64
    }), 200


@app.route('/aiGenerate', methods=['POST'])
def ai_generate() -> Tuple[flask.Response, int]:
    data = flask.request.json
    prompt = data.get('prompt', '')

    try:
        if not prompt:
            return flask.jsonify({'error': 'Invalid input: prompt is empty'}), 400

        response = client.images.generate(prompt=prompt, n=1, size="512x512", response_format="b64_json")

        logging.error("ERROR!!!!!!")
        logging.error(response)


        if 'data' not in response or not response['data']:
            return flask.jsonify({'error': 'No image data returned from OpenAI'}), 500

        image_data = response['data'][0]['b64_json']

        # Convert the base64 image data to a PIL image
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))

        # Apply dithering to the image
        dithered_image = printer_utils.apply_dithering(image)

        # Convert the dithered image back to base64
        dithered_buffer = io.BytesIO()
        dithered_image.save(dithered_buffer, format='PNG')
        dithered_image_base64 = base64.b64encode(dithered_buffer.getvalue()).decode('utf-8')

        return flask.jsonify({
            'image': f'data:image/png;base64,{image_data}',
            'dithered_image': f'data:image/png;base64,{dithered_image_base64}'
        }), 200

    except Exception as api_error:
        return flask.jsonify(format_error_response(api_error, 'API error')), 400


@app.route('/printImage', methods=['POST'])
def print_image() -> Tuple[flask.Response, int]:
    data = flask.request.json
    image_data = data.get('image_data', '')

    if not image_data:
        return flask.jsonify({'error': 'No image data provided for printing'}), 400

    try:
        # Decode the base64 image data
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))

        # Convert the image to instructions and send to printer
        instructions = printer_utils.convert_image_to_instructions(image)
        printer_utils.send_instructions(instructions)

        return flask.jsonify({'status': 'Image printed successfully'}), 200
    except Exception as print_error:
        return flask.jsonify(format_error_response(print_error, 'Print error')), 500

@app.route('/discoverPrinters', methods=['GET'])
def discover_printers() -> Tuple[flask.Response, int]:
    try:
        # Use the discover function from the helpers module
        available_devices = discover_printers_backend()
        logging.warn(available_devices)
        return flask.jsonify({'printers': available_devices}), 200
    except Exception as e:
        return flask.jsonify(format_error_response(e, 'Discovery error')), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5099, debug=True)
