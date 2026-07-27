import os
import re
from pypdf import PdfReader
from typing import Optional


class PDFTool:

    def __init__(self):
        self.loaded_pdfs = {}

    def load_pdf(self, file_path: str) -> dict:

        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            reader = PdfReader(file_path)

            pages = []
            for i, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages.append({
                    "page": i,
                    "text": text.strip(),
                    "char_count": len(text.strip()),
                    "has_images": len(page.images) > 0 if hasattr(page, 'images') else False
                })

            pdf_info = {
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "page_count": len(reader.pages),
                "pages": pages,
                "metadata": reader.metadata if reader.metadata else {}
            }

            self.loaded_pdfs[file_path] = pdf_info

            return {"success": True, "data": pdf_info}

        except Exception as e:
            return {"success": False, "error": f"Failed to load PDF: {str(e)}"}

    def extract_text(self, file_path: str, page_range: Optional[str] = None) -> str:

        if file_path not in self.loaded_pdfs:
            load_result = self.load_pdf(file_path)
            if not load_result["success"]:
                return load_result["error"]

        pdf_info = self.loaded_pdfs[file_path]

        if page_range:
            pages = self._parse_page_range(page_range, pdf_info["page_count"])
            selected_pages = [p for p in pdf_info["pages"] if p["page"] in pages]
        else:
            selected_pages = pdf_info["pages"]

        text_parts = []
        for page in selected_pages:
            text_parts.append(f"--- Page {page['page']} ---\n{page['text']}")

        return "\n\n".join(text_parts)

    def extract_tables(self, file_path: str) -> list:

        if file_path not in self.loaded_pdfs:
            load_result = self.load_pdf(file_path)
            if not load_result["success"]:
                return [{"error": load_result["error"]}]

        pdf_info = self.loaded_pdfs[file_path]
        tables = []

        for page in pdf_info["pages"]:
            text = page["text"]
            lines = text.split('\n')

            table_like = []
            for line in lines:
                if '|' in line or '\t' in line:
                    table_like.append(line)

            if len(table_like) >= 2:
                delimiter = '|' if '|' in table_like[0] else '\t'
                parsed_rows = []
                for row in table_like:
                    cells = [cell.strip() for cell in row.split(delimiter) if cell.strip()]
                    if cells:
                        parsed_rows.append(cells)

                if parsed_rows:
                    tables.append({
                        "page": page["page"],
                        "rows": len(parsed_rows),
                        "columns": len(parsed_rows[0]) if parsed_rows else 0,
                        "data": parsed_rows
                    })

        return tables

    def search_text(self, file_path: str, query: str) -> list:

        if file_path not in self.loaded_pdfs:
            load_result = self.load_pdf(file_path)
            if not load_result["success"]:
                return []

        pdf_info = self.loaded_pdfs[file_path]
        results = []

        for page in pdf_info["pages"]:
            text_lower = page["text"].lower()
            query_lower = query.lower()

            if query_lower in text_lower:
                start = max(0, text_lower.index(query_lower) - 100)
                end = min(len(page["text"]), text_lower.index(query_lower) + len(query) + 100)
                context = page["text"][start:end]

                results.append({
                    "page": page["page"],
                    "context": f"...{context}...",
                    "position": text_lower.index(query_lower)
                })

        return results

    def summarize_page(self, file_path: str, page_number: int) -> str:

        if file_path not in self.loaded_pdfs:
            load_result = self.load_pdf(file_path)
            if not load_result["success"]:
                return load_result["error"]

        pdf_info = self.loaded_pdfs[file_path]

        for page in pdf_info["pages"]:
            if page["page"] == page_number:
                text = page["text"]
                sentences = re.split(r'[.!?]+', text)
                sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

                summary = '. '.join(sentences[:5]) + '.'
                return summary

        return f"Page {page_number} not found"

    def get_info(self, file_path: str) -> dict:

        if file_path not in self.loaded_pdfs:
            load_result = self.load_pdf(file_path)
            if not load_result["success"]:
                return load_result

        pdf_info = self.loaded_pdfs[file_path]

        return {
            "success": True,
            "filename": pdf_info["filename"],
            "page_count": pdf_info["page_count"],
            "total_chars": sum(p["char_count"] for p in pdf_info["pages"]),
            "pages_with_images": sum(1 for p in pdf_info["pages"] if p["has_images"]),
            "metadata": pdf_info["metadata"]
        }

    def _parse_page_range(self, page_range: str, max_pages: int) -> list:

        pages = set()

        for part in page_range.split(','):
            part = part.strip()

            if '-' in part:
                start, end = part.split('-')
                start = max(1, int(start.strip()))
                end = min(max_pages, int(end.strip()))
                pages.update(range(start, end + 1))
            else:
                page_num = int(part.strip())
                if 1 <= page_num <= max_pages:
                    pages.add(page_num)

        return sorted(pages)


pdf_tool = PDFTool()


def extract_pdf_text(file_path: str, page_range: Optional[str] = None) -> str:
    return pdf_tool.extract_text(file_path, page_range)


def search_pdf(file_path: str, query: str) -> list:
    return pdf_tool.search_text(file_path, query)


def get_pdf_info(file_path: str) -> dict:
    return pdf_tool.get_info(file_path)


def extract_pdf_tables(file_path: str) -> list:
    return pdf_tool.extract_tables(file_path)
