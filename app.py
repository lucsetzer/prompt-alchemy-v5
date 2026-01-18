import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")


from fastapi import FastAPI, Request, Query, Body, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import requests
import json
#from routes.dashboard import router as dashboard_router
#from routes.script_wizard import router as script_wizard_router
import time
from fastapi.templating import Jinja2Templates
from fastapi import Request
import sqlite3
import secrets
import datetime


app = FastAPI(title="Prompt Wizard")
templates = Jinja2Templates(directory="templates") 
#app.include_router(dashboard_router)
#app.include_router(script_wizard_router)

# ========== ICON MAPPING ==========
ICON_MAP = {
    # Goals
    "explain": "fa-solid fa-comment-dots",
    "create": "fa-solid fa-lightbulb",
    "analyze": "fa-solid fa-chart-bar",
    "solve": "fa-solid fa-puzzle-piece",
    "brainstorm": "fa-solid fa-brain",
    "edit": "fa-solid fa-pen-to-square",
    
    # Audiences
    "general": "fa-solid fa-users",
    "experts": "fa-solid fa-user-tie",
    "students": "fa-solid fa-graduation-cap",
    "business": "fa-solid fa-briefcase",
    "technical": "fa-solid fa-code",
    "beginners": "fa-solid fa-person-circle-question",
    
    # Platforms
    "chatgpt": "fa-solid fa-comment",
    "claude": "fa-solid fa-robot",
    "gemini": "fa-solid fa-search",
    "deepseek": "fa-solid fa-rocket",
    "perplexity": "fa-solid fa-book",
    "copilot": "fa-solid fa-terminal",
    
    # Styles
    "direct": "fa-solid fa-bullseye",
    "structured": "fa-solid fa-layer-group",
    "creative": "fa-solid fa-palette",
    "technical": "fa-solid fa-microchip",
    "conversational": "fa-solid fa-comments",
    "step-by-step": "fa-solid fa-shoe-prints",
    
    # Tones
    "professional": "fa-solid fa-suitcase",
    "friendly": "fa-solid fa-face-smile",
    "authoritative": "fa-solid fa-graduation-cap",
    "enthusiastic": "fa-solid fa-fire",
    "neutral": "fa-solid fa-balance-scale",
    "humorous": "fa-solid fa-face-laugh-beam",
}

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "ok",
        "service": "Prompt Wizard",
        "version": "1.0",
        "timestamp": time.time()
    }

@app.get("/test")
async def test_page():
    """Simple test page without complex dependencies"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <style>
            body { font-family: sans-serif; padding: 2rem; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1 class="success">✅ App is Running!</h1>
        <p>Basic FastAPI app is working.</p>
        <p><a href="/">Go to Home</a></p>
        <p><a href="/health">Check Health Endpoint</a></p>
    </body>
    </html>
    """)

from fastapi import Cookie, HTTPException

def get_current_user(session_token: str = Cookie(None)):
    """Get current user from session token"""
    if not session_token:
        return None
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """SELECT email, expires_at 
               FROM user_sessions 
               WHERE session_token = ? AND expires_at > ?""",
            (session_token, datetime.datetime.now())
        )
        session = cursor.fetchone()
        
        if not session:
            return None
        
        email, expires_at = session
        
        # Get user data
        cursor.execute(
            "SELECT email, tokens FROM users WHERE email = ?",
            (email,)
        )
        user = cursor.fetchone()
        
        if user:
            return {
                "email": user[0],
                "tokens": user[1],
                "session_token": session_token
            }
        return None
        
    finally:
        conn.close()



def init_db():
    """Initialize SQLite database for users"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        tokens INTEGER DEFAULT 10,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # Login tokens table (for magic links)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS login_tokens (
        token TEXT PRIMARY KEY,
        email TEXT,
        expires_at TIMESTAMP,
        used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # User sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_token TEXT PRIMARY KEY,
        email TEXT,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (email) REFERENCES users(email)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize on startup
init_db()


@app.get("/api/auth/login")
async def verify_login(token: str):
    """Verify magic link token and log user in"""
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # Check token validity
        cursor.execute(
            """SELECT email, expires_at, used 
               FROM login_tokens 
               WHERE token = ? AND used = 0""",
            (token,)
        )
        token_data = cursor.fetchone()
        
        if not token_data:
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Invalid Link - Prompts Alchemy</title>
                    <style>
                        body { background: #0f172a; color: white; font-family: sans-serif; padding: 3rem; text-align: center; }
                        .card { background: #1e293b; padding: 2rem; border-radius: 12px; max-width: 500px; margin: 2rem auto; }
                        .success { color: #10b981; }
                        .error { color: #ef4444; }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <h1 class="error">Invalid or Expired Link</h1>
                        <p>This login link is invalid or has already been used.</p>
                        <p><a href="/prompt-wizard" style="color: #0cc0df;">Go to Prompt Wizard</a></p>
                    </div>
                </body>
                </html>
            """)
        
        email, expires_at, used = token_data
        
        # Check expiration
        if datetime.datetime.now() > datetime.datetime.fromisoformat(expires_at):
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <body style="background: #0f172a; color: white; font-family: sans-serif; padding: 3rem; text-align: center;">
                    <div style="background: #1e293b; padding: 2rem; border-radius: 12px; max-width: 500px; margin: 2rem auto;">
                        <h1 style="color: #ef4444;">Link Expired</h1>
                        <p>This login link has expired. Please request a new one.</p>
                        <p><a href="/prompt-wizard" style="color: #0cc0df;">Go to Prompt Wizard</a></p>
                    </div>
                </body>
                </html>
            """)
        
        # Mark token as used
        cursor.execute(
            "UPDATE login_tokens SET used = 1 WHERE token = ?",
            (token,)
        )
        
        # Update user last login
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE email = ?",
            (datetime.datetime.now(), email)
        )
        
        conn.commit()
        
        # Create session token for the user
        session_token = secrets.token_urlsafe(32)
        session_expires = datetime.datetime.now() + datetime.timedelta(days=30)
        
        # Store session (in production, use Redis or database)
        cursor.execute(
            """INSERT OR REPLACE INTO user_sessions 
               (session_token, email, expires_at) 
               VALUES (?, ?, ?)""",
            (session_token, email, session_expires)
        )
        
        conn.commit()
        
        # Create response with redirect and set cookie
        response = HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Successful - Prompts Alchemy</title>
                <style>
                    body {{ background: #0f172a; color: white; font-family: sans-serif; padding: 3rem; text-align: center; }}
                    .card {{ background: #1e293b; padding: 2rem; border-radius: 12px; max-width: 500px; margin: 2rem auto; }}
                    .success {{ color: #10b981; }}
                </style>
                <script>
                    // Set session cookie
                    document.cookie = "session_token={session_token}; path=/; max-age=2592000; samesite=strict";
                    
                    // Redirect after 2 seconds
                    setTimeout(function() {{
                        window.location.href = "/dashboard";
                    }}, 2000);
                </script>
            </head>
            <body>
                <div class="card">
                    <h1 class="success">✅ Login Successful!</h1>
                    <p>Welcome back, <strong>{email}</strong>!</p>
                    <p>Redirecting to your dashboard...</p>
                    <p><a href="/dashboard" style="color: #0cc0df;">Click here if not redirected</a></p>
                </div>
            </body>
            </html>
        """)
        
        # Also set cookie server-side
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=60*60*24*30,  # 30 days
            httponly=True,
            samesite="strict"
        )
        
        return response
        
    except Exception as e:
        conn.rollback()
        return HTMLResponse(f"""
            <html>
            <body style="background: #0f172a; color: white; padding: 3rem; text-align: center;">
                <div style="background: #1e293b; padding: 2rem; border-radius: 12px; max-width: 500px; margin: 2rem auto;">
                    <h1 style="color: #ef4444;">Error</h1>
                    <p>An error occurred: {str(e)}</p>
                    <p><a href="/" style="color: #0cc0df;">Go Home</a></p>
                </div>
            </body>
            </html>
        """)
    finally:
        conn.close()


# ========== CORE LAYOUT FUNCTION ==========
def layout(title: str, content: str, step: int = 1) -> HTMLResponse:
    """Dark theme layout - FIXED all issues"""
    
    progress_percent = (step / 6) * 100 if step <= 6 else 100
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        /* DARK THEME */
        body {{
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
        }}
        
        /* FULL-WIDTH NAV */
        .app-nav {{
            background: #1e293b;
            border-bottom: 1px solid #334155;
            padding: 1rem 0;
            width: 100%;
        }}
        
        .nav-inner {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 1rem;
        }}
        
        .app-nav a {{
            color: #cbd5e1;
            text-decoration: none;
        }}
        
        .app-nav a:hover {{
            color: #0cc0df;
        }}
        
        /* MAIN CONTENT - Full width but constrained */
        .app-main {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1rem 4rem 1rem;
            min-height: 70vh;
        }}
        
        /* Progress bar */
        .progress-bar {{
            height: 8px;
            background: #334155;
            border-radius: 4px;
            overflow: hidden;
            margin: 2rem 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #0cc0df, #00d9ff);
            width: {progress_percent}%;
        }}
        
        /* Progress steps - HORIZONTAL */
        .progress-steps {{
            display: flex;
            justify-content: space-between;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: #94a3b8;
        }}
        
        .progress-step {{
            text-align: center;
            flex: 1;
        }}
        
        .progress-step.active {{
            color: #0cc0df;
            font-weight: bold;
        }}
        
        /* STEP GRID - 2 COLUMNS */
        .step-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1.5rem;
            margin: 2rem 0;
        }}
        
        /* Step cards */
        .step-card {{
            background: #1e293b;
            border: 2px solid #334155;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            color: #e2e8f0 !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.75rem;
            min-height: 180px;
            justify-content: center;
        }}
        
        .step-card:hover {{
            border-color: #0cc0df;
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(12, 192, 223, 0.15);
        }}
        
        .step-card h3 {{
            color: #f1f5f9 !important;
            margin: 0;
            font-size: 1.25rem;
        }}
        
        .step-card p {{
            color: #cbd5e1 !important;
            margin: 0;
            font-size: 0.95rem;
            line-height: 1.4;
        }}
        
        /* OUTPUT - WHITE BACKGROUND (professional) */
        .clean-output {{
            background: white !important;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 2rem;
            margin: 1.5rem 0 3rem 0;  /* Extra bottom margin */
            line-height: 1.6;
            color: #1f2937 !important;
            font-family: 'Segoe UI', 'SF Pro Text', -apple-system, sans-serif;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .clean-output h3 {{
            color: #111827 !important;
            font-weight: 600;
            margin: 1.5rem 0 0.75rem 0;
        }}
        
        .clean-output p {{
            color: #374151 !important;
        }}
        
        /* Buttons stay on top */
        button, a[role="button"] {{
            position: relative;
            z-index: 10;
        }}
        
        /* Cards */
        article, .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
        }}
    </style>
</head>
<body>
    <!-- FULL WIDTH NAV -->
    <nav class="app-nav">
        <div class="nav-inner">
            <div>
                <a href="/" style="color: #0cc0df; font-size: 1.2rem;">
                    <i class="fa-solid fa-hat-wizard"></i> <strong>Prompts Alchemy</strong>
                </a>
            </div>
            <div>
                <a href="/" style="margin-right: 1.5rem;"><i class="fas fa-home"></i> Home</a>
                <a href="/dashboard" style="margin-right: 1.5rem;"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                <a href="/prompt-wizard"><i class="fas fa-magic"></i> Wizards</a>
            </div>
        </div>
    </nav>
    
    <!-- MAIN CONTENT -->
    <main class="app-main">
        {content}
    </main>
    
    <!-- FOOTER -->
    <footer style="text-align: center; padding: 2rem; color: #64748b; border-top: 1px solid #334155; background: #1e293b;">
        <p>© 2024 Prompts Alchemy</p>
    </footer>
    
    <script>
        function copyPrompt() {{
            const output = document.querySelector('.clean-output');
            const text = output.innerText;
            navigator.clipboard.writeText(text).then(() => {{
                alert('Prompt copied to clipboard!');
            }});
        }}
    </script>
</body>
</html>'''
    
    return HTMLResponse(content=html)

def get_nav_html(current_page="home"):
    """Return consistent navigation HTML for all pages"""
    
    # Define which page is active
    active_styles = {
        "home": 'style="color: #0cc0df !important;"',
        "dashboard": 'style="color: #0cc0df !important;"', 
        "wizards": 'style="color: #0cc0df !important;"'
    }
    
    return f'''
    <nav class="container">
        <ul>
            <li>
                <strong>
                    <a href="/" style="color: #0cc0df; text-decoration: none;">
                        <i class="fa-solid fa-hat-wizard"></i> Prompts Alchemy
                    </a>
                </strong>
            </li>
        </ul>
        <ul>
            <li><a href="/" {active_styles.get("home", "")}><i class="fas fa-home"></i> Home</a></li>
            <li><a href="/dashboard" {active_styles.get("dashboard", "")}><i class="fas fa-tachometer-alt"></i> Dashboard</a></li>
            <li><a href="/prompt-wizard" {active_styles.get("wizards", "")}><i class="fas fa-magic"></i> Wizards</a></li>
        </ul>
    </nav>
    '''


# ========== DEEPSEEK API FUNCTION ==========
# Add this import at the top
import httpx
from functools import lru_cache

# Create a shared HTTP client with connection pooling
@lru_cache()
def get_http_client():
    """Get a shared HTTP client with connection pooling"""
    return httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        http2=True  # HTTP/2 can be faster
    )

async def call_deepseek_api_optimized(goal: str, audience: str, tone: str, platform: str, user_prompt: str) -> str:
    """Optimized async API call with better error handling and fallback"""
    
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    if not api_key:
        print("[DEBUG] No API key found, using fallback")
        return get_fallback_prompt(goal, audience, tone, platform, user_prompt)
    
    # Use shared client
    client = get_http_client()
    
    try:
        # Log start time for debugging
        import time
        start_time = time.time()
        
        response = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "PromptsAlchemy/1.0"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a prompt engineering expert. Create optimized prompts only."
                    },
                    {
                        "role": "user",
                        "content": f"""Please create an optimized prompt with these parameters:
                        - Goal: {goal}
                        - Audience: {audience}
                        - Platform: {platform}
                        - Tone: {tone}
                        
                        Original user request: {user_prompt}
                        
                        Create a prompt that the user can copy/paste directly into {platform.capitalize()}.
                        Format it clearly with sections."""
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500,  # Reduced for faster response
                "stream": False  # Ensure not streaming
            }
        )
        
        elapsed = time.time() - start_time
        print(f"[DEBUG] API call took {elapsed:.2f} seconds, status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            return content
        else:
            print(f"[ERROR] API returned {response.status_code}: {response.text[:200]}")
            return get_fallback_prompt(goal, audience, tone, platform, user_prompt)
            
    except httpx.TimeoutException:
        print("[ERROR] API timeout")
        return get_fallback_prompt(goal, audience, tone, platform, user_prompt)
    except Exception as e:
        print(f"[ERROR] API call failed: {str(e)}")
        return get_fallback_prompt(goal, audience, tone, platform, user_prompt)
        
def get_fallback_prompt(goal, audience, tone, platform, user_prompt):
    """Generate a good fallback prompt when API fails"""
    return f"""## Role & Context
You are an expert AI assistant specializing in {goal}.

## Task & Objective
{user_prompt}

## Target Audience
{audience}

## Desired Tone
{tone}

## Response Requirements
1. Provide detailed, actionable information
2. Use clear headings and organization
3. Include examples when helpful
4. Maintain consistent {tone} tone throughout

## Format Guidelines
- Start with an engaging introduction
- Use bullet points for key points
- Include practical steps or examples
- End with a concise summary

## For {platform.capitalize()}:
Copy this prompt and paste into {platform.capitalize()} for optimal results."""

async def call_deepseek_api_async(goal: str, audience: str, tone: str, platform: str, user_prompt: str) -> str:
    """Async version - often works better with Render"""
    
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    if not api_key:
        return get_fallback_prompt(goal, audience, tone, platform, user_prompt)
    
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a Prompt Engineering Expert. Create prompt structures only."
                        },
                        {
                            "role": "user",
                            "content": f"Create prompt for: {user_prompt} (Goal: {goal}, Audience: {audience}, Tone: {tone}, Platform: {platform})"
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 600
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                return get_fallback_prompt(goal, audience, tone, platform, user_prompt)
                
        except (httpx.TimeoutException, httpx.ConnectError):
            return get_fallback_prompt(goal, audience, tone, platform, user_prompt)


# ========== HOME PAGE ==========
from fastapi.templating import Jinja2Templates

# Initialize templates
templates = Jinja2Templates(directory="templates")

@app.post("/api/auth/request-login")
async def request_login(email: str = Body(..., embed=True)):
    """Handle email submission for magic link login"""
    
    # Basic validation
    if "@" not in email:
        return JSONResponse(
            {"error": "Invalid email address"},
            status_code=400
        )
    
    # Connect to database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            # Create new user with 10 tokens
            cursor.execute(
                "INSERT INTO users (email, tokens) VALUES (?, 10)",
                (email,)
            )
        
        # Generate magic link token (for now, just log it)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
        
        cursor.execute(
            """INSERT INTO login_tokens (token, email, expires_at) 
               VALUES (?, ?, ?)""",
            (token, email, expires_at)
        )
        
        conn.commit()
        
        # In production: Send email with magic link
        # For now, just log it
        print(f"🔐 Login token for {email}: {token}")
        print(f"📧 Magic link: https://yourdomain.com/api/auth/login?token={token}")
        
        return {
            "success": True,
            "message": "Check your email for a login link",
            "demo_token": token  # For demo only
        }
        
    except Exception as e:
        conn.rollback()
        return JSONResponse(
            {"error": "Database error", "detail": str(e)},
            status_code=500
        )
    finally:
        conn.close()


@app.get("/")
async def home(request: Request):  # <-- Add 'request' parameter
    return templates.TemplateResponse(
        "frontpage.html", 
        {"request": request}  # <-- Required by FastAPI templates
    )

@app.get("/dashboard")
async def dashboard(request: Request, session_token: str = Cookie(None)):
    print(f"📊 Dashboard accessed. Session token: {session_token}")
    
    user = get_current_user(session_token)
    print(f"📊 User: {user}")
    
    
    if user:
        # User is logged in
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Prompts Alchemy</title>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                /* Your dark theme CSS */
                body {{ background: #0f172a; color: #e2e8f0; }}
                .card {{ background: #1e293b; border: 1px solid #334155; }}
            </style>
        </head>
        <body>
            <!-- Navigation with user info -->
            <nav class="app-nav">
                <div class="nav-inner">
                    <div>
                        <a href="/" style="color: #0cc0df;">
                            <i class="fa-solid fa-hat-wizard"></i> Prompts Alchemy
                        </a>
                    </div>
                    <div>
                        <span style="color: #0cc0df; margin-right: 1.5rem;">
                            <i class="fas fa-user"></i> {user['email']}
                        </span>
                        <span style="color: #fbbf24; margin-right: 1.5rem;">
                            <i class="fas fa-coins"></i> {user['tokens']} tokens
                        </span>
                        <a href="/" style="margin-right: 1.5rem;">Home</a>
                        <a href="/dashboard">Dashboard</a>
                    </div>
                </div>
            </nav>
            
            <main class="app-main">
                <h1>Your Dashboard</h1>
                
                <!-- Real user stats -->
                <div class="grid" style="grid-template-columns: repeat(3, 1fr); gap: 2rem; margin: 3rem 0;">
                    <div class="card" style="text-align: center;">
                        <h3><i class="fas fa-coins"></i> Tokens</h3>
                        <p style="font-size: 2.5rem; font-weight: bold; color: #0cc0df;">{user['tokens']}</p>
                        <p style="color: #94a3b8;">Remaining this month</p>
                    </div>
                    
                    <div class="card" style="text-align: center;">
                        <h3><i class="fas fa-user"></i> Account</h3>
                        <p style="color: #cbd5e1; margin: 1rem 0;">{user['email']}</p>
                        <button onclick="logout()" style="background: #ef4444; color: white; padding: 0.5rem 1rem; border: none; border-radius: 6px; cursor: pointer;">
                            <i class="fas fa-sign-out-alt"></i> Logout
                        </button>
                    </div>
                    
                    <div class="card" style="text-align: center;">
                        <h3><i class="fas fa-crown"></i> Plan</h3>
                        <p style="font-size: 1.5rem; font-weight: bold; color: #f1f5f9;">Free Tier</p>
                        <p style="color: #94a3b8;">10 tokens/month</p>
                        <a href="#pricing" style="color: #0cc0df;">Upgrade</a>
                    </div>
                </div>
                
                <!-- Rest of dashboard... -->
            </main>
            
            <script>
                function logout() {{
                    document.cookie = "session_token=; path=/; max-age=0;";
                    window.location.href = "/";
                }}
            </script>
        </body>
        </html>
        """
    else:
        # User not logged in - show public dashboard
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - Prompts Alchemy</title>
            <!-- Same CSS as before -->
        </head>
        <body>
            <!-- Public dashboard HTML (what you already have) -->
        </body>
        </html>
        """
    
    return HTMLResponse(content=html)


@app.get("/logout")
async def logout():
    """Log out user by clearing session cookie"""
    response = HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Logged Out - Prompts Alchemy</title>
            <style>
                body { background: #0f172a; color: white; font-family: sans-serif; padding: 3rem; text-align: center; }
                .card { background: #1e293b; padding: 2rem; border-radius: 12px; max-width: 500px; margin: 2rem auto; }
            </style>
            <script>
                // Clear session cookie
                document.cookie = "session_token=; path=/; max-age=0;";
                
                // Redirect after 1 second
                setTimeout(function() {
                    window.location.href = "/";
                }, 1000);
            </script>
        </head>
        <body>
            <div class="card">
                <h1>✅ Logged Out</h1>
                <p>You have been successfully logged out.</p>
                <p>Redirecting to homepage...</p>
                <p><a href="/" style="color: #0cc0df;">Click here if not redirected</a></p>
            </div>
        </body>
        </html>
    """)
    
    # Clear cookie server-side too
    response.delete_cookie("session_token")
    return response


@app.get("/prompt-wizard")
async def prompt_wizard_landing(request: Request):
    """Landing page with auth integration"""
    
    html = f'''
    <!DOCTYPE html>
<html>
<head>
    <title>Prompt Wizard - Prompts Alchemy</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        /* DARK THEME */
        body {{
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
        }}
        
        /* FULL-WIDTH NAV */
        .app-nav {{
            background: #1e293b;
            border-bottom: 1px solid #334155;
            padding: 1rem 0;
            width: 100%;
        }}
        
        .nav-inner {{
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 1rem;
        }}
        
        .app-nav a {{
            color: #cbd5e1;
            text-decoration: none;
        }}
        
        .app-nav a:hover {{
            color: #0cc0df;
        }}
        
        /* MAIN CONTENT */
        .app-main {{
            max-width: 800px;
            margin: 0 auto;
            padding: 3rem 1rem;
        }}
        
        /* Cards */
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 2rem;
            margin: 1.5rem 0;
        }}
        
        /* Steps visualization */
        .step-visual {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 0.5rem;
            margin: 2rem 0;
        }}
        
        .step-circle {{
            text-align: center;
            padding: 0.75rem 0.5rem;
            background: #334155;
            border-radius: 8px;
            transition: all 0.3s ease;
        }}
        
        .step-circle:hover {{
            background: #475569;
            transform: translateY(-2px);
        }}
        
        .step-circle .number {{
            font-size: 1.25rem;
            font-weight: bold;
            color: #0cc0df;
            margin-bottom: 0.25rem;
        }}
        
        .step-circle .label {{
            font-size: 0.8rem;
            color: #cbd5e1;
        }}
        
        /* CTA Button */
        .cta-button {{
            background: linear-gradient(135deg, #0cc0df, #00d9ff);
            color: white;
            padding: 1rem 3rem;
            border: none;
            border-radius: 10px;
            font-size: 1.2rem;
            font-weight: bold;
            cursor: pointer;
            display: inline-block;
            text-decoration: none;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .cta-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(12, 192, 223, 0.3);
            color: white;
        }}
        
        /* Token badge */
        .token-badge {{
            background: rgba(12, 192, 223, 0.1);
            color: #0cc0df;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            display: inline-block;
            margin: 1rem 0;
            border: 1px solid rgba(12, 192, 223, 0.3);
        }}
        
        /* Modal */
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        
        .modal-content {{
            background: #1e293b;
            padding: 2.5rem;
            border-radius: 12px;
            max-width: 400px;
            width: 90%;
            border: 1px solid #334155;
        }}
    </style>
</head>
<body>
    <!-- FULL WIDTH NAV -->
    <nav class="app-nav">
        <div class="nav-inner">
            <div>
                <a href="/" style="color: #0cc0df; font-size: 1.2rem;">
                    <i class="fa-solid fa-hat-wizard"></i> <strong>Prompts Alchemy</strong>
                </a>
            </div>
            <div>
                <a href="/" style="margin-right: 1.5rem;"><i class="fas fa-home"></i> Home</a>
                <a href="/dashboard" style="margin-right: 1.5rem;"><i class="fas fa-tachometer-alt"></i> Dashboard</a>
                <a href="/prompt-wizard" style="color: #0cc0df;"><i class="fas fa-magic"></i> Wizards</a>
            </div>
        </div>
    </nav>
    
    <!-- MAIN CONTENT -->
    <main class="app-main">
        <header style="text-align: center; margin-bottom: 3rem;">
            <h1 style="font-size: 3rem; margin-bottom: 1rem;">
                <i class="fas fa-hat-wizard"></i> Prompt Wizard
            </h1>
            <p style="font-size: 1.2rem; color: #94a3b8; max-width: 600px; margin: 0 auto;">
                Transform simple ideas into professional AI prompts in 6 easy steps
            </p>
        </header>
        
        <!-- How it works -->
        <div class="card">
            <h2><i class="fas fa-play-circle"></i> How It Works</h2>
            <p>Just click through 6 simple choices, and AI builds your perfect prompt:</p>
            
            <div class="step-visual">
                <div class="step-circle">
                    <div class="number">1</div>
                    <div class="label">Goal</div>
                </div>
                <div class="step-circle">
                    <div class="number">2</div>
                    <div class="label">Audience</div>
                </div>
                <div class="step-circle">
                    <div class="number">3</div>
                    <div class="label">Platform</div>
                </div>
                <div class="step-circle">
                    <div class="number">4</div>
                    <div class="label">Style</div>
                </div>
                <div class="step-circle">
                    <div class="number">5</div>
                    <div class="label">Tone</div>
                </div>
                <div class="step-circle">
                    <div class="number">6</div>
                    <div class="label">Your Prompt</div>
                </div>
            </div>
            
            <div style="background: #0f172a; padding: 1.5rem; border-radius: 8px; margin-top: 2rem; border-left: 4px solid #0cc0df;">
                <h4 style="color: #0cc0df; margin-top: 0;"><i class="fas fa-star"></i> Example Output:</h4>
                <p style="margin: 0.5rem 0; color: #cbd5e1;">
                    <strong>Professional prompt for ChatGPT:</strong><br>
                    "You are an expert content strategist. Create a detailed blog post outline about sustainable energy for business executives. Use a professional tone with actionable insights..."
                </p>
            </div>
        </div>
        
        <!-- Token info -->
        <div class="card" style="text-align: center;">
            <h3><i class="fas fa-coins"></i> Token Cost</h3>
            <div class="token-badge">
                <i class="fas fa-bolt"></i> 2 tokens per prompt
            </div>
            <p style="color: #94a3b8; margin: 1rem 0;">
                New users start with <strong>10 free tokens</strong> (5 prompts!)<br>
                No credit card required to start.
            </p>
        </div>
        
        <!-- CTA -->
        <div style="text-align: center; margin-top: 3rem;">
            <h2>Ready to create your perfect prompt?</h2>
            <button onclick="startWizard()" class="cta-button">
                <i class="fas fa-play"></i> Start Prompt Wizard
            </button>
            <p style="color: #94a3b8; margin-top: 1rem;">
                <small>You'll be prompted to sign in or create an account</small>
            </p>
        </div>
    </main>
    
    <!-- FOOTER -->
    <footer style="text-align: center; padding: 2rem; color: #64748b; border-top: 1px solid #334155; background: #1e293b; margin-top: 4rem;">
        <p>© 2024 Prompts Alchemy • <a href="/terms" style="color: #94a3b8;">Terms</a> • <a href="/privacy" style="color: #94a3b8;">Privacy</a></p>
    </footer>
    
    <!-- AUTH MODAL -->
    <div id="authModal" class="modal">
        <div class="modal-content">
            <h2 style="margin-top: 0; color: #f1f5f9;"><i class="fas fa-envelope"></i> Sign In to Continue</h2>
            <p style="color: #94a3b8; margin-bottom: 1.5rem;">
                Enter your email to start using Prompt Wizard. We'll send you a magic link.
            </p>
            
            <form id="authForm" onsubmit="submitAuth(event)">
                <input type="email" id="authEmail" placeholder="you@example.com" required
                       style="width: 100%; padding: 0.75rem; margin-bottom: 1rem; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 6px;">
                
                <div style="display: flex; gap: 0.5rem;">
                    <button type="submit" style="flex: 1; padding: 0.75rem; background: #0cc0df; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">
                        Send Magic Link
                    </button>
                    <button type="button" onclick="hideAuthModal()" style="padding: 0.75rem; background: transparent; color: #94a3b8; border: 1px solid #334155; border-radius: 6px; cursor: pointer;">
                        Cancel
                    </button>
                </div>
            </form>
            
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 1.5rem;">
                <i class="fas fa-shield-alt"></i> No password needed. We email you a secure login link.
            </p>
        </div>
    </div>
    
    
<script>
    // Submit auth form
    async function submitAuth(event) {{
        event.preventDefault();
        const email = document.getElementById('authEmail').value;
        
        if (!email || !email.includes('@')) {{
            alert('Please enter a valid email address.');
            return;
        }}
        
        // Show loading state
        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Sending...';
        submitBtn.disabled = true;
        
        try {{
            // Send email to backend
            const response = await fetch('/api/auth/request-login', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ email: email }})
            }});
            
            const result = await response.json();
            
            if (response.ok) {{
                // Success - show confirmation
                hideAuthModal();
                
                // SHOW MAGIC LINK FOR DEMO
                const magicLink = window.location.origin + '/api/auth/login?token=' + result.demo_token;
                alert('For demo: Click this link to login:\\n\\n' + magicLink + '\\n\\n(In production, this would be emailed to you.)');
                
                // Store email in localStorage for demo
                localStorage.setItem('user_email', email);
                
            }} else {{
                alert('Error: ' + (result.detail || 'Something went wrong'));
            }}
            
        }} catch (error) {{
            alert('Network error. Please try again.');
        }} finally {{
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }}
    }}
</script>
</body>
</html>'''
    
    return HTMLResponse(content=html)


# ========== STEP 1: GOAL SELECTION ==========
@app.get("/prompt-wizard/step/1")
async def step1():
    goals = [
        ("explain", "Explain", "Break down complex topics"),
        ("create", "Create", "Generate content or ideas"),
        ("analyze", "Analyze", "Review data or text"),
        ("solve", "Solve", "Find solutions to problems"),
        ("brainstorm", "Brainstorm", "Generate possibilities"),
        ("edit", "Edit/Improve", "Refine existing content"),
    ]
    
    goal_cards = ""
    for value, label, description in goals:
        # Get icon from ICON_MAP
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        goal_cards += f'''
        <a href="/prompt-wizard/step/2?goal={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #666;">{label}</h3>
            <p style="margin: 0; color: #444; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 1: What's your goal?</h1>
                <p>What do you want the AI to help you with?</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step active">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {goal_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/" class="secondary">
                <i class="fas fa-home"></i> Back to Home
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 1: Goal Selection", content, step=1)
# ========== STEP 2: AUDIENCE SELECTION ==========
@app.get("/prompt-wizard/step/2")
async def step2(goal: str = Query("explain")):
    audiences = [
        ("general", "General Public", "Anyone without specific expertise"),
        ("experts", "Experts", "People with deep knowledge"),
        ("students", "Students", "Learners at various levels"),
        ("business", "Business", "Professionals, clients, stakeholders"),
        ("technical", "Technical", "Developers, engineers, scientists"),
        ("beginners", "Beginners", "New to the topic, need basics"),
    ]
    
    audience_cards = ""
    for value, label, description in audiences:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        audience_cards += f'''
        <a href="/prompt-wizard/step/3?goal={goal}&audience={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 2: Who is your audience?</h1>
                <p>Who will read or use this output?</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step active">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected Goal:</strong> {goal.capitalize()}</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {audience_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/1" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 1
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 2: Audience Selection", content, step=2)

# ========== STEP 3: PLATFORM SELECTION ==========
@app.get("/prompt-wizard/step/3")
async def step3(goal: str = Query("explain"), audience: str = Query("general")):
    platforms = [
        ("chatgpt", "ChatGPT", "OpenAI's conversational AI"),
        ("claude", "Claude", "Anthropic's thoughtful assistant"),
        ("gemini", "Gemini", "Google's multimodal AI"),
        ("deepseek", "DeepSeek", "DeepSeek AI models"),
        ("perplexity", "Perplexity", "Research-focused with citations"),
        ("copilot", "GitHub Copilot", "Code completion and generation"),
    ]
    
    platform_cards = ""
    for value, label, description in platforms:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        platform_cards += f'''
        <a href="/prompt-wizard/step/4?goal={goal}&audience={audience}&platform={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 3: Which AI platform?</h1>
                <p>Where will you use this prompt?</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step active">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected:</strong> {goal.capitalize()} for {audience.capitalize()} audience</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {platform_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/2?goal={goal}" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 2
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 3: Platform Selection", content, step=3)

# ========== STEP 4: STYLE SELECTION ==========
@app.get("/prompt-wizard/step/4")
async def step4(goal: str = Query("explain"), audience: str = Query("general"), platform: str = Query("chatgpt")):
    styles = [
        ("direct", "Direct", "Straight to the point"),
        ("structured", "Structured", "Organized with headings"),
        ("creative", "Creative", "Imaginative, free-flowing"),
        ("technical", "Technical", "Detailed with specifications"),
        ("conversational", "Conversational", "Natural, chat-like"),
        ("step-by-step", "Step-by-Step", "Guided instructions"),
    ]
    
    style_cards = ""
    for value, label, description in styles:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        style_cards += f'''
        <a href="/prompt-wizard/step/5?goal={goal}&audience={audience}&platform={platform}&style={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 4: What style do you prefer?</h1>
                <p>How should the AI structure its response?</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step active">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected:</strong> {goal.capitalize()} for {audience.capitalize()} on {platform.capitalize()}</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {style_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/3?goal={goal}&audience={audience}" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 3
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 4: Style Selection", content, step=4)

# ========== STEP 5: TONE SELECTION ==========
@app.get("/prompt-wizard/step/5")
async def step5(goal: str = Query("explain"), audience: str = Query("general"), 
                platform: str = Query("chatgpt"), style: str = Query("direct")):
    tones = [
        ("professional", "Professional", "Formal, business-appropriate"),
        ("friendly", "Friendly", "Warm, approachable, casual"),
        ("authoritative", "Authoritative", "Confident, expert-like"),
        ("enthusiastic", "Enthusiastic", "Energetic, passionate"),
        ("neutral", "Neutral", "Objective, unbiased"),
        ("humorous", "Humorous", "Funny, lighthearted"),
    ]
    
    tone_cards = ""
    for value, label, description in tones:
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        tone_cards += f'''
        <a href="/prompt-wizard/step/6?goal={goal}&audience={audience}&platform={platform}&style={style}&tone={value}" class="step-card">
            <div class="step-icon">
                <i class="{icon_class}"></i>
            </div>
            <h3 style="margin: 0; color: #333;">{label}</h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">{description}</p>
        </a>
        '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 5: What tone should it use?</h1>
                <p>The overall mood or attitude of the response</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step active">5. Tone</div>
                    <div class="progress-step">6. Prompt</div>
                </div>
            </div>
            
            <div class="card secondary" style="margin: 1rem auto; max-width: 600px; text-align: left;">
                <p><strong>Selected:</strong> {goal.capitalize()} for {audience.capitalize()} on {platform.capitalize()} in {style} style</p>
            </div>
        </header>
        
        <div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 1rem;">
            {tone_cards}
        </div>
        
        <div style="text-align: center; margin-top: 3rem;">
            <a href="/prompt-wizard/step/4?goal={goal}&audience={audience}&platform={platform}" class="secondary">
                <i class="fas fa-arrow-left"></i> Back to Step 4
            </a>
        </div>
    </article>
    '''
    
    return layout("Step 5: Tone Selection", content, step=5)

# ========== STEP 6: PROMPT INPUT ==========
@app.get("/prompt-wizard/step/6")
async def step6(goal: str = Query("explain"), audience: str = Query("general"), 
                platform: str = Query("chatgpt"), style: str = Query("direct"), 
                tone: str = Query("professional")):
    
    # Create a summary of selections
    selections = f'''
    <div class="card secondary" style="margin: 1rem 0 2rem 0;">
        <div class="grid" style="grid-template-columns: repeat(5, 1fr); gap: 0.5rem; text-align: center;">
            <div>
                <small>Goal</small><br>
                <strong>{goal.capitalize()}</strong>
            </div>
            <div>
                <small>Audience</small><br>
                <strong>{audience.capitalize()}</strong>
            </div>
            <div>
                <small>Platform</small><br>
                <strong>{platform.capitalize()}</strong>
            </div>
            <div>
                <small>Style</small><br>
                <strong>{style.replace('-', ' ').title()}</strong>
            </div>
            <div>
                <small>Tone</small><br>
                <strong>{tone.capitalize()}</strong>
            </div>
        </div>
    </div>
    '''
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1>Step 6: Enter Your Prompt</h1>
                <p>Type your original prompt, and AI will optimize it</p>
            </hgroup>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
                <div class="progress-steps">
                    <div class="progress-step">1. Goal</div>
                    <div class="progress-step">2. Audience</div>
                    <div class="progress-step">3. Platform</div>
                    <div class="progress-step">4. Style</div>
                    <div class="progress-step">5. Tone</div>
                    <div class="progress-step active">6. Prompt</div>
                </div>
            </div>
            
            {selections}
        </header>
        
        <form id="promptForm" action="/prompt-wizard/generate" method="get" 
              onsubmit="showLoading(); return true;">
            <!-- Hidden fields to pass selections -->
            <input type="hidden" name="goal" value="{goal}">
            <input type="hidden" name="audience" value="{audience}">
            <input type="hidden" name="platform" value="{platform}">
            <input type="hidden" name="style" value="{style}">
            <input type="hidden" name="tone" value="{tone}">
            
            <div class="grid">
                <div>
                    <label for="user_prompt">
                        <h3>Your Original Prompt:</h3>
                        <p>Type what you'd normally ask the AI</p>
                    </label>
                    <textarea 
                        id="user_prompt" 
                        name="prompt" 
                        rows="8" 
                        placeholder="Example: 'Explain quantum computing like I'm 5' or 'Write a blog post about climate change'"
                        required
                        style="font-size: 1rem; padding: 1rem;"
                    ></textarea>
                </div>
                
                <div>
                    <h3>Tips for Great Prompts:</h3>
                    <div class="card" style="height: 100%;">
                        <ul style="margin: 0; padding-left: 1.5rem;">
                            <li>Be specific about what you want</li>
                            <li>Include context when relevant</li>
                            <li>Mention length or format if needed</li>
                            <li>Add examples if helpful</li>
                            <li>Don't worry about perfection - AI will optimize it!</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <button type="submit" class="primary" style="padding: 1rem 2rem; font-size: 1.1rem;">
                    <i class="fas fa-magic"></i> Generate Optimized Prompt
                </button>
                
                <a href="/prompt-wizard/step/5?goal={goal}&audience={audience}&platform={platform}&style={style}" 
                   class="secondary" style="margin-left: 1rem;">
                    <i class="fas fa-arrow-left"></i> Back
                </a>
            </div>
        </form>
        
        <!-- Loading animation (hidden by default) -->
        <div id="loading" style="display: none; text-align: center; padding: 3rem;">
            <div class="loading-ai">
                <div class="loading-dots">
                    <span>●</span>
                    <span>●</span>
                    <span>●</span>
                </div>
                <h3 style="margin-top: 1rem;">AI is working its magic...</h3>
                <p>This usually takes 10-30 seconds</p>
                <div class="progress-bar" style="max-width: 400px; margin: 2rem auto;">
                    <div class="progress-fill" style="width: 100%; animation: pulse 2s infinite;"></div>
                </div>
                <p><small>Do not refresh the page</small></p>
            </div>
        </div>
    </article>
    
    <script>
        function showLoading() {{
            // Show loading animation
            document.getElementById('loading').style.display = 'block';
            
            // Hide form
            document.getElementById('promptForm').style.display = 'none';
            
            // Scroll to loading
            document.getElementById('loading').scrollIntoView({{ behavior: 'smooth' }});
        }}
    </script>
    '''
    
    return layout("Step 6: Enter Your Prompt", content, step=6)

# ========== GENERATE FINAL PROMPT ==========
@app.get("/prompt-wizard/generate")
async def generate_prompt(
    goal: str = Query("explain"),
    audience: str = Query("general"),
    platform: str = Query("chatgpt"),
    style: str = Query("direct"),
    tone: str = Query("professional"),
    prompt: str = Query("")
):
    """Generate optimized prompt with improved error handling"""
    
    import logging
    import time
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Generating prompt for: {goal}, {audience}, {platform}")
    
    # Start timing
    start_time = time.time()
    
    # Try the optimized async call
    try:
        optimized_prompt = await call_deepseek_api_optimized(goal, audience, tone, platform, prompt)
        
        elapsed = time.time() - start_time
        logger.info(f"Prompt generated in {elapsed:.2f} seconds")
        
        # Log if we used fallback
        if "Role & Context" in optimized_prompt and "Target Audience" in optimized_prompt:
            logger.warning("Used fallback prompt (API may have failed)")
        
    except Exception as e:
        logger.error(f"Error generating prompt: {str(e)}")
        elapsed = time.time() - start_time
        optimized_prompt = get_fallback_prompt(goal, audience, tone, platform, prompt)
        optimized_prompt = f"## ⚠️ Note: Using fallback template\n\n{optimized_prompt}"
    
    # Convert to HTML
    formatted_html = markdown_to_clean_html(optimized_prompt)
    
    # Add performance info (for debugging)
    debug_info = ""
    if elapsed > 10:
        debug_info = f'<p style="color: #999; font-size: 0.8rem; text-align: center;">(Generation took {elapsed:.1f}s)</p>'
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1><i class="fas fa-check-circle"></i> Prompt Ready!</h1>
                <p>Your AI-optimized prompt for {platform.capitalize()}</p>
                {debug_info}
            </hgroup>
        </header>
        
        <div class="card">
            <h3>Your Original Prompt:</h3>
            <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <p style="margin: 0; color: #4b5563;">"{prompt}"</p>
            </div>
            
            <h3>AI-Optimized Prompt:</h3>
            
            <!-- CLEAN OUTPUT HERE -->
            <div class="clean-output">
                {formatted_html}
            </div>
            
            <div style="text-align: center; margin-top: 2rem;">
                <button onclick="copyPrompt()" class="primary" style="padding: 0.75rem 1.5rem;">
                    <i class="fas fa-copy"></i> Copy Prompt to Clipboard
                </button>
                
                <a href="/prompt-wizard/step/6?goal={goal}&audience={audience}&platform={platform}&style={style}&tone={tone}" 
                   class="secondary" style="margin-left: 1rem; padding: 0.75rem 1.5rem;">
                    <i class="fas fa-edit"></i> Try Another Prompt
                </a>
                
                <a href="/" class="secondary" style="margin-left: 1rem; padding: 0.75rem 1.5rem;">
                    <i class="fas fa-home"></i> Start Over
                </a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 3rem; color: #666; font-size: 0.9rem;">
            <p><i class="fas fa-lightbulb"></i> Tip: Paste this prompt directly into {platform.capitalize()} for best results</p>
        </div>
    </article>
    '''
    
    return layout("Generated Prompt", content, step=7)


import re

def markdown_to_clean_html(markdown_text: str) -> str:
    """
    Convert markdown to clean HTML with better contrast
    """
    if not markdown_text:
        return ""
    
    lines = markdown_text.strip().split('\n')
    html_parts = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Empty line = spacing
        if not line:
            html_parts.append('<div style="height: 1rem;"></div>')
            i += 1
            continue
        
        # Header level 1 (#) - Make it stand out
        if line.startswith('# ') and not line.startswith('##'):
            title = line[2:].strip()
            html_parts.append(f'<h2 style="font-weight: 700; font-size: 1.5rem; margin: 2rem 0 1rem 0; color: #222; border-bottom: 2px solid #0cc0df; padding-bottom: 0.5rem;">{title}</h2>')
        
        # Header level 2 (##)
        elif line.startswith('## '):
            title = line[3:].strip()
            html_parts.append(f'<h3 style="font-weight: 600; font-size: 1.3rem; margin: 1.75rem 0 0.75rem 0; color: #333;">{title}</h3>')
        
        # Header level 3 (###)
        elif line.startswith('### '):
            title = line[4:].strip()
            html_parts.append(f'<h4 style="font-weight: 600; font-size: 1.1rem; margin: 1.5rem 0 0.5rem 0; color: #444;">{title}</h4>')
        
        # Bold text (make it darker)
        elif '**' in line:
            # Process bold text with better contrast
            processed = line
            processed = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #222;">\1</strong>', processed)
            html_parts.append(f'<p style="margin-bottom: 1rem; line-height: 1.6; color: #444;">{processed}</p>')
        
        # Unordered list
        elif line.startswith('- ') or line.startswith('* '):
            list_items = []
            while i < len(lines) and (lines[i].startswith('- ') or lines[i].startswith('* ')):
                item = lines[i][2:].strip()
                # Process formatting within list items
                item = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #222;">\1</strong>', item)
                item = re.sub(r'`(.*?)`', r'<code style="background: #f5f5f5; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; color: #333;">\1</code>', item)
                list_items.append(f'<li style="margin-bottom: 0.5rem; color: #444; line-height: 1.5;">{item}</li>')
                i += 1
            
            html_parts.append(f'<ul style="margin: 1rem 0 1.5rem 1.5rem; color: #444;">{"".join(list_items)}</ul>')
            continue
        
        # Ordered list
        elif re.match(r'^\d+[\.\)] ', line):
            list_items = []
            counter = 1
            while i < len(lines) and re.match(r'^\d+[\.\)] ', lines[i]):
                item = re.sub(r'^\d+[\.\)] ', '', lines[i]).strip()
                item = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #222;">\1</strong>', item)
                item = re.sub(r'`(.*?)`', r'<code style="background: #f5f5f5; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; color: #333;">\1</code>', item)
                list_items.append(f'<li style="margin-bottom: 0.5rem; color: #444; line-height: 1.5;"><span style="color: #666; margin-right: 0.5rem;">{counter}.</span>{item}</li>')
                i += 1
                counter += 1
            
            html_parts.append(f'<ol style="margin: 1rem 0 1.5rem 1.5rem; color: #444;">{"".join(list_items)}</ol>')
            continue
        
        # Regular paragraph (with better contrast)
        else:
            processed_line = line
            # Bold
            processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: #222;">\1</strong>', processed_line)
            # Italic
            processed_line = re.sub(r'\*(.*?)\*', r'<em style="color: #444;">\1</em>', processed_line)
            # Inline code
            processed_line = re.sub(r'`(.*?)`', r'<code style="background: #f5f5f5; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; color: #333;">\1</code>', processed_line)
            
            html_parts.append(f'<p style="margin-bottom: 1rem; line-height: 1.6; color: #444;">{processed_line}</p>')
        
        i += 1
    
    return '\n'.join(html_parts)

@app.get("/debug/api")
async def debug_api():
    """Check if API key is working"""
    
    # Get API key
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    api_key_set = bool(api_key)
    
    # Show preview (last 4 chars for security)
    api_preview = "Not set" if not api_key_set else f"...{api_key[-4:]}"
    
    # Test the API
    test_result = {}
    if api_key_set:
        try:
            # Simple test call
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            test_data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": "Say 'API test successful'"}
                ],
                "max_tokens": 10
            }
            
            import requests
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers=headers,
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                test_result = {
                    "status": "✅ Working",
                    "response": response.json()["choices"][0]["message"]["content"]
                }
            else:
                test_result = {
                    "status": f"❌ Error {response.status_code}",
                    "response": response.text[:200]
                }
                
        except Exception as e:
            test_result = {
                "status": f"❌ Exception",
                "error": str(e)
            }
    else:
        test_result = {"status": "❌ No API key to test"}
    
    return {
        "api_key_set": api_key_set,
        "api_key_preview": api_preview,
        "api_test": test_result,
        "environment": os.getenv("APP_ENV", "unknown"),
        "render_service": os.getenv("RENDER_SERVICE_ID", "Not on Render"),
        "all_env_vars": dict(os.environ)  # Shows all environment variables
    }

@app.get("/debug/network")
async def debug_network():
    """Debug network connectivity from Render"""
    import socket
    import time
    import requests
    from datetime import datetime
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test 1: DNS resolution
    start = time.time()
    try:
        ip = socket.gethostbyname('api.deepseek.com')
        elapsed = time.time() - start
        results["tests"]["dns"] = {
            "status": "✅",
            "time": f"{elapsed:.2f}s",
            "ip": ip
        }
    except Exception as e:
        results["tests"]["dns"] = {
            "status": "❌",
            "error": str(e)
        }
    
    # Test 2: Simple HTTP request
    start = time.time()
    try:
        resp = requests.get('https://httpbin.org/status/200', timeout=5)
        elapsed = time.time() - start
        results["tests"]["httpbin"] = {
            "status": "✅",
            "time": f"{elapsed:.2f}s",
            "status_code": resp.status_code
        }
    except Exception as e:
        results["tests"]["httpbin"] = {
            "status": "❌",
            "error": str(e)
        }
    
    # Test 3: DeepSeek API endpoint check (no key)
    start = time.time()
    try:
        resp = requests.get('https://api.deepseek.com/', timeout=5)
        elapsed = time.time() - start
        results["tests"]["deepseek_root"] = {
            "status": "✅",
            "time": f"{elapsed:.2f}s",
            "status_code": resp.status_code
        }
    except Exception as e:
        results["tests"]["deepseek_root"] = {
            "status": "❌",
            "error": str(e)
        }
    
    # Return as JSON
    from fastapi.responses import JSONResponse
    return JSONResponse(content=results)

@app.get("/test/simple")
async def test_simple():
    """Simple test that doesn't call external API"""
    return {
        "status": "ok",
        "message": "App is running",
        "timestamp": time.time(),
        "render_service": os.getenv("RENDER_SERVICE_ID", "local")
    }


@app.get("/check-api-status")
async def check_api_status():
    """Check if DeepSeek API key has credits"""
    import requests
    
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    if not api_key:
        return {
            "status": "❌ No API key found",
            "error": "DEEPSEEK_API_KEY environment variable not set"
        }
    
    try:
        # Try a minimal request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Say 'API test'"}],
            "max_tokens": 5
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "status": "✅ API is working",
                "response": response.json()["choices"][0]["message"]["content"],
                "tokens_used": response.json()["usage"]["total_tokens"]
            }
        elif response.status_code == 401:
            return {
                "status": "❌ Unauthorized",
                "error": "Invalid API key or expired"
            }
        elif response.status_code == 429:
            return {
                "status": "❌ Rate limited",
                "error": "Too many requests or quota exceeded"
            }
        else:
            return {
                "status": f"❌ Error {response.status_code}",
                "error": response.text[:200]
            }
            
    except requests.exceptions.Timeout:
        return {"status": "❌ Timeout", "error": "Request timed out"}
    except Exception as e:
        return {"status": "❌ Exception", "error": str(e)}


# ========== RUN THE APP ==========
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    # Debug info
    print("=" * 50)
    print(f"🚀 STARTING PROMPT WIZARD")
    print(f"📦 Python path: {sys.path}")
    print(f"🌐 Host: 0.0.0.0")
    print(f"🔌 Port: {port}")
    print(f"🔑 API Key exists: {bool(os.getenv('DEEPSEEK_API_KEY', ''))}")
    print("=" * 50)
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port,
            log_level="debug"
        )
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        print(f"📝 Error type: {type(e)}")
        import traceback
        traceback.print_exc()
    print(f"✨ Step 1: http://localhost:{port}/prompt-wizard/step/1")
    print(f"🎨 Font Awesome Icons Enabled")
    print(f"📋 Fixed copy button positioning")
    uvicorn.run(app, host="0.0.0.0", port=port)
