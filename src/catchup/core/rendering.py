"""Markdown rendering utilities with LaTeX support."""
import markdown
from markdown.extensions import fenced_code, tables, nl2br


def render_markdown_to_html(markdown_text: str) -> str:
    """
    Convert markdown to HTML with LaTeX support.

    Extensions:
    - fenced_code: For code blocks
    - tables: For markdown tables
    - nl2br: Newline to <br>
    """
    md = markdown.Markdown(
        extensions=[
            'fenced_code',
            'tables',
            'nl2br',
            'pymdownx.arithmatex',
        ],
        extension_configs={
            'pymdownx.arithmatex': {
                'generic': True
            }
        }
    )

    html = md.convert(markdown_text)
    return html


def create_lecture_html(
    title: str,
    course_code: str,
    lecture_date: str,
    markdown_content: str
) -> str:
    """
    Create full HTML page for lecture with MathJax support.
    """
    html_content = render_markdown_to_html(markdown_content)

    html = f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - CatchUp</title>

    <!-- MathJax for LaTeX rendering -->
    <script>
        MathJax = {{
            tex: {{
                inlineMath: [['$', '$']],
                displayMath: [['$$', '$$']],
                processEscapes: true
            }}
        }};
    </script>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background: #f9f9f9;
        }}

        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .header {{
            border-bottom: 2px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .header h1 {{
            margin: 0 0 10px 0;
            color: #007bff;
        }}

        .meta {{
            color: #666;
            font-size: 0.95em;
        }}

        .meta strong {{
            color: #333;
        }}

        .content {{
            margin-top: 30px;
        }}

        .content h1 {{
            color: #007bff;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
            margin-top: 40px;
        }}

        .content h2 {{
            color: #0056b3;
            margin-top: 30px;
        }}

        .content h3 {{
            color: #495057;
            margin-top: 20px;
        }}

        .content ul, .content ol {{
            padding-left: 30px;
        }}

        .content li {{
            margin: 8px 0;
        }}

        .content code {{
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        .content pre {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #007bff;
        }}

        .content pre code {{
            background: none;
            padding: 0;
        }}

        .content table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}

        .content table th,
        .content table td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}

        .content table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}

        .content blockquote {{
            border-left: 4px solid #007bff;
            padding-left: 20px;
            margin-left: 0;
            color: #666;
            font-style: italic;
        }}

        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #007bff;
            text-decoration: none;
            font-weight: 500;
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Tilbake til oversikt</a>

        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                <strong>Kurs:</strong> {course_code} |
                <strong>Dato:</strong> {lecture_date}
            </div>
        </div>

        <div class="content">
            {html_content}
        </div>
    </div>
</body>
</html>"""

    return html
