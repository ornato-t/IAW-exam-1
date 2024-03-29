from PIL import Image, ImageOps
import uuid
import os

class ImageException(Exception):
    """
    Raised by errors during the image editing and saving procedures

    :param file: name of the file causing the error
    """
    def __init__(self, file):
        self.file = file
        super().__init__()

# Desired file sizes for a 16:9 aspect ratio
WIDTH = 1280
HEIGHT = 720

def save_image(image_form):
    try:
        img = Image.open(image_form)

        # Calculate aspect ratio, scale the image accordingly
        original_aspect_ratio = img.width / float(img.height)
        new_aspect_ratio = WIDTH / float(HEIGHT)

        if original_aspect_ratio > new_aspect_ratio:    # Wider than desired aspect ratio
            new_width = WIDTH
            new_height = int(round(new_width / original_aspect_ratio))
        else:                                           # Taller than desired aspect ratio
            new_height = HEIGHT
            new_width = int(round(new_height * original_aspect_ratio))

        new_img = Image.new('RGB', (WIDTH, HEIGHT), (255, 255, 255))

        # Center the original image on the new one. Resize the original image and paste it
        position = ((WIDTH - new_width) //   2, (HEIGHT - new_height) //   2)
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        new_img.paste(resized_img, position)

        # Save a new image with the same extension as the original and a UUID for its name
        file_extension = image_form.filename.split('.')[-1]
        new_filename = f'{uuid.uuid4()}.{file_extension}'
        new_img.save(f'static/images/{new_filename}')

        return new_filename
    except Exception as e:
        print("ERROR", e)
        raise ImageException(image_form.filename)

def delete_images(path_list):
    for image_path in path_list:
        try:
            full_path = f'static/images/{image_path}'
            if os.path.isfile(full_path):
                os.remove(full_path)
            else:
                print(f"File not found: {full_path}")
        except Exception as e:
            print('ERROR', str(e))
