import dataclasses
from typing import Optional, Dict, Any

import usb.core
from brother_ql.raster import BrotherQLRaster
import brother_ql.backends.helpers
import cairo
import io
from PIL import Image

import logging
import time

from brother_ql.reader import interpret_response


LABEL_SIZE = '62'

@dataclasses.dataclass
class PrinterInfo:
    identifier: str
    model_number: str
    label_size: str
    backend: str

def get_printer_info(printer_name: str = 'LabelBroWired') -> PrinterInfo:
    # TODO: fix this function to handle printer selection when implemented
    # Remove default value
    if printer_name == 'LabelBroWired':
        return PrinterInfo(
            identifier='usb://0x04f9:0x209b',
            model_number="QL-800",
            label_size="62",
            backend="usb",
        )
    elif printer_name == 'LabelBroWireless':
        return PrinterInfo(
            identifier="tcp://192.168.7.150:9100",
            model_number="QL-810W",
            label_size="62x100",
            backend="network",
        )
    else:
        raise ValueError(f'Unknown printer name: {printer_name}')

def check_printer_connection() -> bool:
    # TODO: fix this function to handle multiple printers
    if get_printer_info().backend == "usb":
        dev = usb.core.find(idVendor=0x04f9, idProduct=0x209b)
        return dev is not None
    else:
        # todo: add a check or something
        return True


def convert_image_to_instructions(image: Image.Image) -> Optional[bytes]:
    printer_info = get_printer_info()
    qlr = BrotherQLRaster(printer_info.model_number)
    qlr.exception_on_warning = True
    buffer = io.BytesIO()


    # Save the Pillow image to the buffer as a PNG file
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)

    # Determine if the image should be printed in black and white or with red
    label_type = determine_label_type(image)

    # Convert the image to instructions using the BrotherQLRaster object
    instructions = brother_ql.conversion.convert(
        qlr=qlr,
        images=[buffer],
        label=printer_info.label_size,
        threshold=70.0,
        dither=True,
        red=label_type == 'red'
    )

    return instructions

def apply_dithering(image: Image.Image) -> Image.Image:

    # Convert the image to grayscale
    grayscale_image = image.convert('L')

    # Apply Floyd-Steinberg dithering
    dithered_image = grayscale_image.convert('1', dither=Image.FLOYDSTEINBERG)

    return dithered_image

def determine_label_type(image: Image.Image) -> str:

    # Convert the image to RGB
    rgb_image = image.convert('RGB')

    # Analyze the image to decide if it should be printed with red
    red_threshold = 100  # Define a threshold for red detection
    red_pixels = 0
    total_pixels = rgb_image.width * rgb_image.height

    for pixel in rgb_image.getdata():
        r, g, b = pixel
        if r > red_threshold and g < red_threshold and b < red_threshold:
            red_pixels += 1

    # If a significant portion of the image contains red, use red label
    if red_pixels / total_pixels > 0.1:  # 10% of the image is red
        return 'red'
    else:
        return 'black_and_white'


def send_instructions(instructions: bytes) -> Dict[str, Any]:
    # TODO: fix this function to handle multiple printers
    return brother_ql.backends.helpers.send(instructions, get_printer_info().identifier)

