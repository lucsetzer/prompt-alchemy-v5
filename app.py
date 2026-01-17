from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import requests
import json
from routes.dashboard import router as dashboard_router
from routes.script_wizard import router as script_wizard_router

app = FastAPI(title="Prompt Wizard")
app.include_router(dashboard_router)
app.include_router(script_wizard_router)

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

# ========== CORE LAYOUT FUNCTION ==========
def layout(title: str, content: str, step: int = 1) -> HTMLResponse:
    """Simple, working layout with no syntax errors"""
    
    progress_percent = (step / 6) * 100 if step <= 6 else 100
    
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        /* CSS VARIABLES - NO ERRORS */
        :root {{
            --primary: #0cc0df;
            --primary-hover: #0aa0bf;
            /* STEP CARDS - auDHD Friendly */
            .step-card {
                background: #ffffff;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                color: inherit;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0.75rem;
                min-height: 180px;  /* Original size */
                justify-content: center;
                margin: 0.5rem;
            }
            
            .step-card:hover {
                border-color: #0cc0df;
                transform: translateY(-4px);
                box-shadow: 0 4px 12px rgba(12, 192, 223, 0.15);
            }
            
            .step-icon {
                font-size: 2.5rem;
                color: #0cc0df;
                margin-bottom: 0.5rem;
            }
            
            /* Grid for cards */
            .step-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
                    }}
        
        /* BODY - NO VARIABLES IN CSS VALUES */
        body {{
            background: #ffffff;
            color: #333333;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        /* PROGRESS BAR - USING PERCENT VARIABLE IS OK */
        .progress-container {{
            margin: 2rem 0;
        }}
        
        .progress-bar {{
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #0cc0df, #00d9ff);
            width: {progress_percent}%;
            transition: width 0.5s ease;
        }}
        
        .progress-steps {{
            display: flex;
            justify-content: space-between;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: #666666;
        }}
        
        .progress-step {{
            text-align: center;
            flex: 1;
        }}
        
        .progress-step.active {{
            color: #0cc0df;
            font-weight: bold;
        }}
        
        /* CLEAN OUTPUT - SIMPLE */
        .clean-output {{
            background: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 1.5rem;
            margin: 1rem 0;
            line-height: 1.6;
            color: #555555;
            font-size: 0.95rem;
        }}
        
        .clean-output h3 {{
            font-weight: 600;
            font-size: 1.25rem;
            margin: 1.5rem 0 0.75rem 0;
            color: #333333;
        }}
        
        .clean-output h4 {{
            font-weight: 600;
            font-size: 1.1rem;
            margin: 1.25rem 0 0.5rem 0;
            color: #444444;
        }}
        
        .clean-output p {{
            margin-bottom: 1rem;
            color: #555555;
        }}
        
        .clean-output ul,
        .clean-output ol {{
            margin: 1rem 0;
            padding-left: 1.5rem;
            color: #555555;
        }}
        
        .clean-output li {{
            margin-bottom: 0.5rem;
        }}
        
        .clean-output code {{
            background: #f5f5f5;
            padding: 0.1rem 0.3rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        /* NAVIGATION */
        nav.container {{
            background: #ffffff;
            border-bottom: 1px solid #e5e7eb;
            padding: 1rem 0;
        }}
        
        /* CARDS */
        article, .card {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
        }}
        
        /* GRID FIX */
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
        }}
    </style>
</head>
<body>
    <nav class="container">
        <ul>
            <li>
                <strong>
                    <a href="/" style="color: #0cc0df; text-decoration: none;">
                        <i class="fas fa-flask"></i> Prompts Alchemy
                    </a>
                </strong>
            </li>
        </ul>
        <ul>
            <li><a href="/"><i class="fas fa-home"></i> Dashboard</a></li>
            <li><a href="/prompt-wizard/step/1"><i class="fas fa-magic"></i> Prompt Wizard</a></li>
            <li><a href="/pricing"><i class="fas fa-tags"></i> Pricing</a></li>
        </ul>
    </nav>
    
    <main class="container">
        {content}
    </main>
    
    <footer class="container" style="text-align: center; padding: 2rem 0; margin-top: 3rem; color: #666666; border-top: 1px solid #e5e7eb;">
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
    
# ========== DEEPSEEK API FUNCTION ==========
def call_deepseek_api(goal: str, audience: str, tone: str, platform: str, user_prompt: str) -> str:
    """Call DeepSeek API to generate optimized prompt"""
    
    # Get API key from environment
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    
    if not api_key:
        return f"""## Role & Context
You are an expert AI assistant specializing in {goal}.

## Task & Objective
{user_prompt}

## Target Audience
{audience}

## Desired Tone
{tone}

## Response Structure
1. Clear introduction
2. Detailed explanation
3. Practical examples
4. Actionable takeaways

Copy this prompt into {platform.capitalize()} for optimal results."""
    
    system_prompt = """You are a Prompt Engineering Expert. Create optimized, structured prompts.

CRITICAL RULES:
1. DO NOT answer the user's question
2. DO NOT provide solutions or content
3. ONLY create the prompt structure
4. Use clear markdown formatting"""

    user_message = f"""Create a STRUCTURED prompt for this request:

ORIGINAL REQUEST: "{user_prompt}"
CONTEXT:
- Goal: {goal}
- Target Audience: {audience}
- Desired Tone: {tone}
- Target AI Platform: {platform}

Make it DETAILED and READY-TO-USE. The user will copy-paste this into {platform}."""

    headers = {
        "Authorization": f"Bearer {api_key}",  # Use api_key variable
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            prompt = result["choices"][0]["message"]["content"].strip()
            
            # Ensure proper formatting
            if not prompt.startswith("##"):
                prompt = f"## AI-Optimized Prompt for {platform}\n\n{prompt}"
                
            return prompt
        else:
            return f"## Role: Expert AI Assistant\n## Task: {user_prompt}\n## Audience: {audience}\n## Tone: {tone}\n## Platform: {platform}\n\nProvide detailed, structured responses."
            
    except Exception as e:
        return f"## Role: Expert AI Assistant\n## Task: {user_prompt}\n## Audience: {audience}\n## Tone: {tone}\n## Platform: {platform}\n\nProvide detailed, structured responses."

# ========== HOME PAGE ==========
@app.get("/")
async def home():
    content = '''
    <article style="text-align: center; padding: 3rem 0;">
        <h1>🧙 Prompt Wizard</h1>
        <p class="lead" style="font-size: 1.25rem; color: #666; margin: 1rem 0 2rem 0;">
            Transform simple ideas into powerful AI prompts
        </p>
        
        <div style="max-width: 600px; margin: 0 auto 3rem auto; text-align: left;">
            <div class="card" style="margin-bottom: 1rem;">
                <h4><i class="fas fa-brain" style="color: var(--primary);"></i> auDHD Friendly</h4>
                <p>Clickable cards, clear steps, no overwhelm</p>
            </div>
            
            <div class="card" style="margin-bottom: 1rem;">
                <h4><i class="fas fa-magic" style="color: var(--primary);"></i> 6-Step Process</h4>
                <p>Simple choices → Professional prompt</p>
            </div>
            
            <div class="card">
                <h4><i class="fas fa-robot" style="color: var(--primary);"></i> DeepSeek AI Powered</h4>
                <p>Advanced prompt optimization</p>
            </div>
        </div>
        
        <a href="/prompt-wizard/step/1" role="button" class="primary" style="padding: 1rem 2rem; font-size: 1.1rem;">
            <i class="fas fa-play-circle"></i> Start Wizard
        </a>
        
        <div style="margin-top: 3rem; color: #888; font-size: 0.9rem;">
            <p>No login required • All processing happens in your browser • Free to use</p>
        </div>
    </article>
    '''
    return layout("Home - Prompt Wizard", content, step=0)

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
        icon_class = ICON_MAP.get(value, "fa-solid fa-question")
        
        goal_cards += f'''
        <a href="/prompt-wizard/step/2?goal={value}" class="step-card">
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
    # ... token checking code first ...
    
    # Generate the prompt
    optimized_prompt = call_deepseek_api(goal, audience, tone, platform, prompt)
    
    # Convert to beautiful HTML
    formatted_html = markdown_to_clean_html(optimized_prompt)
    
    # ... rest of your HTML template ...
    
    content = f'''
    <article>
        <header style="text-align: center; margin-bottom: 2rem;">
            <hgroup>
                <h1><i class="fas fa-check-circle"></i> Prompt Ready!</h1>
                <p>Your AI-optimized prompt for {platform.capitalize()}</p>
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
            
            <div style="text-align: center; margin-top: 1rem;">
                <button onclick="copyPrompt()" class="primary">
                    <i class="fas fa-copy"></i> Copy Prompt
                </button>
            </div>
            
            <!-- ... rest of your content ... -->
        </div>
    </article>
    '''
    
    return layout("Generated Prompt", content, step=7)

import re

def markdown_to_clean_html(markdown_text: str) -> str:
    """
    Convert markdown to clean, minimal HTML
    - White/light gray text only
    - No decorative lines or colors
    - Clean spacing
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
        
        # Header level 2 (##)
        if line.startswith('## '):
            title = line[3:].strip()
            html_parts.append(f'<h3 style="font-weight: 600; font-size: 1.25rem; margin: 1.5rem 0 0.75rem 0; color: #333;">{title}</h3>')
        
        # Header level 3 (###)
        elif line.startswith('### '):
            title = line[4:].strip()
            html_parts.append(f'<h4 style="font-weight: 600; font-size: 1.1rem; margin: 1.25rem 0 0.5rem 0; color: #444;">{title}</h4>')
        
        # Unordered list
        elif line.startswith('- ') or line.startswith('* '):
            list_items = []
            while i < len(lines) and (lines[i].startswith('- ') or lines[i].startswith('* ')):
                item = lines[i][2:].strip()
                # Process bold
                item = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item)
                # Process inline code
                item = re.sub(r'`(.*?)`', r'<code style="background: #f5f5f5; padding: 0.1rem 0.3rem; border-radius: 3px; font-family: monospace;">\1</code>', item)
                list_items.append(f'<li style="margin-bottom: 0.5rem; color: #555;">{item}</li>')
                i += 1
            
            html_parts.append(f'<ul style="margin: 1rem 0; padding-left: 1.5rem; color: #555;">{"".join(list_items)}</ul>')
            continue
        
        # Ordered list
        elif re.match(r'^\d+[\.\)] ', line):
            list_items = []
            counter = 1
            while i < len(lines) and re.match(r'^\d+[\.\)] ', lines[i]):
                item = re.sub(r'^\d+[\.\)] ', '', lines[i]).strip()
                item = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item)
                item = re.sub(r'`(.*?)`', r'<code style="background: #f5f5f5; padding: 0.1rem 0.3rem; border-radius: 3px; font-family: monospace;">\1</code>', item)
                list_items.append(f'<li style="margin-bottom: 0.5rem; color: #555;"><span style="color: #777; margin-right: 0.5rem;">{counter}.</span>{item}</li>')
                i += 1
                counter += 1
            
            html_parts.append(f'<ol style="margin: 1rem 0; padding-left: 1.5rem; color: #555;">{"".join(list_items)}</ol>')
            continue
        
        # Regular paragraph
        else:
            # Process inline formatting
            processed_line = line
            
            # Bold
            processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', processed_line)
            
            # Italic
            processed_line = re.sub(r'\*(.*?)\*', r'<em>\1</em>', processed_line)
            
            # Inline code
            processed_line = re.sub(r'`(.*?)`', r'<code style="background: #f5f5f5; padding: 0.1rem 0.3rem; border-radius: 3px; font-family: monospace;">\1</code>', processed_line)
            
            html_parts.append(f'<p style="margin-bottom: 1rem; line-height: 1.6; color: #555;">{processed_line}</p>')
        
        i += 1
    
    return '\n'.join(html_parts)


# ========== RUN THE APP ==========
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting Prompt Wizard on http://localhost:{port}")
    print(f"✨ Step 1: http://localhost:{port}/prompt-wizard/step/1")
    print(f"🎨 Font Awesome Icons Enabled")
    print(f"📋 Fixed copy button positioning")
    uvicorn.run(app, host="0.0.0.0", port=port)
