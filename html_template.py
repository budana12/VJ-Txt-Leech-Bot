"""
HTML Template Generator for JSON to HTML Converter Bot
This module contains functions for generating HTML templates with collapsible sections
"""
from datetime import datetime

def generate_html(content_html: str, title: str) -> str:
    """
    Generate a complete HTML document with collapsible sections.
    
    Args:
        content_html: The HTML content for the collapsible sections
        title: The title of the HTML document
    
    Returns:
        str: Complete HTML document as a string
    """
    display_title = title.replace("_", " ")
    current_date = datetime.now().strftime('%d-%m-%Y')
    current_time = datetime.now().strftime('%I:%M %p')
    current_year = datetime.now().year
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{display_title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    body {{
      font-family: 'Poppins', sans-serif;
      margin: 0;
      background-color: #f8f9fa;
    }}

    .loading-wrapper {{
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: linear-gradient(135deg, #1a1a2e, #16213e);
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: white;
      z-index: 9999;
    }}

    .loading-text {{
      font-size: 2rem;
      font-weight: 600;
      margin-bottom: 2rem;
      background: linear-gradient(90deg, #00dbde, #fc00ff);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      text-align: center;
    }}

    .progress-container {{
      width: 80%;
      max-width: 400px;
      text-align: center;
    }}

    .progress-bar {{
      width: 100%;
      height: 10px;
      background-color: #2c2c54;
      border-radius: 10px;
      overflow: hidden;
    }}

    .progress-bar-fill {{
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #00dbde, #fc00ff);
      border-radius: 10px;
      animation: progress 2s ease-in-out infinite;
    }}

    @keyframes progress {{
      0% {{ width: 0%; }}
      50% {{ width: 100%; }}
      100% {{ width: 0%; left: 100%; }}
    }}

    .container {{
      width: 850px;
      margin: 20px auto;
      display: none;
    }}

    .header {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 20px;
      margin-bottom: 20px;
      justify-content: center;
      background: linear-gradient(135deg, #007BFF, #00C6FF, #7EE8FA, #EEC0C6);
      padding: 20px;
      border-radius: 15px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }}

    .thumbnail {{
      width: 120px;
      border-radius: 10px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}

    h1 {{
      flex: 1 1 300px;
      text-align: center;
      margin: 0;
      color: #fff;
      font-weight: 700;
      text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
    }}

    .info-container {{
      text-align: center;
      margin: 20px 0;
      padding: 15px;
      background: #ffffff;
      border-radius: 10px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }}

    .datetime {{
      font-size: 14px;
      color: #555;
      margin: 10px 0;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 5px;
    }}

    .bot-info {{
      text-align: center;
      padding: 15px;
      background: linear-gradient(to right, #f5f7fa, #c3cfe2);
      border-radius: 10px;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }}

    .collapsible {{
      background: linear-gradient(135deg, #6e8efb, #a777e3);
      color: white;
      cursor: pointer;
      padding: 12px;
      width: 100%;
      border: none;
      text-align: center;
      font-size: 16px;
      border-radius: 8px;
      margin-top: 10px;
      font-weight: 600;
      transition: all 0.3s ease;
    }}

    .active, .collapsible:hover {{
      background: linear-gradient(135deg, #5a7bf9, #9664d4);
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }}

    .content {{
      padding: 10px 18px;
      display: none;
      overflow: hidden;
      background-color: #ffffff;
      margin-top: 5px;
      border-radius: 8px;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
    }}

    .section {{
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      margin-bottom: 12px;
      padding: 5px;
      background: #f9f9f9;
    }}

    .item {{
      padding: 10px;
      border-bottom: 1px solid #eee;
      text-align: center;
    }}

    .item:hover {{
      background: #f0f0f0;
    }}

    a {{
      text-decoration: none;
      color: #4a6bff;
      font-weight: 500;
    }}

    a:hover {{
      color: #2a4bdf;
      text-decoration: underline;
    }}

    .footer-strip {{
      margin-top: 40px;
      padding: 15px;
      text-align: center;
      background: linear-gradient(to right, #ff6a00, #ee0979);
      color: white;
      font-weight: 600;
      border-radius: 8px;
      font-size: 1.1rem;
    }}
  </style>
</head>
<body>

  <div class="loading-wrapper" id="loader">
    <div class="loading-text">Welcome To Engineer's Babu</div>
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-bar-fill"></div>
      </div>
      <div class="progress-text">Your Content is Preparing...</div>
    </div>
  </div>

  <div class="container" id="main-content">
    <div class="header">
      <img class="thumbnail" src="https://i.postimg.cc/4N69wBLt/hat-hacker.webp" alt="Thumbnail">
      <h1>{display_title}</h1>
    </div>

    <div class="info-container">
      <div class="datetime">📅 Date: {current_date} | 🕒 Time: {current_time}</div>
      <div class="subheading">📥 Extracted By: <a href="https://t.me/Engineersbabuhelpbot" target="_blank">𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™</a></div>
    </div>

    <div class="bot-info">
      ✨ Use This Bot for JSON to HTML File Extraction: <a href="https://t.me/htmlextractorbot" target="_blank">@htmlextractorbot</a><br><br>
      🔔 Broadcast Channel: <a href="https://t.me/engineersbabu" target="_blank">@EngineersBabu</a>
    </div>

    <div class="content-container">
      {content_html}
    </div>

    <div class="footer-strip">
      𝕰𝖓𝖌𝖎𝖓𝖊𝖊𝖗𝖘 𝕭𝖆𝖇𝖚™ © {current_year}
    </div>
  </div>

  <script>
    window.addEventListener("load", () => {{
      setTimeout(() => {{
        document.getElementById("loader").style.display = "none";
        document.getElementById("main-content").style.display = "block";
      }}, 1500);
    }});

    document.addEventListener('DOMContentLoaded', function() {{
      var coll = document.getElementsByClassName("collapsible");
      for (var i = 0; i < coll.length; i++) {{
        coll[i].addEventListener("click", function() {{
          this.classList.toggle("active");
          var content = this.nextElementSibling;
          content.style.display = content.style.display === "block" ? "none" : "block";
        }});
      }}
    }});
  </script>
</body>
</html>"""

if __name__ == "__main__":
    # Example usage
    sample_content = """
    <div class="section">
      <button class="collapsible">Example Section</button>
      <div class="content">
        <div class="item">Example item</div>
        <div class="item"><a href="https://example.com" target="_blank">Example link</a></div>
      </div>
    </div>
    """
    
    html = generate_html(sample_content, "Test_Title")
    print(html)
