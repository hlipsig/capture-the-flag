"""
Production Customer Portal - Acme Corp
A legitimate-looking business web application protected by The Mirror.

This is the REAL application that The Mirror defends.
Attackers who scan this will get redirected to the honeypot.
Legitimate users who login correctly can find the production secret.
"""

import os
import secrets
import logging
from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Configure logging to include user-agent (for attack detection)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.after_request
def log_request(response):
    """Log requests in nginx-like format with user-agent for attack detection."""
    # Skip health check logging
    if request.path in ['/health', '/healthz', '/readyz']:
        return response

    # Log in format that log_detector can parse
    # Format: IP - - [timestamp] "METHOD path HTTP/1.1" status "user-agent"
    user_agent = request.headers.get('User-Agent', '-')
    timestamp = datetime.now().strftime('%d/%b/%Y:%H:%M:%S +0000')
    log_line = f'{request.remote_addr} - - [{timestamp}] "{request.method} {request.path} HTTP/1.1" {response.status_code} "{user_agent}"'
    logger.info(log_line)
    return response

# Production credentials (discoverable via OSINT/hints)
# Default user: admin / wealth_of_nations (same as honeypot decoy - intentional!)
VALID_USERS = {
    'admin': 'wealth_of_nations',
    'support': 'invisible_hand_1776',
    'demo': 'demo123'
}

# The REAL production secret (white-hat path victory)
PRODUCTION_FLAG = os.getenv('MASTER_API_KEY', 'flag{production_master_key_' + secrets.token_hex(4) + '}')

# Landing page template
LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Acme Corp - Customer Portal</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        header {
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            color: #667eea;
            margin: 0;
        }
        .tagline {
            color: #666;
            margin-top: 5px;
        }
        .nav {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .nav a {
            color: #667eea;
            text-decoration: none;
            margin-right: 20px;
            font-weight: 500;
        }
        .nav a:hover {
            text-decoration: underline;
        }
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature {
            border: 1px solid #e0e0e0;
            padding: 20px;
            border-radius: 5px;
        }
        .feature h3 {
            color: #667eea;
            margin-top: 0;
        }
        .cta {
            background: #667eea;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .cta:hover {
            background: #5568d3;
        }
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏢 Acme Corp</h1>
            <p class="tagline">Enterprise Solutions & Customer Portal</p>
        </header>

        <div class="nav">
            <a href="/">Home</a>
            <a href="/login">Customer Login</a>
            <a href="/about">About Us</a>
            <a href="/contact">Contact</a>
            <a href="/api">API Docs</a>
        </div>

        <h2>Welcome to Acme Corp Customer Portal</h2>
        <p>Access your account, manage orders, and integrate with our enterprise API.</p>

        <div class="features">
            <div class="feature">
                <h3>📊 Analytics Dashboard</h3>
                <p>Real-time insights into your business metrics and performance indicators.</p>
            </div>
            <div class="feature">
                <h3>🔐 Secure Access</h3>
                <p>Enterprise-grade authentication and data protection for your peace of mind.</p>
            </div>
            <div class="feature">
                <h3>🚀 API Integration</h3>
                <p>RESTful API with comprehensive documentation for seamless integration.</p>
            </div>
            <div class="feature">
                <h3>📞 24/7 Support</h3>
                <p>Our dedicated support team is available around the clock to assist you.</p>
            </div>
        </div>

        <a href="/login" class="cta">Access Customer Portal</a>

        <footer>
            <!-- Development note: Default credentials in source code -->
            <!-- TODO: Remove admin/wealth_of_nations before production! -->
            <p>&copy; 2026 Acme Corp. All rights reserved. | Server: web-prod-01 | Build: v2.1.4</p>
            <p style="font-size: 12px; color: #999;">For API access, contact your account manager</p>
        </footer>
    </div>
</body>
</html>
"""

# Login page template
LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login - Acme Corp</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            color: #667eea;
            margin-top: 0;
            text-align: center;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            background: #667eea;
            color: white;
            padding: 12px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover {
            background: #5568d3;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .back-link {
            text-align: center;
            margin-top: 20px;
        }
        .back-link a {
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 Customer Login</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <div class="back-link">
            <a href="/">← Back to Home</a>
        </div>
    </div>
</body>
</html>
"""

# Dashboard (authenticated area)
DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - Acme Corp</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .topbar {
            background: #667eea;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .container {
            max-width: 1200px;
            margin: 20px auto;
            padding: 0 20px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        .stat {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat h3 {
            margin: 0;
            font-size: 32px;
        }
        .stat p {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
        .nav-links a {
            color: white;
            text-decoration: none;
            margin-left: 20px;
        }
        .nav-links a:hover {
            text-decoration: underline;
        }
        a.logout {
            color: #ff6b6b;
        }
    </style>
</head>
<body>
    <div class="topbar">
        <div>
            <strong>Acme Corp Portal</strong> - Welcome, {{ username }}!
        </div>
        <div class="nav-links">
            <a href="/dashboard">Dashboard</a>
            <a href="/profile">Profile</a>
            <a href="/admin/config">Admin Config</a>
            <a href="/logout" class="logout">Logout</a>
        </div>
    </div>

    <div class="container">
        <h1>Customer Dashboard</h1>

        <div class="stats">
            <div class="stat">
                <h3>247</h3>
                <p>Total Orders</p>
            </div>
            <div class="stat">
                <h3>$15.2K</h3>
                <p>Revenue (MTD)</p>
            </div>
            <div class="stat">
                <h3>98.7%</h3>
                <p>Uptime</p>
            </div>
            <div class="stat">
                <h3>42</h3>
                <p>Active Users</p>
            </div>
        </div>

        <div class="card">
            <h2>Recent Activity</h2>
            <p><strong>{{ now }}</strong> - Login from {{ ip }}</p>
            <p><strong>2026-06-26 14:32</strong> - API request to /v1/orders</p>
            <p><strong>2026-06-25 09:15</strong> - Dashboard accessed</p>
        </div>

        <div class="card">
            <h2>Quick Links</h2>
            <ul>
                <li><a href="/api/docs">API Documentation</a></li>
                <li><a href="/admin/config">System Configuration</a> (Admin only)</li>
                <li><a href="/support">Contact Support</a></li>
            </ul>
        </div>

        <!-- Hint for CTF players -->
        <!-- System configuration available at /admin/config -->
        <!-- Master API key stored there for integration -->
    </div>
</body>
</html>
"""

# Admin config page (THE REAL FLAG IS HERE)
ADMIN_CONFIG = """
<!DOCTYPE html>
<html>
<head>
    <title>System Configuration - Acme Corp</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            color: #00ff00;
            padding: 20px;
        }
        .config {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 5px;
            max-width: 800px;
            margin: 20px auto;
        }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .secret {
            background: #3d3d3d;
            padding: 10px;
            border-left: 3px solid #00ff00;
            margin: 10px 0;
        }
        .warning {
            color: #ffaa00;
            border-left: 3px solid #ffaa00;
        }
        h1 {
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
        }
        a {
            color: #00aaff;
        }
    </style>
</head>
<body>
    <div class="config">
        <h1>⚙️ SYSTEM CONFIGURATION</h1>
        <p>Environment: <strong>PRODUCTION</strong></p>
        <p>Server: web-prod-01</p>
        <p>Last updated: 2026-06-26 18:45:03 UTC</p>

        <hr style="border-color: #00ff00;">

        <h2>Environment Variables</h2>
        <pre>
DATABASE_URL=postgresql://acme_prod:********@db.internal:5432/acme_production
REDIS_URL=redis://cache.internal:6379/0
SECRET_KEY=********
SESSION_TIMEOUT=3600
DEBUG=false
        </pre>

        <h2>API Configuration</h2>
        <div class="secret warning">
        <pre>
# ⚠️ WARNING: CONFIDENTIAL - DO NOT SHARE
# Master API Key for all system integrations
# This key has full administrative privileges

MASTER_API_KEY={{ flag }}

# Rate Limits:
# - Standard tier: 1000 req/hour
# - Premium tier: 10000 req/hour
# - Admin (using master key): unlimited
        </pre>
        </div>

        <h2>🎉 CONGRATULATIONS!</h2>
        <p style="color: #00ff00;">You successfully authenticated and found the production secret.</p>
        <p style="color: #00aaff;">This is the "white hat" path - you accessed the system legitimately.</p>
        <p><a href="/dashboard">← Back to Dashboard</a></p>
    </div>
</body>
</html>
"""


@app.route('/')
def index():
    """Landing page."""
    return render_template_string(LANDING_PAGE)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username in VALID_USERS and VALID_USERS[username] == password:
            session['username'] = username
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(LOGIN_PAGE, error='Invalid credentials'), 401

    return render_template_string(LOGIN_PAGE, error=None)


@app.route('/dashboard')
def dashboard():
    """Customer dashboard (requires auth)."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    return render_template_string(
        DASHBOARD,
        username=session.get('username'),
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        ip=request.headers.get('X-Forwarded-For', request.remote_addr)
    )


@app.route('/admin/config')
def admin_config():
    """Admin configuration page - THE REAL FLAG IS HERE."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    return render_template_string(ADMIN_CONFIG, flag=PRODUCTION_FLAG)


@app.route('/profile')
def profile():
    """User profile."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    return f"""
    <h1>Profile: {session.get('username')}</h1>
    <p><a href="/dashboard">Back to Dashboard</a></p>
    """


@app.route('/api')
@app.route('/api/docs')
def api_docs():
    """API documentation."""
    return """
    <h1>API Documentation</h1>
    <p>Base URL: https://api.acmecorp.example/v1</p>
    <h2>Endpoints:</h2>
    <ul>
        <li>GET /v1/orders - List orders</li>
        <li>POST /v1/orders - Create order</li>
        <li>GET /v1/products - List products</li>
    </ul>
    <p><strong>Authentication:</strong> Use Master API key in Authorization header</p>
    <p>See /admin/config for API credentials (requires login)</p>
    """


@app.route('/about')
def about():
    """About page."""
    return "<h1>About Acme Corp</h1><p>Enterprise solutions since 2020.</p>"


@app.route('/contact')
def contact():
    """Contact page."""
    return "<h1>Contact Us</h1><p>Email: support@acmecorp.example</p>"


@app.route('/logout')
def logout():
    """Logout."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'production-portal', 'version': '2.1.4'})


@app.route('/robots.txt')
def robots():
    """Robots.txt with hints."""
    return """User-agent: *
Allow: /

# Disallow: /admin/config
# (Just kidding, admins need access)
# Default credentials documented in SECURITY.md
# Or check HTML source comments on main page
""", 200, {'Content-Type': 'text/plain'}


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
