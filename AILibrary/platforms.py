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

from enum import Enum


class Platforms(Enum):
    """Enum defining supported AI platforms with their default configurations."""
    Ollama = {
        "default_model": "qwen3-coder:480b-cloud",
        "default_base_url": "http://localhost:11434/v1",
        "api_key_required": False,
        "supports_vision": True
    }
    DockerModel = {
        "default_model": "ai/qwen3-vl:8B-Q8_K_XL",
        "default_base_url": "http://localhost:12434/engines/v1",
        "api_key_required": False,
        "supports_vision": True
    }

    Perplexity = {
        "default_model": "sonar-pro",
        "default_base_url": "https://api.perplexity.ai",
        "api_key_required": True,
        "supports_vision": True
    }
