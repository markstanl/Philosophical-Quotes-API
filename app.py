from flask import Flask, send_file, request
from PIL import Image, ImageDraw, ImageFont
from textwrap import wrap
import random
import io
from data.quotes import quotes_original
from data.themes import themes
from methods import (filter_by_author, filter_to_daily_quote, get_specific_quote, get_quote_by_index, check_error,
                     filter_by_excluded_ids)

app = Flask(__name__)


@app.route('/generate_image', methods=['GET'])
def generate_image():
    """
    Generates an image with a random quote and author

    Args:
        author (str): an author used to filter the quotes theme
        theme (str): a theme used to select the background image
        daily_quote (bool): a boolean used to get a quote based on the current day, instead of randomly generated each
                            time

    Returns:
        image: a generated image with a quote and author

    Raises:
        404: If no quotes are found for the given author
    """

    quotes = quotes_original  # makes a mutable copy of the original quote list

    inputted_author = request.args.get('author', default=None, type=str)
    inputted_theme = request.args.get('theme', default=None, type=str)
    daily_quote = request.args.get('daily_quote', default=None, type=bool)
    specific_quote = request.args.get('quote', default=None, type=str)
    specific_quote_index = request.args.get('quote_index', default=None, type=int)
    exclude_indexes = request.args.get('exclude_indexes', default=None, type=str)

    error = check_error(author=inputted_author, theme=inputted_theme, daily=daily_quote, specific_quote=specific_quote,
                        specific_quote_index=specific_quote_index, exclude_indexes=exclude_indexes, quotes=quotes)
    if error:
        return error

    quotes = filter_by_author(quotes, inputted_author)
    quotes = filter_by_excluded_ids(quotes, exclude_indexes) if exclude_indexes else quotes
    quotes = filter_to_daily_quote(quotes) if daily_quote else quotes
    quotes = get_specific_quote(quotes, specific_quote) if specific_quote else quotes
    quotes = get_quote_by_index(quotes, specific_quote_index) if specific_quote_index else quotes

    quote, author, quote_id = random.choice(quotes)

    theme = themes.get(inputted_theme, themes["default"])
    image_path = theme[0]

    # Load background image
    background_image = Image.open(image_path)

    # Create drawing context
    draw = ImageDraw.Draw(background_image)

    # Define font and size
    quote_font_path = "assets/Philosopher-Italic.ttf"
    author_font_path = "assets/Rambla-Italic.ttf"

    if len(quote) < 100:  # Adjust font size based on quote length
        quote_font_size = 30
        wrapped_quote = wrap(quote, width=25)
    elif len(quote) < 160:
        quote_font_size = 25
        wrapped_quote = wrap(quote, width=25)
    elif len(quote) < 200:
        quote_font_size = 20
        wrapped_quote = wrap(quote, width=30)
    else:
        quote_font_size = 15
        wrapped_quote = wrap(quote, width=40)
    quote_font = ImageFont.truetype(quote_font_path, size=quote_font_size)

    size = 30
    author = f'- {author}'  # Add a dash before the author's name as it will be displayed on the imageq
    if len(author) < 8:  # adjust the x distance based on the length of the author's name
        x_distance = 220
    elif len(author) < 12:
        x_distance = 190
    elif len(author) < 15:
        x_distance = 150
    elif len(author) < 19:
        x_distance = 100
    elif len(author) < 22:
        x_distance = 80
    else:
        x_distance = 80
        size = 25
    author_font = ImageFont.truetype(author_font_path, size=size)

    # Calculate the height of the text box
    text_height = sum(
        draw.textbbox((0, 0), line, font=quote_font)[3] - draw.textbbox((0, 0), line, font=quote_font)[1] for line in
        wrapped_quote)

    # define and redefine the initial y position
    move_up_by = 50
    quote_y = ((background_image.height - text_height) // 2) - move_up_by

    text_color = theme[1]  # author text color
    draw.text((x_distance, 175), author, fill=text_color, font=author_font)  # Draw the author's name on the image
    text_color = theme[2]  # quote text color

    for line in wrapped_quote:  # Draw the quote on the image
        x = (background_image.width - draw.textbbox((0, 0), line, font=quote_font)[2]) // 2
        draw.text((x, quote_y), line, fill=text_color, font=quote_font)
        quote_y += draw.textbbox((0, 0), line, font=quote_font)[3] - draw.textbbox((0, 0), line, font=quote_font)[1]

    img_io = io.BytesIO()
    background_image.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)

    # Send the image data in the response
    return send_file(img_io, mimetype='image/jpeg')


if __name__ == "__main__":
    app.run(host='0.0.0.0')