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

import pytest
from unittest.mock import MagicMock, patch
from AIVision import AIVision
from PIL import Image

@pytest.fixture
def aivison_library():
    return AIVision(api_key="test")

def test_verify_that(aivison_library):
    aivison_library.genai.generate_ai_response = MagicMock(return_value="response")
    aivison_library._assert_result = MagicMock()
    aivison_library.verify_that("path/to/image.png", "instructions")
    aivison_library.genai.generate_ai_response.assert_called_once_with(instructions="instructions", image_paths=["path/to/image.png"])
    aivison_library._assert_result.assert_called_once_with("response")

def test_verify_screenshot_matches_look_and_feel_template(aivison_library):
    aivison_library.genai.generate_ai_response = MagicMock(return_value="response")
    aivison_library._assert_result = MagicMock()
    with patch.object(aivison_library, 'combine_images_on_paths_side_by_side', return_value=None):
        aivison_library.verify_screenshot_matches_look_and_feel_template("path/to/screenshot.png", "path/to/template.png")
        aivison_library.genai.generate_ai_response.assert_called_once()
        aivison_library._assert_result.assert_called_once_with("response")

def test_open_image(aivison_library):
    with patch("PIL.Image.open", return_value=Image.new("RGB", (100, 100))):
        image = aivison_library.open_image("path/to/image.png")
        assert image.mode == "RGB"

def test_save_image(aivison_library):
    image = Image.new("RGB", (100, 100))
    with patch.object(image, 'save', return_value=None) as mock_save:
        with patch("robot.api.logger.info") as mock_logger_info:
            path = aivison_library.save_image(image, image_name="test_image.png")
            mock_save.assert_called_once()
            mock_logger_info.assert_called_once()
            assert path.endswith("test_image.png")

def test_generate_image_name(aivison_library):
    name = aivison_library.generate_image_name(prefix="Test", extension="jpg")
    assert name.startswith("Test")
    assert name.endswith(".jpg")

def test_combine_images_on_paths_side_by_side(aivison_library):
    with patch.object(aivison_library, 'open_image', return_value=Image.new("RGB", (100, 100))):
        with patch.object(aivison_library, 'combine_images_side_by_side', return_value=Image.new("RGB", (200, 100))):
            combined_image = aivison_library.combine_images_on_paths_side_by_side("path/to/image1.png", "path/to/image2.png", save=False)
            assert combined_image.size == (200, 100)

def test_add_watermark_to_image(aivison_library):
    image = Image.new("RGB", (100, 100))
    watermarked_image = aivison_library.add_watermark_to_image(image, "Test Watermark")
    assert watermarked_image.size == (100, 100)

