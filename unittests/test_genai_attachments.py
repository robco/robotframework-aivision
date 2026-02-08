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

from AIVision.genai import GenAI
from AIVision.attachments import AttachmentProcessor


def test_prepare_prompt_includes_text_attachment(tmp_path):
    attachment = tmp_path / "notes.txt"
    attachment.write_text("Hello from attachment")

    genai = GenAI(initialize=False)
    prompt = genai._prepare_prompt(
        "Check text attachment",
        image_paths=[],
        attachment_paths=[str(attachment)]
    )

    content = prompt[0]["content"]
    attachment_blocks = [item for item in content if item.get("type") == "text"]
    assert any("ATTACHMENT:" in item["text"] and "Hello from attachment" in item["text"]
               for item in attachment_blocks)


def test_prepare_prompt_includes_unknown_extension_as_text(tmp_path):
    attachment = tmp_path / "data.bin"
    attachment.write_bytes(b"abc123")

    genai = GenAI(initialize=False)
    prompt = genai._prepare_prompt(
        "Check binary attachment",
        image_paths=[],
        attachment_paths=[str(attachment)]
    )

    content = prompt[0]["content"]
    attachment_blocks = [item for item in content if item.get("type") == "text"]
    assert any("format: text" in item["text"] and "abc123" in item["text"]
               for item in attachment_blocks)


def test_format_attachment_uses_pdf_text_when_available(tmp_path, monkeypatch):
    attachment = tmp_path / "file.pdf"
    attachment.write_bytes(b"%PDF-1.4 mock")

    processor = AttachmentProcessor(supports_vision=False)
    monkeypatch.setattr(processor, "_read_pdf_text", lambda path: ("PDF TEXT", False, True))

    items = processor.prepare_attachment_content(str(attachment))
    text_items = [item for item in items if item.get("type") == "text"]
    assert any("format: pdf text" in item["text"] and "PDF TEXT" in item["text"]
               for item in text_items)


def test_format_attachment_unknown_extension_defaults_to_text(tmp_path):
    attachment = tmp_path / "data.unknown"
    attachment.write_text("Unknown extension content")

    processor = AttachmentProcessor(supports_vision=False)
    items = processor.prepare_attachment_content(str(attachment))
    text_items = [item for item in items if item.get("type") == "text"]

    assert any("format: text" in item["text"] and "Unknown extension content" in item["text"]
               for item in text_items)


def test_pdf_fallback_renders_images_when_no_text(tmp_path, monkeypatch):
    attachment = tmp_path / "file.pdf"
    attachment.write_bytes(b"%PDF-1.4 mock")

    processor = AttachmentProcessor(supports_vision=True)
    monkeypatch.setattr(processor, "_read_pdf_text", lambda path: ("", False, True))
    monkeypatch.setattr(processor, "_render_pdf_to_images", lambda path: ["page1.png", "page2.png"])

    items = processor.prepare_attachment_content(str(attachment))
    text_items = [item for item in items if item.get("type") == "text"]
    image_items = [item for item in items if item.get("type") == "image"]

    assert any("format: pdf images" in item["text"] for item in text_items)
    assert [item["image_path"] for item in image_items] == ["page1.png", "page2.png"]
