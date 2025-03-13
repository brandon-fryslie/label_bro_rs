import base64
import io
from typing import Optional, Tuple, Union, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from PIL import Image

import cairo

from label_bro.utils import printer_utils


def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path, size)

def adjust_font_size(text: str, width: int, font: ImageFont.FreeTypeFont, padding: int) -> ImageFont.FreeTypeFont:
    for size in range(10, 300):
        font = font.font_variant(size=size)
        text_width = max(font.getbbox(word)[2] - font.getbbox(word)[0] for word in text.split())
        if text_width > width - 2 * padding:
            break
    return font

def create_full_width_label_image(text: str, width: int) -> Tuple[Optional[Image.Image], Optional[Exception]]:
    padding = 20
    vertical_padding = 20
    line_spacing = 40
    bottom_margin = 50  # Ensure sufficient bottom margin

    # Load the font
    try:
        font = load_font("Impact.ttf", 10)
    except IOError:
        error_message = "Font file not found."
        print(error_message)
        return None, IOError(error_message)

    # Dynamically adjust the font size to fit the width
    font = adjust_font_size(text, width, font, padding)

    # Calculate the total height
    total_height = sum(font.getbbox(word)[3] - font.getbbox(word)[1] + line_spacing for word in text.split()) + 2 * vertical_padding + bottom_margin

    # Create the image
    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)
    y = vertical_padding
    y = vertical_padding  # Start drawing text after the vertical padding

    # Draw the text
    for word in text.split():
        text_width, text_height = font.getbbox(word)[2] - font.getbbox(word)[0], font.getbbox(word)[3] - font.getbbox(word)[1]
        x = (width - text_width) / 2
        draw.text((x, y), word, font=font, fill="black")
        y += text_height + line_spacing

    return image, None


def create_small_label_image(text: str, width: int) -> Tuple[Optional[Image.Image], Optional[Exception]]:
    initial_font_size = 100
    left_padding = 10
    vertical_padding = 10
    min_font_size = 10
    bottom_margin = 50  # Ensure sufficient bottom margin

    # Load the font
    try:
        font = ImageFont.truetype("Impact.ttf", initial_font_size)
    except IOError:
        return None, IOError("Font file not found.")

    # Dynamically adjust the font size to fit the width
    font_size = initial_font_size
    text_height = font.getbbox(text)[3] - font.getbbox(text)[1]
    while True:
        text_width = font.getbbox(text)[2] - font.getbbox(text)[0]
        if text_width <= width - 2 * left_padding or font_size <= min_font_size:
            break
        font_size -= 1
        font = font.font_variant(size=font_size)

    # Calculate the total height
    total_height = text_height + 2 * vertical_padding + bottom_margin  # Add bottom margin

    # Create the image
    image = Image.new("RGB", (width, total_height), "white")
    draw = ImageDraw.Draw(image)
    y = vertical_padding  # Start drawing text after the vertical padding

    # Draw the text
    draw.text((left_padding, y), text, font=font, fill="black")

    return image, None




def process_label(text: str, width: int, label_type: str) -> Union[Exception, Dict[str, Any], None]:
    if label_type == 'full':
        image, error = create_full_width_label_image(text, width)
    else:
        image, error = create_small_label_image(text, width)

    if error:
        return error

    instructions = printer_utils.convert_image_to_instructions(image)
    return printer_utils.send_instructions(instructions)


def img_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f'data:image/png;base64,{img_str}'


def str_to_bool(s: str) -> bool:
    truthy = ['true', '1', 'yes', 'y', 'on']
    falsy = ['false', '0', 'no', 'n', 'off']
    lower_s = s.lower()
    if lower_s in truthy:
        return True
    if lower_s in falsy:
        return False

    raise ValueError(f"Invalid value {s}")
