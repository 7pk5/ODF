
import markdown
from xhtml2pdf import pisa
import os

def convert_md_to_pdf(source_md, output_pdf):
    # Read Markdown
    with open(source_md, 'r', encoding='utf-8') as f:
        text = f.read()

    # Convert to HTML
    html_content = markdown.markdown(text, extensions=['extra', 'codehilite'])

    # Add some basic styling
    styled_html = f"""
    <html>
    <head>
    <style>
        body {{ font-family: Helvetica, Arial, sans-serif; font-size: 12pt; line-height: 1.5; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 20px; border-bottom: 1px solid #ddd; }}
        h3 {{ color: #16a085; margin-top: 15px; }}
        code {{ background-color: #f8f9fa; padding: 2px 5px; border-radius: 3px; font-family: Courier; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #ddd; }}
        blockquote {{ border-left: 4px solid #3498db; padding-left: 10px; color: #555; }}
    </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """

    # Convert to PDF
    with open(output_pdf, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(styled_html, dest=pdf_file)

    if pisa_status.err:
        print(f"Error converting to PDF: {pisa_status.err}")
        return False
    
    print(f"PDF successfully created at: {output_pdf}")
    return True

if __name__ == "__main__":
    # Source is the artifact path
    source_path = r"C:\Users\kaust\.gemini\antigravity\brain\3d8b571a-c2d1-4fd6-8d07-ff54a8f5f641\interview_guide.md"
    # Output to the project directory
    output_path = r"d:\FInalYear-Krunal\ODF\Interview_Guide.pdf"
    
    if os.path.exists(source_path):
        convert_md_to_pdf(source_path, output_path)
    else:
        print(f"Source file not found: {source_path}")
