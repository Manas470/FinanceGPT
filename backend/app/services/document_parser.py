"""
Document Parser Service
Handles CSV, Excel, PDF ingestion and data extraction
"""
import io
import csv
import json
import logging
from pathlib import Path
from typing import Any
import pandas as pd
import pdfplumber

logger = logging.getLogger(__name__)


class DocumentParser:
    """Parses uploaded financial documents into structured data"""

    SUPPORTED_TYPES = {
        "text/csv": "csv",
        "application/vnd.ms-excel": "excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
        "application/pdf": "pdf",
    }

    async def parse(self, file_path: str, mime_type: str) -> dict[str, Any]:
        """
        Parse a financial document and return structured data.
        Returns: {"sheets": {...}, "metadata": {...}, "summary": {...}}
        """
        file_type = self.SUPPORTED_TYPES.get(mime_type)
        if not file_type:
            raise ValueError(f"Unsupported file type: {mime_type}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if file_type == "csv":
            return await self._parse_csv(path)
        elif file_type == "excel":
            return await self._parse_excel(path)
        elif file_type == "pdf":
            return await self._parse_pdf(path)

    async def _parse_csv(self, path: Path) -> dict[str, Any]:
        """Parse CSV financial data"""
        try:
            df = pd.read_csv(path, thousands=",", na_values=["", "-", "N/A", "n/a"])
            df = df.dropna(how="all")

            # Try to detect numeric columns
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[\$,\(\)]", "", regex=True))
                except (ValueError, TypeError):
                    pass

            return {
                "sheets": {
                    "Sheet1": {
                        "columns": df.columns.tolist(),
                        "rows": df.head(500).to_dict(orient="records"),
                        "shape": {"rows": len(df), "cols": len(df.columns)},
                        "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
                        "summary_stats": df.describe().to_dict() if len(df.select_dtypes(include="number").columns) > 0 else {},
                    }
                },
                "metadata": {
                    "file_type": "csv",
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                },
            }
        except Exception as e:
            logger.error(f"CSV parse error: {e}")
            raise ValueError(f"Failed to parse CSV: {str(e)}")

    async def _parse_excel(self, path: Path) -> dict[str, Any]:
        """Parse Excel financial data (all sheets)"""
        try:
            xl = pd.ExcelFile(path)
            sheets = {}

            for sheet_name in xl.sheet_names[:10]:  # Limit to 10 sheets
                try:
                    df = xl.parse(sheet_name, thousands=",", na_values=["", "-", "N/A"])
                    df = df.dropna(how="all")

                    # Try numeric coercion for string columns
                    for col in df.columns:
                        if df[col].dtype == object:
                            try:
                                cleaned = df[col].astype(str).str.replace(r"[\$,\(\)%]", "", regex=True)
                                numeric_try = pd.to_numeric(cleaned, errors="coerce")
                                if numeric_try.notna().sum() > len(df) * 0.5:
                                    df[col] = numeric_try
                            except Exception:
                                pass

                    sheets[sheet_name] = {
                        "columns": [str(c) for c in df.columns.tolist()],
                        "rows": df.head(500).fillna("").to_dict(orient="records"),
                        "shape": {"rows": len(df), "cols": len(df.columns)},
                        "numeric_columns": df.select_dtypes(include="number").columns.tolist(),
                        "summary_stats": df.describe().to_dict(),
                    }
                except Exception as e:
                    logger.warning(f"Sheet {sheet_name} parse failed: {e}")
                    sheets[sheet_name] = {"error": str(e)}

            return {
                "sheets": sheets,
                "metadata": {
                    "file_type": "excel",
                    "sheet_names": xl.sheet_names,
                    "total_sheets": len(xl.sheet_names),
                },
            }
        except Exception as e:
            logger.error(f"Excel parse error: {e}")
            raise ValueError(f"Failed to parse Excel: {str(e)}")

    async def _parse_pdf(self, path: Path) -> dict[str, Any]:
        """Parse PDF financial reports using pdfplumber"""
        try:
            pages_data = []
            tables = []
            full_text = []

            with pdfplumber.open(path) as pdf:
                total_pages = len(pdf.pages)

                for i, page in enumerate(pdf.pages[:50]):  # Limit to 50 pages
                    text = page.extract_text() or ""
                    full_text.append(text)

                    # Extract tables from this page
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table and len(table) > 1:
                            headers = [str(h or f"Col{i}") for i, h in enumerate(table[0])]
                            rows = []
                            for row in table[1:]:
                                row_dict = {}
                                for j, cell in enumerate(row):
                                    if j < len(headers):
                                        row_dict[headers[j]] = cell
                                rows.append(row_dict)
                            tables.append({
                                "page": i + 1,
                                "headers": headers,
                                "rows": rows,
                                "row_count": len(rows),
                            })

                    pages_data.append({
                        "page": i + 1,
                        "text_length": len(text),
                        "has_tables": bool(page_tables),
                    })

            combined_text = "\n\n".join(full_text)

            return {
                "sheets": {
                    "raw_text": {
                        "full_text": combined_text[:50000],  # Cap at 50k chars
                        "word_count": len(combined_text.split()),
                    }
                },
                "tables": tables,
                "metadata": {
                    "file_type": "pdf",
                    "total_pages": total_pages,
                    "pages_processed": len(pages_data),
                    "tables_found": len(tables),
                },
            }
        except Exception as e:
            logger.error(f"PDF parse error: {e}")
            raise ValueError(f"Failed to parse PDF: {str(e)}")

    def detect_document_type(self, data: dict[str, Any], filename: str) -> str:
        """Heuristic detection of financial document type from content"""
        filename_lower = filename.lower()
        text = ""

        if "sheets" in data:
            for sheet in data["sheets"].values():
                if isinstance(sheet, dict):
                    text += " ".join(str(c) for c in sheet.get("columns", []))
                    if "raw_text" in sheet:
                        text += sheet.get("full_text", "")[:2000]

        text = (filename_lower + " " + text).lower()

        if any(kw in text for kw in ["profit", "loss", "income", "revenue", "p&l"]):
            return "profit_loss"
        elif any(kw in text for kw in ["balance sheet", "assets", "liabilities", "equity"]):
            return "balance_sheet"
        elif any(kw in text for kw in ["cash flow", "operating activities", "investing"]):
            return "cash_flow"
        elif any(kw in text for kw in ["trial balance", "general ledger"]):
            return "trial_balance"
        elif any(kw in text for kw in ["annual report", "10-k", "10k"]):
            return "annual_report"
        else:
            return "other"


document_parser = DocumentParser()
