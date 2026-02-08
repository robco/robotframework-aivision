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

import base64
import os
import tempfile


class AttachmentProcessor:
    def __init__(self, supports_vision: bool,
                 max_bytes: int = 200_000,
                 max_chars: int = 200_000,
                 pdf_max_pages: int = 3):
        self.supports_vision = supports_vision
        self.max_bytes = max_bytes
        self.max_chars = max_chars
        self.pdf_max_pages = pdf_max_pages

    def prepare_attachment_content(self, attachment_path: str):
        size = os.path.getsize(attachment_path)
        filename = os.path.basename(attachment_path)
        ext = os.path.splitext(attachment_path)[1].lower()
        mime_type = self._guess_mime_type(ext)

        if ext == ".pdf":
            text, truncated, ok = self._read_pdf_text(attachment_path)
            if ok and text.strip():
                body = text.strip()
                kind = "pdf text"
                header = self._format_attachment_header(filename, mime_type, size, kind, truncated)
                return [{"type": "text", "text": header + body}]

            image_paths = []
            if self.supports_vision:
                image_paths = self._render_pdf_to_images(attachment_path)

            if image_paths:
                kind = "pdf images"
                header = self._format_attachment_header(filename, mime_type, size, kind, False)
                items = [{
                    "type": "text",
                    "text": header + f"[PDF rendered to {len(image_paths)} images]"
                }]
                items.extend({"type": "image", "image_path": image_path} for image_path in image_paths)
                return items

            body, truncated = self._read_binary_base64(attachment_path)
            kind = "base64"
            header = self._format_attachment_header(filename, mime_type, size, kind, truncated)
            return [{"type": "text", "text": header + body}]

        body, truncated = self._read_text_file(attachment_path)
        kind = "text"
        header = self._format_attachment_header(filename, mime_type, size, kind, truncated)
        return [{"type": "text", "text": header + body}]

    @staticmethod
    def _format_attachment_header(filename: str, mime_type: str, size: int, kind: str, truncated: bool) -> str:
        header = f"ATTACHMENT: {filename} (mime: {mime_type}, size: {size} bytes, format: {kind}"
        if truncated:
            header += ", truncated"
        header += ")\n"
        return header

    def _read_text_file(self, attachment_path: str):
        data, truncated = self._read_file_bytes(attachment_path, self.max_bytes)
        text = data.decode("utf-8", errors="replace")
        return text, truncated

    def _read_binary_base64(self, attachment_path: str):
        data, truncated = self._read_file_bytes(attachment_path, self.max_bytes)
        return base64.b64encode(data).decode("ascii"), truncated

    def _read_pdf_text(self, attachment_path: str):
        try:
            import fitz  # PyMuPDF
        except Exception:
            return "", False, False

        try:
            doc = fitz.open(attachment_path)
            text_chunks = []
            total_chars = 0
            for page in doc:
                page_text = page.get_text() or ""
                if not page_text:
                    continue
                text_chunks.append(page_text)
                total_chars += len(page_text)
                if total_chars >= self.max_chars:
                    break

            text = "\n".join(text_chunks)
            truncated = len(text) > self.max_chars
            if truncated:
                text = text[: self.max_chars]
            return text, truncated, True
        except Exception:
            return "", False, False

    def _render_pdf_to_images(self, attachment_path: str):
        image_paths = []
        temp_dir = tempfile.mkdtemp(prefix="aivision_pdf_")

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(attachment_path)
            page_count = min(len(doc), self.pdf_max_pages)
            for index in range(page_count):
                page = doc.load_page(index)
                pix = page.get_pixmap()
                image_path = os.path.join(temp_dir, f"pdf_page_{index + 1}.png")
                pix.save(image_path)
                image_paths.append(image_path)
            return image_paths
        except Exception:
            return []

    @staticmethod
    def _read_file_bytes(path: str, max_bytes: int):
        with open(path, "rb") as file_handle:
            data = file_handle.read(max_bytes + 1)
        truncated = len(data) > max_bytes
        if truncated:
            data = data[:max_bytes]
        return data, truncated

    @staticmethod
    def _guess_mime_type(ext: str) -> str:
        mime_types = {
            ".txt": "text/plain",
            ".log": "text/plain",
            ".pdf": "application/pdf",
            ".md": "text/markdown",
            ".json": "application/json",
            ".yaml": "application/x-yaml",
            ".yml": "application/x-yaml",
            ".xml": "application/xml",
            ".csv": "text/csv",
            ".py": "text/x-python",
            ".js": "text/javascript",
            ".ts": "text/typescript",
            ".java": "text/x-java-source",
            ".c": "text/x-c",
            ".h": "text/x-c",
            ".cpp": "text/x-c",
            ".hpp": "text/x-c",
            ".rs": "text/x-rust",
            ".go": "text/x-go",
            ".rb": "text/x-ruby",
            ".php": "text/x-php",
            ".sh": "text/x-shellscript"
        }
        return mime_types.get(ext, "text/plain")
