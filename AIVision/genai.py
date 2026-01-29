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

from .platforms import Platforms
from openai import OpenAI
import os
import base64


class AIPlatform:
    """Configuration class for AI platform settings."""
    DEFAULT_IMG_DETAIL = "high"

    def __init__(self, platform: Platforms = None, base_url: str = None,
                 api_key: str = None, model: str = None, image_detail: str = DEFAULT_IMG_DETAIL):
        """
        Initialize AI platform configuration.

        Args:
            platform: Platform enum value
            base_url: Custom base URL (overrides platform default)
            api_key: API key for authentication
            model: Model name (overrides platform default)
            image_detail: Image detail level for vision models
        """
        self.platform = platform
        self.base_url = base_url or (platform.value["default_base_url"] if platform else None)
        self.model = model or (platform.value["default_model"] if platform else None)
        self.detail = image_detail
        self.api_key = api_key
        self.supports_vision = platform.value.get("supports_vision", False) if platform else False

        # Validate API key requirement
        if platform and platform.value.get("api_key_required", False) and not api_key:
            raise ValueError(f"{platform.name} requires an API key")


class GenAI:
    """
    GenAI class for interacting with multiple AI platforms using OpenAI-compatible API.
    Supports Ollama, Perplexity, and is easily extensible for other providers.
    """

    AUTOMATOR_INSTRUCTION = """
You are a response system for Robot Framework, specialized in test automation. 
Your task is to evaluate an input instruction (assertion) against one or more provided images. 
You must verify whether the assertion holds true based on the visual content of the images.
Make sure you observe images in every detail - all the logos, texts, titles, buttons, elements, inputs.

Your response must be strictly formatted like this:

RESULT: // PASS if assertion is verified, FAIL if not
EXPLANATION: 
<brief explanation if TRUE, detailed explanation if FALSE>


When the assertion is TRUE:
Confirm the assertion and provide a brief explanation of why it was verified successfully.

When the assertion is FALSE:
Explain in detail what was wrong and why the assertion could not be verified.

Highlight any visual discrepancies, missing elements, or mismatches.

Example Inputs and Outputs:

Input Instruction: "The login button is visible and labeled 'Sign In'"
Provided Image: [screenshot of a login form]

Response when TRUE:

RESULT: pass
EXPLANATION: 
1. The login button is clearly visible
2. The login button is labeled 'Sign In' as expected.


Response when FALSE:

RESULT: fail
EXPLANATION:
1. The login button is either not visible or not labeled 'Sign In'.
2. The visible button is labeled 'Log In' instead.


Ensure no other text is provided in the response.
    """

    def __init__(self, platform: Platforms = Platforms.Ollama, base_url: str = None,
                 api_key: str = None, model: str = None, image_detail: str = None,
                 simple_response: bool = True, initialize: bool = True,
                 system_prompt: str = AUTOMATOR_INSTRUCTION):
        """
        Initialize GenAI instance.

        Args:
            platform: AI platform to use (default: Ollama)
            base_url: Custom base URL for API endpoint
            api_key: API key for authentication
            model: Model name to use
            image_detail: Detail level for image processing
            simple_response: Return simplified responses
            initialize: Initialize client immediately
            system_prompt: Main AI System prompt specifying Gen AI behavior
        """
        self.client = None
        self.simple_response = simple_response
        self.system_prompt = system_prompt or self.AUTOMATOR_INSTRUCTION

        # Set default API key for platforms that don't require real keys
        if platform == Platforms.Ollama and not api_key:
            api_key = "ollama"  # Required by OpenAI client but ignored by Ollama

        self.ai_platform = AIPlatform(
            platform=platform,
            base_url=base_url,
            api_key=api_key,
            model=model,
            image_detail=image_detail
        )

        if initialize:
            self.initialize_genai(ai_platform=self.ai_platform)

    def initialize_genai(self, ai_platform: AIPlatform = None):
        """
        Initialize the OpenAI client with platform-specific configuration.

        Args:
            ai_platform: AIPlatform configuration object
        """
        if not ai_platform:
            raise ValueError("AI platform not specified")

        if not ai_platform.base_url:
            raise ValueError("Base URL is required")

        # Initialize OpenAI client with platform-specific settings
        self.client = OpenAI(
            base_url=ai_platform.base_url,
            api_key=ai_platform.api_key or "default"
        )

        self.ai_platform = ai_platform

    def generate_ai_response(self, instructions: str, image_paths: list):
        """
        Generate AI response for test automation assertions with images.

        Args:
            instructions: Test assertion instructions
            image_paths: List of image file paths to analyze

        Returns:
            AI-generated response
        """
        prompt = self._prepare_prompt(instructions, image_paths)
        return self.chat_completion(prompt)

    def chat_completion(self, messages):
        """
        Execute chat completion request.

        Args:
            messages: List of message dictionaries in OpenAI format

        Returns:
            Response content (simplified or full based on simple_response setting)
        """
        if not self.client:
            raise RuntimeError("GenAI client not initialized. Call initialize_genai() first.")

        # Convert messages format if needed (handle custom image format)
        formatted_messages = self._format_messages_for_openai(messages)

        try:
            response = self.client.chat.completions.create(
                model=self.ai_platform.model,
                messages=formatted_messages
            )

            if self.simple_response:
                return response.choices[0].message.content
            else:
                return response

        except Exception as e:
            raise Exception(f"Error during chat completion: {str(e)}")

    def _prepare_prompt(self, instruction: str, image_paths: list = None):
        """
        Prepare prompt with instructions and images for test automation.

        Args:
            instruction: Test instruction/assertion
            image_paths: List of image file paths

        Returns:
            Formatted prompt as list of messages
        """
        content = [
            {
                "type": "text",
                "text": self.system_prompt
            },
            {
                "type": "text",
                "text": instruction
            }
        ]

        # Add images if vision is supported
        if image_paths and self.ai_platform.supports_vision:
            for img_path in image_paths:
                if not os.path.isfile(img_path):
                    raise FileNotFoundError(f"Image not found: {img_path}")

                content.append({
                    "type": "image",
                    "image_path": img_path
                })

        return [{"role": "user", "content": content}]

    def _format_messages_for_openai(self, messages):
        """
        Convert custom message format to OpenAI-compatible format.
        Handles image paths by converting them to base64 data URIs.

        Args:
            messages: List of messages in custom format

        Returns:
            List of messages in OpenAI format
        """
        formatted_messages = []

        for message in messages:
            formatted_content = []

            for item in message.get("content", []):
                if item.get("type") == "image":
                    # Convert image file to base64 data URI
                    image_path = item.get("image_path")
                    if image_path and self.ai_platform.supports_vision:
                        image_data = self._encode_image_to_base64(image_path)
                        formatted_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": image_data,
                                "detail": self.ai_platform.detail
                            }
                        })
                elif item.get("type") == "text":
                    formatted_content.append({
                        "type": "text",
                        "text": item.get("text", "")
                    })

            formatted_messages.append({
                "role": message.get("role"),
                "content": formatted_content
            })

        return formatted_messages

    @staticmethod
    def _encode_image_to_base64(image_path: str) -> str:
        """
        Encode image file to base64 data URI.

        Args:
            image_path: Path to image file

        Returns:
            Base64-encoded data URI string
        """
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Detect image format from file extension
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/png')

        return f"data:{mime_type};base64,{image_data}"

    @staticmethod
    def extract_result_and_explanation_from_response(response: str):
        """
        Extract RESULT and EXPLANATION from formatted response.

        Args:
            response: AI response string

        Returns:
            Tuple of (result, explanation)
        """
        parts = response.split("RESULT:", 1)
        if len(parts) < 2:
            return "fail", response

        result_and_explanation = parts[1].strip()

        parts = result_and_explanation.split("EXPLANATION:", 1)
        if len(parts) < 2:
            return parts[0].strip(), response

        result = parts[0].strip()
        explanation = parts[1].strip()

        return result, explanation
