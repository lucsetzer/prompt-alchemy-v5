from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import sys
from pathlib import Path

# Add parent directory to path to import auth modules
sys.path.append(str(Path(__file__).parent.parent))

# Import from root directory
try:
    from auth import verify_magic_link, create_magic_link
    from email_service import send_magic_link_email
except ImportError as e:
    print(f"Import error: {e}")
    # Mock functions for testing
    def verify_magic_link(token):
        return "test@example.com" if token else None
    def create_magic_link(email):
        return f"/auth?token=test_{email}"
    def send_magic_link_email(email):
        print(f"📨 MOCK: Magic link for {email}")
        return f"http://localhost:8000/auth?token=test_{email}"

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_user_balance(email: str):
    """Get user's token balance from bank database"""
    db_path = Path(__file__).parent.parent / "bank.db"
    conn = sqlite3.connect(str(db_path))
    c = conn.cursor()
    c.execute('SELECT tokens FROM accounts WHERE email = ?', (email,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# Routes
@app.get("/")
async def root(request: Request, session: str = Cookie(default=None)):
    """Main dashboard - requires login"""
    if not session:
        return RedirectResponse("/login")
    
    email = verify_magic_link(session)
    if not email:
        return RedirectResponse("/login")
    
    balance = get_user_balance(email)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_email": email,
        "balance": balance,
        "apps": [
            {"name": "Thumbnail Wizard", "cost": 4, "icon": "🖼️", "status": "ready"},
            {"name": "Document Wizard", "cost": 4, "icon": "📄", "status": "ready"},
            {"name": "Hook Wizard", "cost": 4, "icon": "🎣", "status": "ready"},
            {"name": "Prompt Wizard", "cost": 5, "icon": "✨", "status": "ready"},
            {"name": "Script Wizard", "cost": 3, "icon": "📝", "status": "ready"},
            {"name": "A11y Wizard", "cost": 0, "icon": "♿", "status": "ready"},
        ]
    })

@app.get("/login")
async def login_page(request: Request):
    """Login form"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_request(email: str = Form(...)):
    """Send magic link - CORRECTED"""
    link = send_magic_link_email(email)
    
    # Create a mock request for the template
    from fastapi import Request
    mock_request = Request(scope={"type": "http"})
    
    return templates.TemplateResponse("check_email.html", {
        "request": mock_request,
        "email": email
    })

@app.get("/debug")
async def debug_all():
    """Show all routes and templates"""
    import os
    templates_dir = "templates"
    templates = os.listdir(templates_dir) if os.path.exists(templates_dir) else []
    
    return HTMLResponse(f"""
    <h1>Debug Info</h1>
    <h2>Routes:</h2>
    <ul>
        <li>GET / → dashboard (requires login)</li>
        <li>GET /login → login page</li>
        <li>POST /login → send magic link</li>
        <li>GET /auth → verify magic link</li>
        <li>GET /logout → clear session</li>
    </ul>
    <h2>Templates found:</h2>
    <ul>
        {"".join(f'<li>{t}</li>' for t in templates)}
    </ul>
    <h2><a href="/login">Go to login page</a></h2>
    """)

@app.get("/auth")
async def auth_callback(token: str):
    """Magic link callback - sets cookie"""
    email = verify_magic_link(token)
    if not email:
        return RedirectResponse("/login?error=invalid")
    
    response = RedirectResponse("/")
    response.set_cookie(key="session", value=token)
    return response

@app.get("/logout")
async def logout():
    """Logout - clears cookie"""
    response = RedirectResponse("/login")
    response.delete_cookie(key="session")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
