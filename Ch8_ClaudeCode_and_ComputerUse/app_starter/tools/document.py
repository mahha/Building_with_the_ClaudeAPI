import os
from markitdown import MarkItDown, StreamInfo
from io import BytesIO
from pydantic import Field


def binary_document_to_markdown(binary_data: bytes, file_type: str) -> str:
    """Converts binary document data to markdown-formatted text."""
    md = MarkItDown()
    file_obj = BytesIO(binary_data)
    stream_info = StreamInfo(extension=file_type)
    result = md.convert(file_obj, stream_info=stream_info)
    return result.text_content


def document_path_to_markdown(
    file_path: str = Field(description="Absolute or relative path to the document file to convert. Supported formats: .pdf, .docx"),
) -> str:
    """Convert a document file at the given path to markdown-formatted text.

    Reads the file at `file_path`, detects its format from the file extension,
    and converts it to markdown using the markitdown library.

    Use this tool when you have a file path to a document and want its content
    as markdown. Prefer this over `binary_document_to_markdown` when you have
    access to the file path rather than the raw bytes.
    Do NOT use this tool for file formats other than .pdf and .docx.

    Examples:
        Input: file_path="/home/user/report.pdf"
        Output: "# Report Title\\n\\nSection content..."

        Input: file_path="./docs/spec.docx"
        Output: "# Spec\\n\\n- Item 1\\n- Item 2\\n"
    """
    extension = os.path.splitext(file_path)[1].lstrip(".")
    with open(file_path, "rb") as f:
        binary_data = f.read()
    return binary_document_to_markdown(binary_data, extension)
