import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pygments import highlight
from pygments.lexers import guess_lexer, PythonLexer
from pygments.formatter import Formatter


class ReportLabHTMLFormatter(Formatter):
    """Custom Pygments Formatter generating ReportLab-compatible XML inline tags."""

    def format_unencoded(self, tokensource, outfile):
        token_color_map = {
            'Token.Keyword': '#38BDF8',  # Sky Blue (def, class, return, import)
            'Token.Keyword.Namespace': '#38BDF8',
            'Token.Name.Function': '#FACC15',  # Yellow (method names)
            'Token.Name.Class': '#FACC15',  # Yellow (class names)
            'Token.Name.Decorator': '#E879F9',  # Purple/Pink (@decorator)
            'Token.String': '#4ADE80',  # Light Green ("strings")
            'Token.String.Doc': '#6EE7B7',  # Mint Green (docstrings)
            'Token.Comment': '#64748B',  # Slate Gray (# comments)
            'Token.Number': '#FB923C',  # Orange (numbers)
            'Token.Operator': '#38BDF8',  # Operators (=, +, -)
            'Token.Name.Builtin': '#38BDF8',  # Builtins (str, len, range)
            'Token.Name.Exception': '#F87171',  # Red (exceptions)
        }

        for ttype, value in tokensource:
            safe_val = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;')

            hex_color = None
            str_ttype = str(ttype)
            for key, col in token_color_map.items():
                if str_ttype.startswith(key):
                    hex_color = col
                    break

            if hex_color:
                outfile.write(f'<font color="{hex_color}">{safe_val}</font>')
            else:
                outfile.write(f'<font color="#F8FAFC">{safe_val}</font>')


class PDFReportGenerator:
    """Utility class to generate styled PDF audit reports from SAST Markdown text."""

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Converts Markdown bold and inline code syntax into ReportLab HTML tags."""
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"`(.*?)`", r'<font face="Courier" color="#2563EB"><b>\1</b></font>', text)
        return text

    @classmethod
    def _render_ide_code_table(cls, code_text: str) -> Table:
        """Constructs an IDE-like dark theme code window with line numbers and syntax highlighting."""
        lines = code_text.split('\n')
        if lines and not lines[-1].strip():
            lines.pop()

        try:
            lexer = guess_lexer(code_text)
        except Exception:
            lexer = PythonLexer()

        formatter = ReportLabHTMLFormatter()
        highlighted_lines = [highlight(line, lexer, formatter).rstrip('\n') for line in lines]

        styles = getSampleStyleSheet()

        lineno_style = ParagraphStyle(
            'LineNoStyle',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leading=11,
            alignment=2,  # Right aligned
            textColor=colors.HexColor('#64748B')
        )

        code_style = ParagraphStyle(
            'IDECodeStyle',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#F8FAFC')
        )

        table_data = []
        for idx, h_line in enumerate(highlighted_lines, 1):
            p_lineno = Paragraph(str(idx), lineno_style)
            p_code = Paragraph(h_line if h_line else '&nbsp;', code_style)
            table_data.append([p_lineno, p_code])

        # Expanded width for line numbers (32pt) to support 3+ digit line numbers seamlessly
        code_table = Table(table_data, colWidths=[32, 508])
        code_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('RIGHTPADDING', (0, 0), (0, -1), 4),
            ('LEFTPADDING', (1, 0), (1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
            ('LINEAFTER', (0, 0), (0, -1), 0.8, colors.HexColor('#334155')),
        ]))

        return code_table

    @classmethod
    def _render_markdown_table(cls, table_lines: list) -> Table:
        """Parses raw Markdown pipe table lines into a styled ReportLab Table."""
        styles = getSampleStyleSheet()

        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor('#1E293B')
        )

        header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontSize=8.5,
            leading=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0F172A')
        )

        table_data = []
        for idx, row_str in enumerate(table_lines):
            cols = [c.strip() for c in row_str.strip('|').split('|')]
            row_data = []
            for col_text in cols:
                cleaned = cls._clean_markdown(col_text)
                p_style = header_style if idx == 0 else cell_style
                row_data.append(Paragraph(cleaned, p_style))
            table_data.append(row_data)

        if not table_data:
            return None

        num_cols = len(table_data[0])
        col_width = 540 / max(num_cols, 1)

        t = Table(table_data, colWidths=[col_width] * num_cols)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        return t

    @classmethod
    def build_sast_pdf(cls, file_name: str, report_content: str, output_path: str = "sast_audit_report.pdf") -> str:
        """Constructs a professional PDF document containing the SAST audit report."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'HeaderSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=10
        )

        heading2_style = ParagraphStyle(
            'ReportH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=12,
            spaceAfter=6
        )

        heading3_style = ParagraphStyle(
            'ReportH3',
            parent=styles['Heading3'],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=8,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=5
        )

        story = []

        # Document Header
        story.append(Paragraph("🛡️ CyberAssistant LLM - SAST Security Audit Report", title_style))
        story.append(Paragraph(f"<b>Target File Audited:</b> {file_name}", subtitle_style))
        story.append(
            HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceBefore=2, spaceAfter=10))

        lines = report_content.split('\n')
        in_code_block = False
        code_buffer = []

        in_table = False
        table_buffer = []

        for line in lines:
            raw_line = line.rstrip()
            line_str = raw_line.strip()

            # Handle code block delimiters
            if line_str.startswith("```"):
                # Flush table if active before code block
                if in_table and table_buffer:
                    tbl = cls._render_markdown_table(table_buffer)
                    if tbl:
                        story.append(tbl)
                        story.append(Spacer(1, 6))
                    table_buffer = []
                    in_table = False

                if in_code_block:
                    code_text = "\n".join(code_buffer)
                    if code_text.strip():
                        story.append(Spacer(1, 4))
                        story.append(cls._render_ide_code_table(code_text))
                        story.append(Spacer(1, 6))
                    code_buffer = []
                    in_code_block = False
                else:
                    in_code_block = True
                    code_buffer = []
                continue

            if in_code_block:
                code_buffer.append(raw_line)
                continue

            # Handle Markdown tables
            if line_str.startswith("|") and line_str.endswith("|"):
                # Ignore table alignment lines like |---|---|
                if re.match(r"^\|[\s:\-|\+]+\|$", line_str):
                    continue
                table_buffer.append(line_str)
                in_table = True
                continue
            elif in_table:
                if table_buffer:
                    tbl = cls._render_markdown_table(table_buffer)
                    if tbl:
                        story.append(tbl)
                        story.append(Spacer(1, 6))
                table_buffer = []
                in_table = False

            if not line_str:
                story.append(Spacer(1, 3))
                continue

            if line_str.startswith("### "):
                cleaned = cls._clean_markdown(line_str[4:])
                story.append(Paragraph(cleaned, heading2_style))
            elif line_str.startswith("## ") or line_str.startswith("# "):
                cleaned = cls._clean_markdown(line_str.lstrip("#").strip())
                story.append(Paragraph(cleaned, heading2_style))
            elif re.match(r"^\d+\.\s", line_str):
                cleaned = cls._clean_markdown(line_str)
                story.append(Paragraph(cleaned, heading3_style))
            else:
                cleaned = cls._clean_markdown(line_str)
                story.append(Paragraph(cleaned, body_style))

        # Flush remaining buffers if file ends abruptly
        if in_table and table_buffer:
            tbl = cls._render_markdown_table(table_buffer)
            if tbl:
                story.append(tbl)

        if in_code_block and code_buffer:
            code_text = "\n".join(code_buffer)
            if code_text.strip():
                story.append(Spacer(1, 4))
                story.append(cls._render_ide_code_table(code_text))

        doc.build(story)
        return output_path