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
from AILibrary import AILibrary
from PIL import Image

@pytest.fixture
def genai_ai_library():
    return AILibrary(api_key="test")

def test_verify_that(genai_ai_library):
    genai_ai_library.genai.generate_ai_response = MagicMock(return_value="response")
    genai_ai_library._assert_result = MagicMock()
    genai_ai_library.verify_that("path/to/image.png", "instructions")
    genai_ai_library.genai.generate_ai_response.assert_called_once_with(instructions="instructions", image_paths=["path/to/image.png"])
    genai_ai_library._assert_result.assert_called_once_with("response")

def test_verify_screenshot_matches_look_and_feel_template(genai_ai_library):
    genai_ai_library.genai.generate_ai_response = MagicMock(return_value="response")
    genai_ai_library._assert_result = MagicMock()
    with patch.object(genai_ai_library, 'combine_images_on_paths_side_by_side', return_value=None):
        genai_ai_library.verify_screenshot_matches_look_and_feel_template("path/to/screenshot.png", "path/to/template.png")
        genai_ai_library.genai.generate_ai_response.assert_called_once()
        genai_ai_library._assert_result.assert_called_once_with("response")

def test_open_image(genai_ai_library):
    with patch("PIL.Image.open", return_value=Image.new("RGB", (100, 100))):
        image = genai_ai_library.open_image("path/to/image.png")
        assert image.mode == "RGB"

def test_save_image(genai_ai_library):
    image = Image.new("RGB", (100, 100))
    with patch.object(image, 'save', return_value=None) as mock_save:
        with patch("robot.api.logger.info") as mock_logger_info:
            path = genai_ai_library.save_image(image, image_name="test_image.png")
            mock_save.assert_called_once()
            mock_logger_info.assert_called_once()
            assert path.endswith("test_image.png")

def test_generate_image_name(genai_ai_library):
    name = genai_ai_library.generate_image_name(prefix="Test", extension="jpg")
    assert name.startswith("Test")
    assert name.endswith(".jpg")

def test_combine_images_on_paths_side_by_side(genai_ai_library):
    with patch.object(genai_ai_library, 'open_image', return_value=Image.new("RGB", (100, 100))):
        with patch.object(genai_ai_library, 'combine_images_side_by_side', return_value=Image.new("RGB", (200, 100))):
            combined_image = genai_ai_library.combine_images_on_paths_side_by_side("path/to/image1.png", "path/to/image2.png", save=False)
            assert combined_image.size == (200, 100)

def test_add_watermark_to_image(genai_ai_library):
    image = Image.new("RGB", (100, 100))
    watermarked_image = genai_ai_library.add_watermark_to_image(image, "Test Watermark")
    assert watermarked_image.size == (100, 100)

