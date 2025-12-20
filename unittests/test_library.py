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

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from robot.api.deco import keyword
from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

# Import the class under test - adjust the import path as needed
from AIVision import AIVision


class TestAIVision:

    @pytest.fixture
    def mock_genai(self):
        """Fixture to create a mock GenAI instance"""
        with patch('AIVision.genai.GenAI') as mock_genai_class:
            mock_genai_instance = mock_genai_class.return_value
            mock_genai_instance.generate_ai_response.return_value = "AI Response"
            mock_genai_instance.extract_result_and_explanation_from_response.return_value = ("pass", "Test passed")
            yield mock_genai_instance

    @pytest.fixture
    def library(self, mock_genai):
        """Fixture to create a AIVision instance with mocked dependencies"""
        with patch('AIVision.library._get_rf_output_dir', return_value='/mock/output/dir'):
            lib = AIVision(api_key="test")
            yield lib

    @pytest.fixture
    def mock_image(self):
        """Fixture to create a mock PIL Image"""
        mock_img = MagicMock(spec=Image.Image)
        mock_img.size = (100, 100)
        mock_img.mode = "RGB"
        mock_img.copy.return_value = mock_img
        mock_img.convert.return_value = mock_img
        return mock_img

    @pytest.fixture
    def mock_logger(self):
        """Fixture to mock robot.api.logger"""
        with patch('AIVision.library.logger') as mock_logger:
            yield mock_logger

    def test_init(self, mock_genai):
        """Test the initialization of AIVision"""
        with patch('AIVision.library._get_rf_output_dir', return_value='/mock/output/dir'):
            lib = AIVision(
                api_key="test_key",
                base_url="http://test.com",
                model="test_model",
                image_detail="high",
                simple_response=True,
                initialize=True
            )

            # Verify GenAI was initialized with the correct parameters
            from AIVision.genai import GenAI
            GenAI.assert_called_once_with(
                base_url="http://test.com",
                api_key="test_key",
                model="test_model",
                image_detail="high",
                simple_response=True,
                initialize=True
            )

    def test_verify_that_single_path(self, library, mock_genai, mock_logger):
        """Test verify_that method with a single screenshot path"""
        AIVision.verify_that("/path/to/image.png", "Contains green logo in top right corner")

        mock_genai.generate_ai_response.assert_called_once_with(
            instructions="Contains green logo in top right corner",
            image_paths=["/path/to/image.png"]
        )
        mock_logger.debug.assert_called_once_with("AI Response")
        mock_genai.extract_result_and_explanation_from_response.assert_called_once_with("AI Response")
        mock_logger.info.assert_called_once_with("Verification passed:\nTest passed", html=False)

    def test_verify_that_multiple_paths(self, library, mock_genai, mock_logger):
        """Test verify_that method with multiple screenshot paths"""
        image_paths = ["/path/to/image1.png", "/path/to/image2.png"]
        AIVision.verify_that(image_paths, "Compare these images")

        mock_genai.generate_ai_response.assert_called_once_with(
            instructions="Compare these images",
            image_paths=image_paths
        )

    def test_verify_that_fail(self, library, mock_genai, mock_logger):
        """Test verify_that method when verification fails"""
        mock_genai.extract_result_and_explanation_from_response.return_value = ("FAIL", "Test failed")

        with pytest.raises(AssertionError) as exc:
            AIVision.verify_that("/path/to/image.png", "Contains green logo in top right corner")

        assert str(exc.value) == "Verification failed:\nTest failed"

    def test_verify_screenshot_matches_look_and_feel_template(self, library, mock_genai, mock_logger):
        """Test verify_screenshot_matches_look_and_feel_template method"""
        with patch.object(library, 'combine_images_on_paths_side_by_side') as mock_combine:
            AIVision.verify_screenshot_matches_look_and_feel_template(
                "/path/to/screenshot.png",
                "/path/to/template.png"
            )

            mock_combine.assert_called_once_with(
                "/path/to/screenshot.png",
                "/path/to/template.png",
                "Actual",
                "Expected",
                save=True
            )

            mock_genai.generate_ai_response.assert_called_once()
            assert "First image is showing actual application view" in mock_genai.generate_ai_response.call_args[1][
                'instructions']
            assert mock_genai.generate_ai_response.call_args[1]['image_paths'] == ["/path/to/screenshot.png",
                                                                                   "/path/to/template.png"]

    def test_verify_screenshot_matches_look_and_feel_template_with_override(self, library, mock_genai):
        """Test verify_screenshot_matches_look_and_feel_template method with override instructions"""
        with patch.object(library, 'combine_images_on_paths_side_by_side'):
            AIVision.verify_screenshot_matches_look_and_feel_template(
                "/path/to/screenshot.png",
                "/path/to/template.png",
                override_instructions="Custom instructions"
            )

            mock_genai.generate_ai_response.assert_called_once_with(
                instructions="Custom instructions",
                image_paths=["/path/to/screenshot.png", "/path/to/template.png"]
            )

    def test_verify_screenshot_matches_look_and_feel_template_no_combine(self, library, mock_genai):
        """Test verify_screenshot_matches_look_and_feel_template method without combining images"""
        AIVision.verify_screenshot_matches_look_and_feel_template(
            "/path/to/screenshot.png",
            "/path/to/template.png",
            create_combined_image=False
        )

        mock_genai.generate_ai_response.assert_called_once()

    def test_verify_screenshot_matches_look_and_feel_template_combine_exception(self, library, mock_genai, mock_logger):
        """Test verify_screenshot_matches_look_and_feel_template method with exception during combine"""
        with patch.object(library, 'combine_images_on_paths_side_by_side', side_effect=Exception("Combine error")):
            AIVision.verify_screenshot_matches_look_and_feel_template(
                "/path/to/screenshot.png",
                "/path/to/template.png"
            )

            mock_logger.warn.assert_called_once()
            assert "Could not create combined image: Combine error" in mock_logger.warn.call_args[0][0]
            mock_genai.generate_ai_response.assert_called_once()

    def test_open_image_success(self, mock_logger):
        """Test open_image method with successful image opening"""
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "RGB"

        with patch('AIVision.library.Image.open', return_value=mock_img) as mock_open_image:
            result = AIVision.open_image("/path/to/image.png")

            mock_open_image.assert_called_once_with("/path/to/image.png")
            assert result == mock_img
            mock_logger.debug.assert_called_once_with("Image '/path/to/image.png' was opened successfully")

    def test_open_image_with_conversion(self, mock_logger):
        """Test open_image method with mode conversion"""
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "RGB"
        converted_img = MagicMock(spec=Image.Image)
        mock_img.convert.return_value = converted_img

        with patch('AIVision.library.Image.open', return_value=mock_img) as mock_open_image:
            result = AIVision.open_image("/path/to/image.png", mode="RGBA")

            mock_open_image.assert_called_once_with("/path/to/image.png")
            mock_img.convert.assert_called_once_with(mode="RGBA")
            assert result == converted_img
            assert mock_logger.debug.call_count == 2

    def test_open_image_failure(self):
        """Test open_image method with failure to open image"""
        with patch('AIVision.Image.open', side_effect=Exception("Open error")):
            with pytest.raises(AssertionError) as exc:
                AIVision.open_image("/path/to/image.png")

            assert "Could not open image on provided path" in str(exc.value)
            assert "Open error" in str(exc.value)

    def test_open_image_conversion_failure(self, mock_logger):
        """Test open_image method with failure during conversion"""
        mock_img = MagicMock(spec=Image.Image)
        mock_img.mode = "RGB"
        mock_img.convert.side_effect = Exception("Convert error")

        with patch('AIVision.library.Image.open', return_value=mock_img):
            with pytest.raises(AssertionError) as exc:
                AIVision.open_image("/path/to/image.png", mode="RGBA")

            assert "Could not convert image to provided mode" in str(exc.value)
            assert "Convert error" in str(exc.value)

    def test_save_image_with_name(self, library, mock_image, mock_logger):
        """Test save_image method with specified image name"""
        with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
            result = AIVision.save_image(mock_image, "test_image.png")

            assert result == "/mock/output/dir/test_image.png"
            mock_image.save.assert_called_once_with("/mock/output/dir/test_image.png")
            mock_logger.info.assert_called_once()

    def test_save_image_with_format(self, library, mock_image):
        """Test save_image method with specified format"""
        with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
            AIVision.save_image(mock_image, "test_image", "jpg")

            mock_image.save.assert_called_once()

    def test_save_image_generated_name(self, library, mock_image):
        """Test save_image method with generated name"""
        with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
            with patch.object(library, 'generate_image_name', return_value="generated.png"):
                result = AIVision.save_image(mock_image)

                assert result == "/mock/output/dir/generated.png"
                mock_image.save.assert_called_once_with("/mock/output/dir/generated.png")

    def test_save_image_with_watermark(self, library, mock_image):
        """Test save_image method with watermark"""
        with patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
            with patch.object(library, 'add_watermark_to_image', return_value=mock_image) as mock_add_watermark:
                AIVision.save_image(mock_image, "test_image.png", watermark="Test Watermark")

                mock_add_watermark.assert_called_once_with(mock_image, "Test Watermark")
                mock_image.save.assert_called_once_with("/mock/output/dir/test_image.png")

    def test_save_image_failure(self, library, mock_image):
        """Test save_image method with failure to save"""
        mock_image.save.side_effect = Exception("Save error")

        with pytest.raises(AssertionError) as exc:
            AIVision.save_image(mock_image, "test_image.png")

        assert "Could not save image" in str(exc.value)
        assert "Save error" in str(exc.value)

    def test_generate_image_name_default(self, mock_logger):
        """Test generate_image_name method with default parameters"""
        with patch('AIVision.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "03-11-2025_10-30-45-123"
            result = AIVision.generate_image_name()

            assert result == "Snap-03-11-2025_10-30-45-123.png"
            mock_logger.debug.assert_called_once_with(f"Generated image name is: {result}")

    def test_generate_image_name_custom(self, mock_logger):
        """Test generate_image_name method with custom parameters"""
        with patch('AIVision.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "03-11-2025_10-30-45-123"
            result = AIVision.generate_image_name(prefix="Custom", extension="jpg")

            assert result == "Custom-03-11-2025_10-30-45-123.jpg"

    def test_generate_image_name_no_prefix(self, mock_logger):
        """Test generate_image_name method with no prefix"""
        with patch('AIVision.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "03-11-2025_10-30-45-123"
            result = AIVision.generate_image_name(prefix="", extension="png")

            assert result == "03-11-2025_10-30-45-123.png"

    def test_combine_images_on_paths_side_by_side(self, library, mock_image, mock_logger):
        """Test combine_images_on_paths_side_by_side method"""
        with patch.object(library, 'open_image', return_value=mock_image) as mock_open:
            with patch.object(library, 'combine_images_side_by_side', return_value=mock_image) as mock_combine:
                with patch.object(library, 'save_image') as mock_save:
                    AIVision.combine_images_on_paths_side_by_side(
                        "/path/to/image1.png",
                        "/path/to/image2.png",
                        "Watermark1",
                        "Watermark2"
                    )

                    mock_open.assert_any_call("/path/to/image1.png", mode="RGB")
                    mock_open.assert_any_call("/path/to/image2.png", mode="RGB")
                    mock_combine.assert_called_once_with(
                        mock_image,
                        mock_image,
                        watermark1="Watermark1",
                        watermark2="Watermark2",
                        mode="RGB"
                    )
                    mock_save.assert_called_once_with(mock_image)

    def test_combine_images_on_paths_side_by_side_no_save(self, library, mock_image):
        """Test combine_images_on_paths_side_by_side method without saving"""
        with patch.object(library, 'open_image', return_value=mock_image):
            with patch.object(library, 'combine_images_side_by_side', return_value=mock_image) as mock_combine:
                with patch.object(library, 'save_image') as mock_save:
                    result = AIVision.combine_images_on_paths_side_by_side(
                        "/path/to/image1.png",
                        "/path/to/image2.png",
                        save=False
                    )

                    mock_combine.assert_called_once()
                    mock_save.assert_not_called()

    def test_combine_images_side_by_side(self, library, mock_image):
        """Test combine_images_side_by_side method"""
        with patch('AIVision.Image.new', return_value=mock_image) as mock_new_image:
            with patch.object(library, 'add_watermark_to_image', return_value=mock_image) as mock_add_watermark:
                result = AIVision.combine_images_side_by_side(
                    mock_image,
                    mock_image,
                    watermark1="Watermark1",
                    watermark2="Watermark2"
                )

                mock_new_image.assert_called_once_with("RGB", (201, 100))
                mock_add_watermark.assert_any_call(mock_image, "Watermark1")
                mock_add_watermark.assert_any_call(mock_image, "Watermark2")
                assert mock_add_watermark.call_count == 2
                mock_image.paste.assert_any_call(mock_image, (0, 0))
                mock_image.paste.assert_any_call(mock_image, (101, 0))
                assert result == mock_image

    def test_combine_images_side_by_side_no_watermarks(self, library, mock_image):
        """Test combine_images_side_by_side method without watermarks"""
        with patch('AIVision.Image.new', return_value=mock_image) as mock_new_image:
            with patch.object(library, 'add_watermark_to_image') as mock_add_watermark:
                result = AIVision.combine_images_side_by_side(mock_image, mock_image)

                mock_new_image.assert_called_once()
                mock_add_watermark.assert_not_called()
                assert mock_image.paste.call_count == 2
                assert result == mock_image

    def test_combine_images_side_by_side_failure(self, library, mock_image):
        """Test combine_images_side_by_side method with failure"""
        with patch('AIVision.Image.new', side_effect=Exception("Combine error")):
            with pytest.raises(AssertionError) as exc:
                AIVision.combine_images_side_by_side(mock_image, mock_image)

            assert "Could not create combined image" in str(exc.value)
            assert "Combine error" in str(exc.value)

    def test_add_watermark_to_image(self, library, mock_image, mock_logger):
        """Test add_watermark_to_image method"""
        mock_font = MagicMock()
        mock_draw = MagicMock()
        mock_mask = MagicMock()

        with patch('AIVision.ImageFont.truetype', return_value=mock_font) as mock_truetype:
            with patch('AIVision.Image.new', return_value=mock_image) as mock_new_image:
                with patch('AIVision.ImageDraw.ImageDraw', return_value=mock_draw) as mock_imagedraw:
                    mock_image.convert.return_value.point.return_value = mock_mask

                    result = AIVision.add_watermark_to_image(mock_image, "Watermark", "blue", 40, (10, 10))

                    mock_truetype.assert_called_once_with(AIVision.FONT, 40)
                    mock_new_image.assert_called_once_with("RGB", (100, 100))
                    mock_imagedraw.assert_called_once_with(mock_image, "RGB")
                    mock_draw.text.assert_called_once_with((10, 10), "Watermark", fill="blue", font=mock_font)
                    mock_image.convert.assert_called_once_with("L")
                    mock_image.convert.return_value.point.assert_called_once()
                    mock_image.putalpha.assert_called_once_with(mock_mask)
                    mock_image.copy.assert_called_once()
                    mock_image.paste.assert_called_once_with(mock_image, None, mock_image)
                    assert result == mock_image

    def test_add_watermark_to_image_font_error(self, library, mock_image):
        """Test add_watermark_to_image method with font error"""
        with patch('AIVision.ImageFont.truetype', side_effect=Exception("Font error")):
            with pytest.raises(AssertionError) as exc:
                AIVision.add_watermark_to_image(mock_image, "Watermark")

            assert "Could not set watermark font" in str(exc.value)
            assert "Font error" in str(exc.value)

    def test_add_watermark_to_image_creation_error(self, library, mock_image):
        """Test add_watermark_to_image method with watermark creation error"""
        with patch('AIVision.ImageFont.truetype', return_value=MagicMock()):
            with patch('AIVision.Image.new', side_effect=Exception("Watermark error")):
                with pytest.raises(AssertionError) as exc:
                    AIVision.add_watermark_to_image(mock_image, "Watermark")

                assert "Could not create watermark" in str(exc.value)
                assert "Watermark error" in str(exc.value)

    def test_assert_result_pass(self, library, mock_genai, mock_logger):
        """Test _assert_result method with passing result"""
        mock_genai.extract_result_and_explanation_from_response.return_value = ("pass", "Test passed successfully")

        AIVision._assert_result("AI Response")

        mock_genai.extract_result_and_explanation_from_response.assert_called_once_with("AI Response")
        mock_logger.info.assert_called_once_with("Verification passed:\nTest passed successfully")

    def test_assert_result_fail(self, library, mock_genai):
        """Test _assert_result method with failing result"""
        mock_genai.extract_result_and_explanation_from_response.return_value = ("fail", "Test failed")

        with pytest.raises(AssertionError) as exc:
            AIVision._assert_result("AI Response")

        mock_genai.extract_result_and_explanation_from_response.assert_called_once_with("AI Response")
        assert str(exc.value) == "Verification failed:\nTest failed"

    def test_assert_result_none(self, library, mock_genai):
        """Test _assert_result method with None result"""
        mock_genai.extract_result_and_explanation_from_response.return_value = (None, "No result")

        with pytest.raises(AssertionError) as exc:
            AIVision._assert_result("AI Response")

        assert str(exc.value) == "Verification failed:\nNo result"

    def test_get_rf_output_dir_running(self):
        """Test _get_rf_output_dir function when Robot Framework is running"""
        with patch('AIVision.BuiltIn') as mock_builtin:
            mock_builtin.return_value.get_variable_value.return_value = "/robot/output"

            from library import _get_rf_output_dir
            result = _get_rf_output_dir()

            assert result == "/robot/output"
            mock_builtin.return_value.get_variable_value.assert_called_once_with("${OUTPUT_DIR}")

    def test_get_rf_output_dir_not_running(self):
        """Test _get_rf_output_dir function when Robot Framework is not running"""
        with patch('AIVision.BuiltIn') as mock_builtin:
            mock_builtin.return_value.get_variable_value.side_effect = RobotNotRunningError("Not running")
            with patch('AIVision.os.getcwd', return_value="/current/dir"):
                from library import _get_rf_output_dir
                result = _get_rf_output_dir()

                assert result == "/current/dir"
