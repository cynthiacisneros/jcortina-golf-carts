import http.server
import sqlite3
import json
import os
import secrets
import urllib.parse
from http.cookies import SimpleCookie

DB_PATH = "requests.db"
ADMIN_PASSWORD = "admin123"
SESSION_TOKEN = secrets.token_hex(16)
PORT = 5500

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT DEFAULT '',
            cart_make TEXT DEFAULT '',
            issue TEXT NOT NULL,
            preferred_date TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()

def save_submission(data):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO submissions (name, phone, email, cart_make, issue, preferred_date) VALUES (?, ?, ?, ?, ?, ?)",
        (data["name"], data["phone"], data.get("email", ""), data.get("cartMake", ""), data["issue"], data.get("date", ""))
    )
    conn.commit()
    conn.close()

def get_submissions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM submissions ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def is_authenticated(cookie_str):
    if not cookie_str:
        return False
    cookie = SimpleCookie()
    cookie.load(cookie_str)
    return cookie.get("session", "").value == SESSION_TOKEN

ADMIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin — Service Requests</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; color: #222; padding: 40px 24px; }
h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: 24px; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
th, td { text-align: left; padding: 12px 16px; font-size: 14px; border-bottom: 1px solid #eee; }
th { background: #222; color: #fff; font-weight: 600; }
tr:hover td { background: #fafafa; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; background: #e8f5e9; color: #2e7d32; }
.empty { padding: 48px 24px; text-align: center; color: #888; font-size: 15px; }
.logout { display: inline-block; margin-bottom: 24px; color: #d32f2f; text-decoration: none; font-size: 14px; }
.login-box { max-width: 360px; margin: 80px auto; background: #fff; padding: 32px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.login-box h1 { font-size: 1.25rem; margin-bottom: 20px; }
.login-box label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: #555; }
.login-box input { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; margin-bottom: 16px; }
.login-box button { width: 100%; padding: 10px; background: #222; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.login-box .error { color: #d32f2f; font-size: 13px; margin-bottom: 12px; }
@media (max-width: 768px) {
  table, thead, tbody, th, td, tr { display: block; }
  thead tr { position: absolute; top: -9999px; left: -9999px; }
  td { padding: 8px 12px; border: none; position: relative; }
  td::before { content: attr(data-label); display: block; font-weight: 600; font-size: 12px; color: #888; margin-bottom: 2px; }
  tr { margin-bottom: 12px; border: 1px solid #eee; border-radius: 6px; overflow: hidden; }
}
</style>
</head>
<body>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/admin/login":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write((ADMIN_HTML + """
<div class="login-box">
  <h1>Admin Login</h1>
  <form method="post" action="/admin/login">
    <label>Password</label>
    <input type="password" name="password" required autofocus />
    <button type="submit">Sign In</button>
  </form>
</div>
</body></html>""").encode())
            return

        if path == "/admin/logout":
            self.send_response(302)
            self.send_header("Set-Cookie", "session=; Max-Age=0; Path=/")
            self.send_header("Location", "/admin/login")
            self.end_headers()
            return

        if path in ("/admin", "/admin/"):
            cookie_str = self.headers.get("Cookie", "")
            if not is_authenticated(cookie_str):
                self.send_response(302)
                self.send_header("Location", "/admin/login")
                self.end_headers()
                return

            rows = get_submissions()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            html = ADMIN_HTML + '<a href="/admin/logout" class="logout">Log out</a>'
            html += f"<h1>Service Requests ({len(rows)})</h1>"

            if not rows:
                html += '<div class="empty">No requests yet.</div>'
            else:
                html += '<table><thead><tr>'
                for col in ["ID", "Name", "Phone", "Email", "Cart Make", "Issue", "Preferred Date", "Submitted"]:
                    html += f"<th>{col}</th>"
                html += '</tr></thead><tbody>'
                for r in rows:
                    html += "<tr>"
                    html += f"<td data-label='ID'>#{r['id']}</td>"
                    html += f"<td data-label='Name'>{r['name']}</td>"
                    html += f"<td data-label='Phone'><a href='tel:{r['phone']}'>{r['phone']}</a></td>"
                    html += f"<td data-label='Email'>{r['email'] or '—'}</td>"
                    html += f"<td data-label='Cart Make'>{r['cart_make'] or '—'}</td>"
                    html += f"<td data-label='Issue'>{r['issue']}</td>"
                    html += f"<td data-label='Date'>{r['preferred_date'] or '—'}</td>"
                    html += f"<td data-label='Submitted'><span class='badge'>{r['created_at']}</span></td>"
                    html += "</tr>"
                html += '</tbody></table>'

            html += '</body></html>'
            self.wfile.write(html.encode())
            return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/submit":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            try:
                data = json.loads(body)
                if not data.get("name") or not data.get("phone") or not data.get("issue"):
                    raise ValueError("Missing required fields")
                save_submission(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
            return

        if path == "/admin/login":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            params = urllib.parse.parse_qs(body)
            password = params.get("password", [""])[0]

            if password == ADMIN_PASSWORD:
                self.send_response(302)
                self.send_header("Set-Cookie", f"session={SESSION_TOKEN}; Path=/; HttpOnly")
                self.send_header("Location", "/admin")
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write((ADMIN_HTML + """
<div class="login-box">
  <h1>Admin Login</h1>
  <div class="error">Incorrect password</div>
  <form method="post" action="/admin/login">
    <label>Password</label>
    <input type="password" name="password" required autofocus />
    <button type="submit">Sign In</button>
  </form>
</div>
</body></html>""").encode())
            return

        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    init_db()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Server running at http://localhost:{PORT}")
    print(f"Admin panel at http://localhost:{PORT}/admin")
    print(f"Password: {ADMIN_PASSWORD}")
    server.serve_forever()
