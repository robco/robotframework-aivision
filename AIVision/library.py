# MIT License
#
# Copyright (c) 2025 Róbert Malovec
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from .genai import GenAI
from .genai import Platforms
from PIL import Image, ImageDraw, ImageFont
from robot.api.deco import keyword
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError
from datetime import datetime
import os

"""
GenAI Testing library module for Robot Framework
"""


def _get_rf_output_dir():
    """Returns Robot Framework output directory path"""
    try:
        output_dir = BuiltIn().get_variable_value("${OUTPUT_DIR}")
    except RobotNotRunningError:
        output_dir = os.getcwd()

    return output_dir


class AIVision:
    """
    AI Vision Library module for Robot Framework

    This RF library provides GenAI enabled front-end, UI and visual templates testing capabilities

    """
    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    FONT = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "font", "Anton-Regular.ttf"
    )
    OUTPUT_DIR = _get_rf_output_dir()

    def __init__(self, base_url: str = None, api_key: str = None, platform: Platforms = Platforms.Ollama,
                 model: str = None, image_detail: str = None, simple_response: bool = True,
                 initialize: bool = True, system_prompt: str = None):

        self.genai = GenAI(base_url=base_url, api_key=api_key, platform=platform,
                           model=model, image_detail=image_detail,
                           simple_response=simple_response, initialize=initialize, system_prompt=system_prompt)
        self.OUTPUT_DIR = _get_rf_output_dir()

    @keyword
    def verify_that(self, screenshot_paths, instructions):
        """Verifies that the image matches the instructions

        Input parameters:

        ``image_path``: (required) Path(s) to the image. Can be a single path or a list of paths

        ``instructions``: (required) Instructions to be verified

        *Examples*:

        | Verify That | /path/to/image.png | Contains green logo in top right corner |

        | @{img_paths}  = | Create List | /path/to/image1.png | /path/to/image2.png |
        | Verify That | ${img_paths} | First image contains logo as referenced on 2nd image. |
        """
        screenshot_paths = [screenshot_paths] if isinstance(screenshot_paths, str) else screenshot_paths
        response = self.genai.generate_ai_response(instructions=f"Verify that: {instructions}", image_paths=screenshot_paths)
        logger.debug(response)

        self._assert_result(response)

    @keyword
    def verify_screenshot_matches_look_and_feel_template(self, screenshot_path, template_path,
                                                         override_instructions: str = None,
                                                         create_combined_image: bool = True):
        """Verifies that the screenshot matches the look and feel template

        Input parameters:

        ``screenshot_path``: (required) Path to the screenshot image

        ``template_path``: (required) Path to the template image

        ``override_instructions``: (optional) If specified, it will override the built-in assertion instructions

        ``create_combined_image``: (optional) default is _True_. If _True_, combined image will be created and saved

        _Return Value_ is the path of the saved image

        *Examples*:
        | Verify Screenshot Matches Look And Feel Template | /path/to/screenshot.png | /path/to/template.png |
        | Verify Screenshot Matches Look And Feel Template | /path/to/screenshot.png | /path/to/template.png | override_instructions=Custom instructions |
        """
        if create_combined_image:
            try:
                self.combine_images_on_paths_side_by_side(screenshot_path, template_path, "Actual", "Expected",
                                                          save=True)
            except Exception as e:
                logger.warn(f"Could not create combined image: {e}")

        instructions = """First image is showing actual application view.
Second image is reference design template. 
Verify screenshot matches look and feel template. Pay attention to details, design is important.
Make sure to check also all the visible logos, titles, labels, spelling, texts, links, menus, banners
and any available graphics. Always doublecheck the reference image in case you think some
text, label, logo or element is overlapping or containing typo.
"""
        if override_instructions:
            instructions = override_instructions
        response = self.genai.generate_ai_response(
            instructions=instructions,
            image_paths=[screenshot_path, template_path])

        self._assert_result(response)

    @staticmethod
    @keyword
    def open_image(image_path, mode="RGB"):
        """Opens image from provided path

        Input parameters:

        ``image_path``: (required) Path to the image

        ``mode``: (optional) default is _RGB_.
                  Defines type and depth of a pixel to which the opened image will be converted.
                  Supported modes can be seen
                  [https://pillow.readthedocs.io/en/3.0.x/handbook/concepts.html#modes|here].

        _Return value_ is the PIL Image object

        *Example*:
        | ${image} = | Open Image | /path/to/image.png |
        | ${image} = | Open Image | /path/to/image.png | RGBA |
        """

        try:
            image = Image.open(image_path)
            logger.debug(f"Image '{image_path}' was opened successfully")
        except Exception as err:
            raise AssertionError(
                f"Could not open image on provided path:\n{type(err).__name__}: {err}"
            )

        if image.mode != mode:
            logger.debug(
                f"Image is in mode '{image.mode}' but desired is '{mode}'. Starting conversion."
            )
            try:
                image = image.convert(mode=mode)
                logger.debug(f"Image successfully converted to mode '{mode}'")
            except Exception as err:
                raise AssertionError(
                    f"Could not convert image to provided mode:\n{type(err).__name__}: {err}"
                )

        return image

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    @keyword
    def save_image(
            self,
            image,
            image_name=None,
            image_format=None,
            watermark=None,
            image_path=None,
    ):
        """Saves image to provided path and name

        Input parameters:

        ``image``: (required) PIL image object to save

        ``image_name``: (optional) Name of the image.
                        If empty image name will be auto-generated

        ``image_format``: (optional) If not set the image format will be determined from the _image_name_ extension
                          if specified there

        ``watermark``: (optional) If the specified image will be watermarked with the specified string in top left corner

        ``image_path``: (optional) Path to image to save.
                        If not specified images are being stored to the Robot Framework output directory

        _Return Value_: Path of the saved image

        *Examples*:
        | Save Image | ${image}| my_image.png |
        | Save Image | ${image}| my_image | png |
        | Save Image | ${image}| my_image.png | watermark=My Label |
        | Save Image | ${image}| my_image.png | image_path=/path/to/my/image/directory |
        """
        if image_path is None:
            image_path = self.OUTPUT_DIR

        try:
            if not image_name:
                if image_format:
                    image_name = self.generate_image_name(extension=image_format)
                else:
                    image_name = self.generate_image_name()

            dest = os.path.join(image_path, image_name)

            if image_format:
                dest = os.path.join(dest, ".", image_format.lower())

            logger.debug(f"Image will be saved to '{dest}'")

            if watermark:
                logger.debug(f"Adding watermark '{watermark}' to image")
                image = self.add_watermark_to_image(image, watermark)

            image.save(dest)

        except Exception as err:
            raise AssertionError(f"Could not save image:\n{type(err).__name__}: {err}")

        logger.info(
            f"<img width='800' src='{os.path.relpath(dest, image_path)}'/>", html=True
        )

        return dest

    @staticmethod
    @keyword
    def generate_image_name(prefix="Snap", extension="png"):
        """Generates unique image name with the specified prefix and optional image extension

        Input parameters:

        ``prefix``: (optional) default is "Image"

        ``extension``: (optional) default is _png_

        _Return Value_ is generated string representing unique image name

        *Examples*:
        | ${img_name} = | Generate Image Name |
        | ${img_name} = | Generate Image Name | My-Image |
        | ${img_name} = | Generate Image Name | My-Image | jpg |
        """
        if not prefix:
            prefix = ""
            name_template = "%s%s"
        else:
            name_template = "%s-%s"

        image_name = name_template % (
            prefix,
            datetime.now().strftime("%m-%d-%Y_%H-%M-%S-%f")[:-3],
        )
        if extension:
            image_name = f"{image_name}.{extension.lower()}"

        logger.debug(f"Generated image name is: {image_name}")

        return image_name

    @keyword
    def combine_images_on_paths_side_by_side(self, image_path1, image_path2, watermark1=None, watermark2=None,
                                             mode="RGB", save=True):
        """Combines two images specified by file path to one big image side-by-side

        Input parameters:

        ``image_path1``: (required) Path to the first image

        ``image_path2``: (required) Path to the second image

        ``watermark1``: (optional) If specified image1 will be watermarked with the specified string in top left corner

        ``watermark2``: (optional) If specified image2 will be watermarked with the specified string in top left corner

        ``mode``: (optional) default is _RGB_.

        _Return Value_ is combined image as PIL Image format

        *Examples*:
        | ${image} = | Combine Images On Paths Side By Side | /path/to/image1.png | /path/to/image2.png |
        | ${image} = | Combine Images On Paths Side By Side | /path/to/image1.png | /path/to/image2.png | Expected | Actual |

        """
        img1 = self.open_image(image_path1, mode=mode)
        img2 = self.open_image(image_path2, mode=mode)

        combined_img = self.combine_images_side_by_side(img1, img2, watermark1=watermark1, watermark2=watermark2,
                                                        mode=mode)

        if save:
            self.save_image(combined_img)

        return combined_img

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    @keyword
    def combine_images_side_by_side(
            self, image1, image2, watermark1=None, watermark2=None, mode="RGB"
    ):
        """Combines two images to one big image side-by-side

        Input parameters:

        ``image1``: (required) Image one (PIL Image object) to combine

        ``image2``: (required) Image two (PIL Image object) to combine

        ``watermark1``: (optional) If specified image1 will be watermarked with the specified string in top left corner

        ``watermark2``: (optional) If specified image2 will be watermarked with the specified string in top left corner

        ``mode``: (optional) default is _RGB_.
                  Defines type and depth of a pixel which will be used for watermark layer.
                  You do not need typically change this value.
                  Supported modes can be seen
                  [https://pillow.readthedocs.io/en/3.0.x/handbook/concepts.html#modes|here].

        _Return Value_ is combined image as PIL Image format

        *Examples*:
        | ${image} = | Combine Images Side By Side | ${image1} | ${image2} |
        | ${image} = | Combine Images Side By Side | ${image1} | ${image2} |RGBA |
        """
        try:
            # Create empty image for both images to fit
            combined_image = Image.new(
                mode,
                (
                    image1.size[0] + image2.size[0] + 1,
                    max(image1.size[1], image2.size[1]),
                ),
            )

            if watermark1:
                logger.debug(f"Adding watermark '{watermark1}' to image1")
                image1 = self.add_watermark_to_image(image1, watermark1)

            if watermark2:
                logger.debug(f"Adding watermark '{watermark2}' to image2")
                image2 = self.add_watermark_to_image(image2, watermark2)

            # Concatenate both images to one big image
            combined_image.paste(image1, (0, 0))
            combined_image.paste(image2, (image1.size[0] + 1, 0))

        except Exception as err:
            raise AssertionError(
                f"Could not create combined image:\n{type(err).__name__}: {err}"
            )

        return combined_image

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    @keyword
    def add_watermark_to_image(
            self, image, text, color="red", text_size=50, text_position=(0, 0), mode="RGB"
    ):
        """Adds watermark text to the image

        Input parameters:

        ``image``: (required) PIL image object to add watermark to

        ``text``: (required) Text string which will be added to the image

        ``color``: (optional) default is _red_.
                   Text color of the watermark

        ``text_size``: (optional) default is _50_.
                       Text size of the watermark

        ``text_position``: (optional) default is _(0, 0)_.
                           Represents X,Y coordinates in the image where to add watermark

        ``mode``: (optional) default is _RGB_.
                  Defines type and depth of a pixel which will be used for watermark layer.
                  You do not need typically change this value.
                  Supported modes can be seen
                  [https://pillow.readthedocs.io/en/3.0.x/handbook/concepts.html#modes|here].

        _Return Value_ represents PIL Image object

        *Examples*:
        | ${w_image} = | Add Watermark To Image | ${image} | Original |
        | ${w_image} = | Add Watermark To Image | ${image} | Original | blue |
        | ${w_image} = | Add Watermark To Image | ${image} | text=Original | color=blue |
        """
        font_path = self.FONT

        try:
            font = ImageFont.truetype(font_path, text_size)
        except Exception as err:
            raise AssertionError(
                f"Could not set watermark font:\n{type(err).__name__}: {err}"
            )

        try:
            # Create watermark drawing canvas object
            watermark = Image.new(mode, image.size)
            draw = ImageDraw.ImageDraw(watermark, mode)

            # Create semi-transparent watermark text
            draw.text(text_position, text, fill=color, font=font)
            mask = watermark.convert("L").point(lambda x: min(x, 100))
            watermark.putalpha(mask)

            # Create new image with watermark
            w_image = image.copy()
            w_image.paste(watermark, None, watermark)
        except Exception as err:
            raise AssertionError(
                f"Could not create watermark:\n{type(err).__name__}: {err}"
            )

        return w_image

    def _assert_result(self, response):
        result, explanation = self.genai.extract_result_and_explanation_from_response(response)
        if result and result.lower() == "pass":
            logger.info(f"Verification passed:\n{explanation}")
        else:
            raise AssertionError(f"Verification failed:\n{explanation}")
