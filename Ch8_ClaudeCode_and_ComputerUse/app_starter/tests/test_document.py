import os
import shutil
import tempfile
import pytest
from tools.document import binary_document_to_markdown, document_path_to_markdown


class TestBinaryDocumentToMarkdown:
    # Define fixture paths
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    def test_fixture_files_exist(self):
        """Verify test fixtures exist."""
        assert os.path.exists(self.DOCX_FIXTURE), (
            f"DOCX fixture not found at {self.DOCX_FIXTURE}"
        )
        assert os.path.exists(self.PDF_FIXTURE), (
            f"PDF fixture not found at {self.PDF_FIXTURE}"
        )

    def test_binary_document_to_markdown_with_docx(self):
        """Test converting a DOCX document to markdown."""
        # Read binary content from the fixture
        with open(self.DOCX_FIXTURE, "rb") as f:
            docx_data = f.read()

        # Call function
        result = binary_document_to_markdown(docx_data, "docx")

        # Basic assertions to check the conversion was successful
        assert isinstance(result, str)
        assert len(result) > 0
        # Check for typical markdown formatting - this will depend on your actual test file
        assert "#" in result or "-" in result or "*" in result


class TestDocumentPathToMarkdown:
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
    DOCX_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.docx")
    PDF_FIXTURE = os.path.join(FIXTURES_DIR, "mcp_docs.pdf")

    def test_document_path_to_markdown_with_docx(self):
        """Test converting a DOCX file path to markdown."""
        result = document_path_to_markdown(self.DOCX_FIXTURE)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "#" in result or "-" in result or "*" in result

    def test_document_path_to_markdown_with_pdf(self):
        """Test converting a PDF file path to markdown."""
        result = document_path_to_markdown(self.PDF_FIXTURE)

        assert isinstance(result, str)
        assert len(result) > 0
        assert "#" in result or "-" in result or "*" in result
    def test_binary_document_to_markdown_with_pdf(self):
        """Test converting a PDF document to markdown."""
        # Read binary content from the fixture
        with open(self.PDF_FIXTURE, "rb") as f:
            pdf_data = f.read()

        # Call function
        result = binary_document_to_markdown(pdf_data, "pdf")

        # Basic assertions to check the conversion was successful
        assert isinstance(result, str)
        assert len(result) > 0
        # Check for typical markdown formatting - this will depend on your actual test file
        assert "#" in result or "-" in result or "*" in result

    def test_file_not_found(self):
        """Non-existent path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            document_path_to_markdown("/nonexistent/path/to/file.pdf")

    def test_unsupported_extension(self):
        """Unsupported file extension returns a string (markitdown does not raise)."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"some content")
            tmp_path = f.name
        try:
            result = document_path_to_markdown(tmp_path)
            assert isinstance(result, str)
        finally:
            os.unlink(tmp_path)

    def test_path_with_spaces(self):
        """File path containing spaces is handled correctly."""
        tmp_dir = tempfile.mkdtemp()
        spaced_path = os.path.join(tmp_dir, "my document file.docx")
        try:
            shutil.copy(self.DOCX_FIXTURE, spaced_path)
            result = document_path_to_markdown(spaced_path)
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            shutil.rmtree(tmp_dir)

    def test_docx_contains_markdown_headings(self):
        """DOCX with headings produces markdown heading syntax."""
        result = document_path_to_markdown(self.DOCX_FIXTURE)
        assert "#" in result

    def test_pdf_returns_string(self):
        """PDF conversion returns a str, not bytes or None."""
        result = document_path_to_markdown(self.PDF_FIXTURE)
        assert isinstance(result, str)

    def test_docx_returns_string(self):
        """DOCX conversion returns a str, not bytes or None."""
        result = document_path_to_markdown(self.DOCX_FIXTURE)
        assert isinstance(result, str)
