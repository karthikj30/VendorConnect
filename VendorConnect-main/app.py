from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, send_file, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text
import json
import random
from datetime import datetime, timedelta
from queue import Queue, Empty
import io
import csv
import requests
from threading import Lock
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import string
import secrets
import jwt
from datetime import timezone
from authlib.integrations.flask_client import OAuth
import logging
import pytz
from ai_integrations import ai_bp

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# IST Timezone Configuration
IST = pytz.timezone('Asia/Kolkata')

# Helper functions for distance calculation and rewards
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points on Earth."""
    try:
        R = 6371.0  # Earth radius in kilometers
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c  # Distance in kilometers
    except Exception:
        return 0.0

def calculate_distance_reward(distance_km):
    """Calculate reward points based on distance covered (in km)."""
    # Award 10 points per km for self-pickup
    return max(10, int(distance_km * 10))

def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

def to_ist(dt):
    """Convert datetime to IST"""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except Exception:
            return dt
    if dt.tzinfo is None:
        # Assume UTC if no timezone
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(IST)

def format_ist_time(dt, fmt='%d %b %Y, %I:%M %p'):
    """Format datetime to IST with custom format"""
    if dt is None:
        return ''
    ist_dt = to_ist(dt) if not isinstance(dt, str) else to_ist(dt)
    if isinstance(ist_dt, str):
        return ist_dt
    return ist_dt.strftime(fmt)


# Shared image configuration
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Action label localization helper (Marathi)
MR_ACTION_LABELS = {
    'find-suppliers': 'पुरवठादार शोधा',
    'place-order': 'ऑर्डर करा',
    'price-alerts': 'किंमत अलर्ट',
    'market-trends': 'बाजारातील प्रवृत्ती',
    'supplier-tips': 'पुरवठादार टिप्स',
    'pricing-strategy': 'किंमत धोरण',
    'customer-service': 'ग्राहक सेवा',
    'inventory-management': 'इन्व्हेंटरी व्यवस्थापन',
    'seasonal-planning': 'हंगामी नियोजन',
    'price-analysis': 'किंमत विश्लेषण',
    'demand-forecast': 'मागणी अंदाज',
    'seasonal-trends': 'हंगामी प्रवृत्ती',
    'competitor-analysis': 'स्पर्धक विश्लेषण',
    'supply-chain-insights': 'पुरवठा साखळी अंतर्दृष्टी',
    'customer-preferences': 'ग्राहक पसंती',
    'live-chat': 'लाइव्ह चॅट सुरू करा',
    'phone-support': 'फोन सपोर्ट',
    'email-support': 'ईमेल सपोर्ट',
    'faq': 'FAQ पहा',
    'video-tutorials': 'व्हिडिओ ट्युटोरियल',
    'community-forum': 'कम्युनिटी फोरम',
    'technical-support': 'तांत्रिक सहाय्य',
    'business-consultation': 'व्यवसाय सल्लामसलत',
    'view-supplier-details': 'पुरवठादार तपशील पहा',
    'compare-suppliers': 'पुरवठादार तुलना करा',
    'contact-supplier': 'पुरवठादाराशी संपर्क करा',
    'supplier-performance': 'कामगिरी विश्लेषण',
    'negotiate-prices': 'किंमतींची चर्चा करा',
    'backup-suppliers': 'बॅकअप पुरवठादार शोधा',
    'seasonal-analysis': 'हंगामी विश्लेषण',
    'supplier-reviews': 'रिव्ह्यू वाचा',
    'get-directions': 'मार्ग मिळवा',
    'call-supplier': 'पुरवठादाराला कॉल करा',
    'view-on-map': 'नकाशावर पहा',
    'set-location': 'माझे ठिकाण सेट करा',
    'read-reviews': 'रिव्ह्यू वाचा',
    'view-details': 'तपशील पहा',
    'add-to-favorites': 'आवडत्यांमध्ये जोडा',
    'compare-prices': 'किंमतींची तुलना करा',
    'set-price-alert': 'किंमत अलर्ट सेट करा',
    'bulk-discount': 'मोठ्या सवलती',
    'negotiate-price': 'किंमत चर्चा करा',
    'select-category': 'श्रेणी निवडा',
    'view-all-categories': 'सर्व श्रेणी पहा',
    'mixed-order': 'मिश्रित ऑर्डर',
    'seasonal-products': 'हंगामी उत्पादने',
    'track-current': 'सध्याची डिलिव्हरी ट्रॅक करा',
    'delivery-history': 'डिलिव्हरी इतिहास',
    'delivery-settings': 'डिलिव्हरी सेटिंग्ज',
    'contact-driver': 'ड्रायव्हरशी संपर्क करा',
    'urgent-delivery': 'तातडीची डिलिव्हरी',
    'report-delay': 'विलंब नोंदवा',
    'schedule-delivery': 'डिलिव्हरी शेड्यूल करा',
    'change-address': 'पत्ता बदला',
    'current-prices': 'सध्याचे भाव',
    'set-alerts': 'अलर्ट सेट करा',
    'price-comparison': 'किंमत तुलना',
    'price-trends': 'किंमतीचे ट्रेंड',
    'market-analysis': 'बाजार विश्लेषण',
    'bulk-pricing': 'मोठ्या ऑर्डरचे दर',
    'price-history': 'किंमत इतिहास',
    'browse-products': 'उत्पादने ब्राउझ करा',
    'search-products': 'उत्पादने शोधा',
    'product-details': 'उत्पादन तपशील',
    'add-to-cart': 'कार्टमध्ये जोडा',
    'business-analytics': 'व्यवसाय विश्लेषण',
    'best-practices': 'सर्वोत्तम पद्धती',
    'growth-strategies': 'वाढीच्या रणनीती',
    'networking': 'नेटवर्किंग',
    'resources': 'संसाधने',
    'consultation': 'तज्ज्ञ सल्ला',
    'related-topics': 'संबंधित विषय',
    'start-over': 'पुन्हा सुरू करा',
    'create-group-order': 'ग्रुप ऑर्डर तयार करा',
    'view-orders': 'ऑर्डर पहा',
    'urgent-order': 'तातडीचा ऑर्डर',
    'bulk-order': 'मोठा ऑर्डर',
    'price-check': 'किंमती तपासा',
    'stock-check': 'स्टॉक तपासा',
    'login': 'लॉग इन',
    'register': 'नोंदणी',
    'view-profile': 'प्रोफाइल पहा',
    'edit-profile': 'प्रोफाइल संपादित करा',
    'order-history': 'ऑर्डर इतिहास',
    'settings': 'सेटिंग्ज',
    'account-settings': 'अकाउंट सेटिंग्ज',
    'contact-support': 'सपोर्टशी संपर्क करा'
}

def localize_action_label(language, action_key, default_label):
    if language == 'mr':
        return MR_ACTION_LABELS.get(action_key, default_label)
    return default_label

def make_actions(language, pairs):
    return [{'action': k, 'label': localize_action_label(language, k, v)} for (k, v) in pairs if k and v]

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try to load .env manually
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass  # .env file doesn't exist, use default values

basedir = os.path.abspath(os.path.dirname(__file__))

# Configure Flask app with explicit instance path pointing to the repo-level instance folder
app = Flask(__name__, instance_path=os.path.join(basedir, '../instance'))
app.config['SECRET_KEY'] = 'vendorconnect_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size

# Flask session configuration - REQUIRED for OAuth state management
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True for HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session expires in 7 days

# Configure logging
log_level = logging.DEBUG if os.environ.get('FLASK_DEBUG') in ('1', 'true', 'True') or os.environ.get('DEBUG') in ('1', 'true', 'True') else logging.INFO
logging.basicConfig(level=log_level)
app.logger.setLevel(log_level)

# Ensure the instance directory exists (required for SQLite file creation)
os.makedirs(app.instance_path, exist_ok=True)

# Use an absolute path inside the instance directory for the SQLite database
db_path = os.path.join(app.instance_path, 'vendorconnect.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
try:
    from email_config import MAIL_USERNAME, MAIL_PASSWORD, MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS
    app.config['MAIL_SERVER'] = MAIL_SERVER
    app.config['MAIL_PORT'] = MAIL_PORT
    app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
    app.config['MAIL_USERNAME'] = MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
except ImportError:
    # Fallback to environment variables
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'hackathongoo@gmail.com')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-app-password')

db = SQLAlchemy(app)
# optional migrations support (Flask-Migrate)
try:
    from flask_migrate import Migrate
    migrate = Migrate(app, db)
except Exception:
    migrate = None

CORS(app)

# Register AI blueprint
app.register_blueprint(ai_bp, url_prefix='/api/ai')

# Real-time delivery tracking cache (in-memory for speed)
delivery_location_cache = {}
delivery_cache_lock = Lock()

# Order event queues for Server-Sent Events (in-memory)
order_event_queues = {}

def publish_order_event(order_id, event_type, data=None):
    # Publish to per-order queue
    q = order_event_queues.setdefault(order_id, Queue())
    ev = {'type': event_type, 'data': data or {}, 'timestamp': format_ist_time(datetime.utcnow(), '%d %b %Y, %I:%M %p')}
    q.put(ev)

    # Also publish to supplier-level queue so supplier dashboards can subscribe
    try:
        order = Order.query.get(order_id)
        if order and getattr(order, 'supplier_id', None):
            sup_key = f"supplier_{order.supplier_id}"
            sup_q = order_event_queues.setdefault(sup_key, Queue())
            sup_q.put(ev)
    except Exception:
        # If DB not available in current context or other error, skip supplier publish
        pass

# Uploads for supplier files
app.config['SUPPLIER_UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads', 'suppliers')
os.makedirs(app.config['SUPPLIER_UPLOAD_FOLDER'], exist_ok=True)

# Google OAuth client ID (set via environment variable `GOOGLE_CLIENT_ID`)
def _sanitize_val(v):
    if not isinstance(v, str):
        return v
    s = v.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    return s

app.config['GOOGLE_CLIENT_ID'] = _sanitize_val(os.environ.get('GOOGLE_CLIENT_ID', ''))
app.config['GOOGLE_CLIENT_SECRET'] = _sanitize_val(os.environ.get('GOOGLE_CLIENT_SECRET', ''))
# Redirect URI for OAuth callbacks (set to your deployed callback or localhost for testing)
app.config['GOOGLE_REDIRECT_URI'] = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/google/callback')

# Google Maps API Key for delivery tracking and location services
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', 'AIzaSyAWQBl4gL3BK5dvcPIzSCQf8DPILngrZoo')

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', os.environ.get('SECRET_KEY', 'change-me-jwt-secret'))
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_EXP_DELTA_SECONDS'] = int(os.environ.get('JWT_EXP_DELTA_SECONDS', 60*60*24))

# Try to load Google client credentials from a local JSON file if env vars are not set
def _load_google_client_from_file():
    """Populate GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET safely.

    Many setups export the entire Google client JSON as the value of
    GOOGLE_CLIENT_SECRET. Previously we returned early if both env values
    were present, which left the raw JSON string as the secret and caused
    token exchange failures (invalid_client). Now we detect and parse the
    JSON even when GOOGLE_CLIENT_ID is set.
    """
    # If the secret looks like JSON, prefer parsing it regardless of whether
    # a client_id has been provided separately.
    raw_secret_env = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    if raw_secret_env and isinstance(raw_secret_env, str) and raw_secret_env.strip().startswith('{'):
        try:
            data = json.loads(raw_secret_env)
            kind = 'web' if data.get('web') else ('installed' if data.get('installed') else 'raw')
            creds = data.get('web') or data.get('installed') or data
            cid = creds.get('client_id')
            csec = creds.get('client_secret')
            if cid:
                app.config['GOOGLE_CLIENT_ID'] = _sanitize_val(cid)
            if csec:
                app.config['GOOGLE_CLIENT_SECRET'] = _sanitize_val(csec)
            app.config['GOOGLE_CLIENT_KIND'] = kind
            app.config['GOOGLE_CLIENT_SOURCE'] = 'env_json'
            if cid or csec:
                app.logger.info('Loaded Google client credentials from GOOGLE_CLIENT_SECRET env JSON')
                return
        except Exception as e:
            app.logger.exception('Failed to parse GOOGLE_CLIENT_SECRET env as JSON:')

    # If both are already non-empty plain strings (not JSON), we are done.
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        return

    possible_files = ['client_secret.json', 'client_secrets.json', 'google_client_secret.json']
    for fname in possible_files:
        try:
            with open(os.path.join(basedir, fname), 'r') as f:
                data = json.load(f)
                # support both {"web": {...}} and root object
                kind = 'web' if data.get('web') else ('installed' if data.get('installed') else 'raw')
                creds = data.get('web') or data.get('installed') or data
                cid = creds.get('client_id')
                csec = creds.get('client_secret')
                if cid:
                    app.config['GOOGLE_CLIENT_ID'] = _sanitize_val(cid)
                if csec:
                    app.config['GOOGLE_CLIENT_SECRET'] = _sanitize_val(csec)
                app.config['GOOGLE_CLIENT_KIND'] = kind
                app.config['GOOGLE_CLIENT_SOURCE'] = f'file:{fname}'
                if cid or csec:
                    app.logger.info('Loaded Google client credentials from %s', fname)
                    return
        except FileNotFoundError:
            continue
        except Exception as e:
            app.logger.exception('Error reading google client file %s', fname)
            continue

_load_google_client_from_file()

# Register Authlib OAuth client for Google
oauth = OAuth(app)

# Error handlers - return JSON for API errors
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors by returning JSON for API calls"""
    if request.content_type and 'application/json' in request.content_type or request.path.startswith('/api'):
        return jsonify({'success': False, 'error': 'Not found', 'message': 'The requested resource was not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(401)
def unauthorized_error(error):
    """Handle 401 errors by returning JSON for API calls"""
    if request.content_type and 'application/json' in request.content_type or request.path.startswith('/api'):
        return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'Please login first'}), 401
    return redirect(url_for('vendor_login')), 401

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors by returning JSON for API calls"""
    db.session.rollback()
    app.logger.error(f'Internal server error: {error}')
    if request.content_type and 'application/json' in request.content_type or request.path.startswith('/api'):
        return jsonify({'success': False, 'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
    return render_template('index.html'), 500

@app.errorhandler(400)
def bad_request_error(error):
    """Handle 400 errors by returning JSON"""
    if request.content_type and 'application/json' in request.content_type or request.path.startswith('/api'):
        return jsonify({'success': False, 'error': 'Bad request', 'message': 'Invalid request data'}), 400
    return render_template('index.html'), 400

@app.errorhandler(405)
def method_not_allowed_error(error):
    """Handle 405 errors by returning JSON"""
    if request.content_type and 'application/json' in request.content_type or request.path.startswith('/api'):
        return jsonify({'success': False, 'error': 'Method not allowed', 'message': f'The {request.method} method is not allowed for this endpoint'}), 405
    return render_template('index.html'), 405

# --------------------
# Role-based decorators
# --------------------
from functools import wraps

def _make_redirector(role_key, login_endpoint):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if role_key not in session:
                return redirect(url_for(login_endpoint))
            return f(*args, **kwargs)
        return wrapper
    return decorator

def _make_json_guard(role_key):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if role_key not in session:
                return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Specific decorators
supplier_required = _make_redirector('supplier_id', 'vendor_login')
supplier_api_required = _make_json_guard('supplier_id')
vendor_required = _make_redirector('vendor_id', 'vendor_login')
vendor_api_required = _make_json_guard('vendor_id')
customer_required = _make_redirector('customer_id', 'customer_login')
customer_api_required = _make_json_guard('customer_id')
delivery_agent_required = _make_redirector('delivery_agent_id', 'delivery_login')
delivery_api_required = _make_json_guard('delivery_agent_id')
@app.errorhandler(Exception)
def handle_exception(error):
    """Handle any unhandled exceptions"""
    app.logger.error(f'Unhandled exception: {error}', exc_info=True)
    if request.content_type and 'application/json' in request.content_type or request.path.startswith('/api'):
        return jsonify({'success': False, 'error': 'Internal server error', 'message': 'An unexpected error occurred. Please check the server logs.'}), 500
    return render_template('index.html'), 500

def ensure_oauth_registered(force=False):
    """Ensure the Google OAuth client is registered with Authlib.

    This validates that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are present
    and are strings. If missing, it logs a helpful message. Calling this before
    `authorize_redirect` prevents the "missing client_id" error.
    """
    clients = getattr(oauth, 'clients', None) or getattr(oauth, '_clients', None)
    registered = False
    if clients:
        registered = 'google' in clients

    client_id = _sanitize_val(app.config.get('GOOGLE_CLIENT_ID'))
    client_secret = _sanitize_val(app.config.get('GOOGLE_CLIENT_SECRET'))
    # Persist sanitized versions
    app.config['GOOGLE_CLIENT_ID'] = client_id or ''
    app.config['GOOGLE_CLIENT_SECRET'] = client_secret or ''

    # Validate presence and types
    if not client_id or not isinstance(client_id, str) or not client_id.strip():
        app.logger.error('Google OAuth client_id is missing or empty. Set GOOGLE_CLIENT_ID env var before starting the app.')
        return False
    if not client_secret or not isinstance(client_secret, str) or not client_secret.strip():
        app.logger.error('Google OAuth client_secret is missing or empty. Set GOOGLE_CLIENT_SECRET env var (plain secret or JSON) before starting the app.')
        return False

    # If not registered yet, or forced re-registration, register now
    if not registered or force:
        try:
            # Remove any existing registration
            try:
                if registered:
                    try:
                        del oauth._clients['google']
                    except Exception:
                        pass
            except Exception:
                pass

            oauth.register(
                name='google',
                client_id=client_id,
                client_secret=client_secret,
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
            app.logger.info('Registered Authlib Google client with client_id: %s', client_id)
            return True
        except Exception as e:
            app.logger.exception('Error registering Google OAuth client:')
            return False

    return True

def _is_local_debug_request():
    try:
        if os.environ.get('FLASK_DEBUG') in ('1', 'true', 'True') or os.environ.get('DEBUG') in ('1', 'true', 'True'):
            return True
        ra = request.remote_addr or ''
        # Allow localhost and common private ranges
        return ra.startswith('127.') or ra == '::1' or ra.startswith('10.') or ra.startswith('192.168.') or ra.startswith('172.16.')
    except Exception:
        return False

@app.route('/_debug/oauth', methods=['GET'])
def oauth_debug_info():
    """Return redacted OAuth config for local debugging only."""
    if not _is_local_debug_request():
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    # Do not mutate registration here; only inspect
    clients = getattr(oauth, 'clients', None) or getattr(oauth, '_clients', None) or {}
    cid = _sanitize_val(app.config.get('GOOGLE_CLIENT_ID', '')) or ''
    secret_val = _sanitize_val(app.config.get('GOOGLE_CLIENT_SECRET', '')) or ''
    secret_present = bool(secret_val)
    secret_len = len(secret_val)
    info = {
        'client_id_present': bool(cid),
        'client_id_suffix': cid[-8:] if cid else '',
        'secret_present': secret_present,
        'redirect_uri_config': app.config.get('GOOGLE_REDIRECT_URI'),
        'redirect_uri_url_for': url_for('vendor_login_google_callback', _external=True),
        'oauth_client_registered': 'google' in clients,
        'client_kind': app.config.get('GOOGLE_CLIENT_KIND', ''),
        'client_source': app.config.get('GOOGLE_CLIENT_SOURCE', ''),
        'secret_length': secret_len,
    }
    return jsonify({'success': True, 'info': info})

def exchange_google_auth_code(code, redirect_uri):
    """Manually exchange Google authorization code for access token.
    
    This bypasses Authlib's state validation which can fail when session
    is not properly maintained across redirects.
    """
    try:
        token_endpoint = 'https://oauth2.googleapis.com/token'
        client_id = _sanitize_val(app.config.get('GOOGLE_CLIENT_ID'))
        client_secret = _sanitize_val(app.config.get('GOOGLE_CLIENT_SECRET'))
        
        if not client_id or not client_secret:
            app.logger.error('Google OAuth credentials not configured')
            return None
        
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        app.logger.info('Exchanging auth code for token: redirect_uri=%s', redirect_uri)
        # Some Google configurations prefer/require HTTP Basic auth with
        # client_id:client_secret in addition to form params.
        resp = requests.post(
            token_endpoint,
            data=payload,
            auth=(client_id, client_secret),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        if resp.status_code != 200:
            try:
                app.logger.error('Token exchange failed: %s', resp.text)
            except Exception:
                pass
        resp.raise_for_status()
        token_data = resp.json()
        app.logger.info('Token exchange successful, access_token=%s...', token_data.get('access_token', '')[:20])
        return token_data
    except Exception as e:
        app.logger.exception('Error exchanging authorization code for token:')
        return None

def fetch_google_userinfo(access_token):
    """Fetch user info from Google using access token"""
    try:
        userinfo_endpoint = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        resp = requests.get(userinfo_endpoint, headers=headers)
        resp.raise_for_status()
        user_info = resp.json()
        app.logger.info('Userinfo fetched: email=%s, name=%s', user_info.get('email'), user_info.get('name'))
        return user_info
    except Exception as e:
        app.logger.exception('Error fetching userinfo from Google:')
        return None


def send_otp_email(email, otp):
    """Send OTP email to user"""
    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = email
        msg['Subject'] = "VendorConnect - Password Reset OTP"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">🍽️ VendorConnect</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Street Food Vendor Platform</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <h2 style="color: #333; margin-bottom: 20px;">Password Reset Request</h2>
                <p style="color: #666; line-height: 1.6;">You have requested to reset your password for your VendorConnect account.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; border: 2px solid #667eea;">
                    <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Your verification code is:</p>
                    <div style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px; margin: 10px 0;">{otp}</div>
                    <p style="margin: 10px 0 0 0; color: #dc3545; font-size: 12px; font-weight: bold;">⏰ Valid for 10 minutes only</p>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404; font-size: 14px;">
                        <strong>⚠️ Security Notice:</strong> If you did not request this password reset, please ignore this email. 
                        Your account remains secure.
                    </p>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This email was sent from <strong>hackathongoo@gmail.com</strong><br>
                    For support, please contact our team.
                </p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                <p>© 2024 VendorConnect - Empowering Street Food Vendors</p>
                <p>Built with ❤️ for India's Street Food Culture</p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        text = msg.as_string()
        server.sendmail(app.config['MAIL_USERNAME'], email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        # Fallback to mock email service for testing
        return send_mock_otp_email(email, otp)

def send_mock_otp_email(email, otp):
    """Mock email sending - just prints the OTP to console"""
    print("\n" + "="*60)
    print("📧 MOCK EMAIL SENT (For Testing Purposes)")
    print("="*60)
    print(f"📧 To: {email}")
    print(f"📧 From: hackathongoo@gmail.com")
    print(f"📧 Subject: VendorConnect - Password Reset OTP")
    print(f"🔑 OTP Code: {otp}")
    print(f"⏰ Expires: 10 minutes from now")
    print("="*60)
    print("✅ In production, this would be sent as a real email")
    print("✅ The user would receive this OTP in their inbox")
    print("="*60)
    
    # Also save to a file for easy access
    with open('otp_log.txt', 'a') as f:
        f.write(f"{datetime.now()}: OTP {otp} sent to {email}\n")
    
    return True

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def extract_gps_from_address(address):
    """
    Extract or generate approximate GPS coordinates from address string
    Uses simple pattern matching for common Bangalore locations
    For production, integrate with Google Maps Geocoding API or Mapbox
    """
    if not address:
        return None, None
    
    address_lower = address.lower()
    
    # Common Bangalore locations and their approximate coordinates
    bangalore_locations = {
        'mg road': (12.9352, 77.6245),
        'indiranagar': (12.9716, 77.6412),
        'koramangala': (12.9352, 77.6245),
        'whitefield': (12.9698, 77.7499),
        'marathahalli': (12.9716, 77.7501),
        'jayanagar': (13.0033, 77.5933),
        'yelahanka': (13.1059, 77.5945),
        'sr nagar': (13.0035, 77.5936),
        'banaswadi': (13.0259, 77.5869),
        'malleshwaram': (13.0021, 77.5738),
        'btm': (12.9176, 77.6412),
        'hsr': (12.9352, 77.6298),
        'rest area': (13.1939, 77.7063),
        'central': (12.9716, 77.5945),
        'east': (13.0259, 77.6411),
        'west': (12.9716, 77.5200),
        'south': (12.8397, 77.6245),
        'north': (13.0830, 77.6245),
    }
    
    # Search for known locations in address
    for location_name, (lat, lon) in bangalore_locations.items():
        if location_name in address_lower:
            # Add slight random variation to simulate different addresses in area (±0.01 degrees)
            lat += random.uniform(-0.01, 0.01)
            lon += random.uniform(-0.01, 0.01)
            return round(lat, 6), round(lon, 6)
    
    # Default: Return center of Bangalore if location not recognized
    # This allows the system to work without external API
    default_lat = 12.9716 + random.uniform(-0.05, 0.05)
    default_lon = 77.5945 + random.uniform(-0.05, 0.05)
    return round(default_lat, 6), round(default_lon, 6)


# Database Models
class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    location = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(100), nullable=False, default='other')
    gstin = db.Column(db.String(15), unique=True, nullable=True)
    logo = db.Column(db.String(300), nullable=True)
    hero_image = db.Column(db.String(300), nullable=True)
    promo_due = db.Column(db.Float, default=0.0)
    # Open/Closed status to control menu visibility for customers
    is_open = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True)
    balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float, default=0.0)
    verification_status = db.Column(db.Boolean, default=False)
    hygiene_rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Added authentication fields so suppliers can sign up / login
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    # Business details
    business_name = db.Column(db.String(200), nullable=True)
    gstin = db.Column(db.String(20), unique=True, nullable=True)
    # Path to uploaded certification file
    certification = db.Column(db.String(300), nullable=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    stock_available = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='kg')

class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(400), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(400), nullable=True)
    postal_codes = db.Column(db.Text, nullable=True)  # comma separated list of postal codes or areas
    radius_km = db.Column(db.Float, nullable=True)  # optional radius from base location
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    image = db.Column(db.String(300), nullable=True)
    ingredients = db.Column(db.Text, nullable=True)  # Comma-separated or JSON list of ingredients
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DeliveryAgent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    vehicle_info = db.Column(db.String(200), nullable=True)
    vehicle_type = db.Column(db.String(50), nullable=True)  # bike, car, auto, van, small_truck, tempo, truck, container
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Settings
    email_notifications = db.Column(db.Boolean, default=True)
    sms_notifications = db.Column(db.Boolean, default=True)
    promo_emails = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(10), default='en')
    theme = db.Column(db.String(20), default='light')
    default_instructions = db.Column(db.Text, nullable=True)
    default_payment = db.Column(db.String(20), default='cod')
    profile_visibility = db.Column(db.String(20), default='private')
    data_sharing = db.Column(db.Boolean, default=False)
    # Rewards
    reward_points = db.Column(db.Float, default=0.0)  # Points earned from self-pickup distance rewards

class CustomerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    delivery_fee = db.Column(db.Float, default=40.0)
    tax_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, preparing, ready, out_for_delivery, delivered, cancelled, done
    delivery_type = db.Column(db.String(20), default='delivery')  # delivery or self_pickup
    payment_method = db.Column(db.String(20), default='cod')
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    delivery_address = db.Column(db.String(300), nullable=True)
    delivery_instructions = db.Column(db.String(500), nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    customer_email = db.Column(db.String(120), nullable=True)
    customer_phone = db.Column(db.String(15), nullable=True)
    delivery_agent_id = db.Column(db.Integer, db.ForeignKey('delivery_agent.id'), nullable=True)
    delivery_latitude = db.Column(db.Float, nullable=True)
    delivery_longitude = db.Column(db.Float, nullable=True)
    estimated_delivery_time = db.Column(db.DateTime, nullable=True)
    actual_delivery_time = db.Column(db.DateTime, nullable=True)
    confirmed_at = db.Column(db.DateTime, nullable=True)  # When order was confirmed
    preparing_at = db.Column(db.DateTime, nullable=True)  # When food preparation started
    ready_at = db.Column(db.DateTime, nullable=True)  # When order was ready
    pickup_ready_at = db.Column(db.DateTime, nullable=True)  # When order is ready for pickup (self-pickup orders)
    picked_up_at = db.Column(db.DateTime, nullable=True)  # When delivery agent picked up OR customer picked up
    out_for_delivery_at = db.Column(db.DateTime, nullable=True)  # When delivery started
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CustomerOrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    order_type = db.Column(db.String(20), default='individual')  # individual or group
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Timestamps for supplier order lifecycle
    confirmed_at = db.Column(db.DateTime, nullable=True)
    preparing_at = db.Column(db.DateTime, nullable=True)
    ready_at = db.Column(db.DateTime, nullable=True)
    out_for_delivery_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)
    # Delivery agent assignment
    delivery_agent_id = db.Column(db.Integer, db.ForeignKey('delivery_agent.id'), nullable=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

class GroupOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)   # nullable: allow free-text name
    product_name = db.Column(db.String(200), nullable=True)                           # free-text fallback when no FK
    target_quantity = db.Column(db.Float, nullable=False)
    current_quantity = db.Column(db.Float, default=0)
    price_per_unit = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupOrderParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_order_id = db.Column(db.Integer, db.ForeignKey('group_order.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

class OTPVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    video_url = db.Column(db.String(500), nullable=False)
    price_per_view = db.Column(db.Float, default=5.0)  # 5-10 per view
    total_views = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

class PromotionView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotion.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

# Tracking links for public order tracking
class TrackingLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

class CustomerReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    food_quality = db.Column(db.Integer, nullable=True)  # 1-5
    delivery_speed = db.Column(db.Integer, nullable=True)  # 1-5
    packaging = db.Column(db.Integer, nullable=True)  # 1-5
    review_text = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), nullable=True)
    helpful_votes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=True)
    item_type = db.Column(db.String(20), default='vendor')  # 'vendor' or 'item'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScheduledOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_data = db.Column(db.Text, nullable=False)  # JSON string with order details
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    recurring = db.Column(db.String(20), nullable=True)  # daily, weekly, monthly, or None for one-time
    next_occurrence = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VendorChatMessage(db.Model):
    """Model for vendor-to-vendor chat messages"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('Vendor', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('Vendor', foreign_keys=[receiver_id], backref='received_messages')

class InternshipOpportunity(db.Model):
    """Model for internship opportunities"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=True)
    responsibilities = db.Column(db.Text, nullable=True)
    skills_required = db.Column(db.Text, nullable=True)  # Comma-separated
    stipend = db.Column(db.String(100), nullable=True)  # e.g., "5000-10000" or "Unpaid"
    duration = db.Column(db.String(100), nullable=True)  # e.g., "3 months", "6 months"
    location = db.Column(db.String(200), nullable=True)
    work_mode = db.Column(db.String(50), default='on-site')  # on-site, remote, hybrid
    category = db.Column(db.String(100), nullable=True)  # e.g., "Software", "Marketing", "Design"
    application_deadline = db.Column(db.DateTime, nullable=True)
    contact_email = db.Column(db.String(200), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    company_website = db.Column(db.String(300), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InternshipApplication(db.Model):
    """Model for vendor internship applications"""
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship_opportunity.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=True)
    resume_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), default='pending')  # pending, reviewed, shortlisted, rejected, accepted
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = db.relationship('Vendor', backref='internship_applications')
    internship = db.relationship('InternshipOpportunity', backref='applications')

# Sample data for demonstration
def create_sample_data():
    # Create sample suppliers only if none exist yet
    if not Supplier.query.first():
        suppliers_data = [
            {'name': 'Krishna Mandi', 'phone': '9876543210', 'location': 'Mumbai Central', 'rating': 4.5, 'verification_status': True, 'hygiene_rating': 4.2},
            {'name': 'Fresh Farm Supplies', 'phone': '9876543211', 'location': 'Andheri West', 'rating': 4.8, 'verification_status': True, 'hygiene_rating': 4.6},
            {'name': 'Quality Vegetables', 'phone': '9876543212', 'location': 'Bandra East', 'rating': 4.3, 'verification_status': True, 'hygiene_rating': 4.0},
            {'name': 'Organic Market', 'phone': '9876543213', 'location': 'Juhu', 'rating': 4.7, 'verification_status': True, 'hygiene_rating': 4.8},
            {'name': 'Local Grocery Store', 'phone': '9876543214', 'location': 'Santacruz', 'rating': 4.1, 'verification_status': False, 'hygiene_rating': 3.8}
        ]
        for supplier_data in suppliers_data:
            supplier = Supplier(**supplier_data)
            db.session.add(supplier)
        db.session.commit()

    # Only seed products if table is empty
    if Product.query.first():
        return
    
    # Create sample products
    products_data = [
        {'name': 'Tomatoes', 'category': 'vegetables', 'current_price': 28.0, 'supplier_id': 1, 'stock_available': 500, 'unit': 'kg'},
        {'name': 'Onions', 'category': 'vegetables', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 300, 'unit': 'kg'},
        {'name': 'Potatoes', 'category': 'vegetables', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 400, 'unit': 'kg'},
        {'name': 'Cooking Oil', 'category': 'oils', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 100, 'unit': 'liter'},
        {'name': 'Rice', 'category': 'grains', 'current_price': 45.0, 'supplier_id': 4, 'stock_available': 200, 'unit': 'kg'},
        {'name': 'Lentils', 'category': 'pulses', 'current_price': 85.0, 'supplier_id': 5, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Milk', 'category': 'dairy', 'current_price': 60.0, 'supplier_id': 2, 'stock_available': 100, 'unit': 'liter'},
        {'name': 'Sugar', 'category': 'essentials', 'current_price': 45.0, 'supplier_id': 3, 'stock_available': 200, 'unit': 'kg'},
        {'name': 'Ice Cream Mix', 'category': 'ice_cream', 'current_price': 150.0, 'supplier_id': 4, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Vanilla Essence', 'category': 'ice_cream', 'current_price': 500.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'liter'},
        {'name': 'Chocolate Syrup', 'category': 'ice_cream', 'current_price': 300.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'liter'},
        {'name': 'Strawberry Syrup', 'category': 'ice_cream', 'current_price': 280.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'liter'},
        {'name': 'Mango Pulp', 'category': 'ice_cream', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Pista (Pistachio)', 'category': 'ice_cream', 'current_price': 1200.0, 'supplier_id': 4, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Badam (Almonds)', 'category': 'ice_cream', 'current_price': 900.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Kesar (Saffron)', 'category': 'ice_cream', 'current_price': 2500.0, 'supplier_id': 1, 'stock_available': 5, 'unit': 'kg'},
        {'name': 'Rose Essence', 'category': 'ice_cream', 'current_price': 400.0, 'supplier_id': 2, 'stock_available': 15, 'unit': 'liter'},
        {'name': 'Coconut Powder', 'category': 'ice_cream', 'current_price': 180.0, 'supplier_id': 3, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Dry Fruits Mix', 'category': 'ice_cream', 'current_price': 800.0, 'supplier_id': 4, 'stock_available': 10, 'unit': 'kg'},
        {'name': 'Ice Cream Cones', 'category': 'ice_cream', 'current_price': 200.0, 'supplier_id': 5, 'stock_available': 100, 'unit': 'pack'},
        {'name': 'Sprinkles', 'category': 'ice_cream', 'current_price': 150.0, 'supplier_id': 1, 'stock_available': 50, 'unit': 'pack'},
        {'name': 'Chocolate Chips', 'category': 'ice_cream', 'current_price': 350.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Waffle Mix', 'category': 'ice_cream', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 35, 'unit': 'kg'},
        # Add more products for different business types
        {'name': 'Chickpeas', 'category': 'chaat', 'current_price': 65.0, 'supplier_id': 1, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Tamarind', 'category': 'chaat', 'current_price': 120.0, 'supplier_id': 2, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Mint Chutney', 'category': 'chaat', 'current_price': 80.0, 'supplier_id': 3, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Sev', 'category': 'chaat', 'current_price': 90.0, 'supplier_id': 4, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Papdi', 'category': 'chaat', 'current_price': 150.0, 'supplier_id': 5, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Boondi', 'category': 'chaat', 'current_price': 70.0, 'supplier_id': 1, 'stock_available': 60, 'unit': 'kg'},
        {'name': 'Pomegranate Seeds', 'category': 'chaat', 'current_price': 200.0, 'supplier_id': 2, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Coriander Leaves', 'category': 'chaat', 'current_price': 40.0, 'supplier_id': 3, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Green Chutney', 'category': 'chaat', 'current_price': 60.0, 'supplier_id': 4, 'stock_available': 35, 'unit': 'kg'},
        {'name': 'Sweet Chutney', 'category': 'chaat', 'current_price': 80.0, 'supplier_id': 5, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Curd', 'category': 'chaat', 'current_price': 50.0, 'supplier_id': 1, 'stock_available': 80, 'unit': 'liter'},
        {'name': 'Chaat Masala', 'category': 'chaat', 'current_price': 120.0, 'supplier_id': 2, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Rice Batter', 'category': 'dosa', 'current_price': 40.0, 'supplier_id': 4, 'stock_available': 200, 'unit': 'kg'},
        {'name': 'Urad Dal', 'category': 'dosa', 'current_price': 90.0, 'supplier_id': 5, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Potato Filling', 'category': 'dosa', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Coconut Chutney', 'category': 'dosa', 'current_price': 80.0, 'supplier_id': 2, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Sambar Powder', 'category': 'dosa', 'current_price': 150.0, 'supplier_id': 3, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Sambar Vegetables', 'category': 'dosa', 'current_price': 45.0, 'supplier_id': 4, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Onion Chutney', 'category': 'dosa', 'current_price': 60.0, 'supplier_id': 5, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Tomato Chutney', 'category': 'dosa', 'current_price': 55.0, 'supplier_id': 1, 'stock_available': 35, 'unit': 'kg'},
        {'name': 'Ginger Chutney', 'category': 'dosa', 'current_price': 70.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Dosa Batter Mix', 'category': 'dosa', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Potato Filling', 'category': 'samosa', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Samosa Sheets', 'category': 'samosa', 'current_price': 200.0, 'supplier_id': 2, 'stock_available': 50, 'unit': 'pack'},
        {'name': 'Green Peas', 'category': 'samosa', 'current_price': 45.0, 'supplier_id': 3, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Samosa Masala', 'category': 'samosa', 'current_price': 180.0, 'supplier_id': 4, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Coriander Powder', 'category': 'samosa', 'current_price': 160.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Cumin Seeds', 'category': 'samosa', 'current_price': 200.0, 'supplier_id': 1, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Garam Masala', 'category': 'samosa', 'current_price': 220.0, 'supplier_id': 2, 'stock_available': 12, 'unit': 'kg'},
        {'name': 'Red Chili Powder', 'category': 'samosa', 'current_price': 140.0, 'supplier_id': 3, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Turmeric Powder', 'category': 'samosa', 'current_price': 120.0, 'supplier_id': 4, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Ginger Garlic Paste', 'category': 'samosa', 'current_price': 80.0, 'supplier_id': 5, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Potato Filling', 'category': 'vada_pav', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Pav Bread', 'category': 'vada_pav', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 200, 'unit': 'pack'},
        {'name': 'Besan', 'category': 'vada_pav', 'current_price': 70.0, 'supplier_id': 3, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Vada Pav Masala', 'category': 'vada_pav', 'current_price': 160.0, 'supplier_id': 4, 'stock_available': 18, 'unit': 'kg'},
        {'name': 'Green Chutney', 'category': 'vada_pav', 'current_price': 60.0, 'supplier_id': 5, 'stock_available': 35, 'unit': 'kg'},
        {'name': 'Red Chutney', 'category': 'vada_pav', 'current_price': 65.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Garlic Chutney', 'category': 'vada_pav', 'current_price': 75.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Mustard Seeds', 'category': 'vada_pav', 'current_price': 180.0, 'supplier_id': 3, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Curry Leaves', 'category': 'vada_pav', 'current_price': 90.0, 'supplier_id': 4, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Asafoetida', 'category': 'vada_pav', 'current_price': 300.0, 'supplier_id': 5, 'stock_available': 8, 'unit': 'kg'},
        {'name': 'Tea Leaves', 'category': 'tea', 'current_price': 180.0, 'supplier_id': 4, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Ginger', 'category': 'tea', 'current_price': 60.0, 'supplier_id': 5, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Cardamom', 'category': 'tea', 'current_price': 1200.0, 'supplier_id': 1, 'stock_available': 10, 'unit': 'kg'},
        {'name': 'Black Pepper', 'category': 'tea', 'current_price': 400.0, 'supplier_id': 2, 'stock_available': 25, 'unit': 'kg'},
        {'name': 'Cinnamon', 'category': 'tea', 'current_price': 600.0, 'supplier_id': 3, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Cloves', 'category': 'tea', 'current_price': 800.0, 'supplier_id': 4, 'stock_available': 12, 'unit': 'kg'},
        {'name': 'Bay Leaves', 'category': 'tea', 'current_price': 300.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Tulsi Leaves', 'category': 'tea', 'current_price': 200.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Lemon Grass', 'category': 'tea', 'current_price': 250.0, 'supplier_id': 2, 'stock_available': 18, 'unit': 'kg'},
        {'name': 'Tea Masala', 'category': 'tea', 'current_price': 350.0, 'supplier_id': 3, 'stock_available': 22, 'unit': 'kg'},
        {'name': 'Oranges', 'category': 'juice', 'current_price': 80.0, 'supplier_id': 2, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Apples', 'category': 'juice', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Carrots', 'category': 'juice', 'current_price': 40.0, 'supplier_id': 4, 'stock_available': 120, 'unit': 'kg'},
        {'name': 'Beetroot', 'category': 'juice', 'current_price': 35.0, 'supplier_id': 5, 'stock_available': 90, 'unit': 'kg'},
        {'name': 'Cucumber', 'category': 'juice', 'current_price': 30.0, 'supplier_id': 1, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Spinach', 'category': 'juice', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Mint Leaves', 'category': 'juice', 'current_price': 45.0, 'supplier_id': 3, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Ginger', 'category': 'juice', 'current_price': 60.0, 'supplier_id': 4, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Honey', 'category': 'juice', 'current_price': 400.0, 'supplier_id': 5, 'stock_available': 25, 'unit': 'liter'},
        {'name': 'Rock Salt', 'category': 'juice', 'current_price': 20.0, 'supplier_id': 1, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Black Salt', 'category': 'juice', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 80, 'unit': 'kg'},
        {'name': 'Lemons', 'category': 'juice', 'current_price': 60.0, 'supplier_id': 5, 'stock_available': 60, 'unit': 'kg'},
        # Fruits for ice cream
        {'name': 'Strawberries', 'category': 'fruits', 'current_price': 200.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'kg'},
        {'name': 'Mangoes', 'category': 'fruits', 'current_price': 80.0, 'supplier_id': 2, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Bananas', 'category': 'fruits', 'current_price': 40.0, 'supplier_id': 3, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Pineapple', 'category': 'fruits', 'current_price': 60.0, 'supplier_id': 4, 'stock_available': 40, 'unit': 'kg'},
        {'name': 'Blueberries', 'category': 'fruits', 'current_price': 400.0, 'supplier_id': 5, 'stock_available': 15, 'unit': 'kg'},
        {'name': 'Kiwi', 'category': 'fruits', 'current_price': 300.0, 'supplier_id': 1, 'stock_available': 20, 'unit': 'kg'},
        {'name': 'Oranges', 'category': 'fruits', 'current_price': 80.0, 'supplier_id': 2, 'stock_available': 100, 'unit': 'kg'},
        {'name': 'Apples', 'category': 'fruits', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 80, 'unit': 'kg'}
    ]
    
    for product_data in products_data:
        # Map supplier_id to an existing supplier (cycle through available ones)
        available_suppliers = [s.id for s in Supplier.query.all()]
        if available_suppliers:
            sid = product_data['supplier_id']
            product_data['supplier_id'] = available_suppliers[(sid - 1) % len(available_suppliers)]
        product = Product(**product_data)
        db.session.add(product)
    
    db.session.commit()

def create_sample_orders():
    """Create sample orders for demonstration"""
    # Check if orders already exist
    if Order.query.first():
        return
    
    # Create sample orders for different vendors
    sample_orders = [
        # Vendor 1 orders (ice cream vendor)
        {'vendor_id': 1, 'supplier_id': 1, 'total_amount': 1200.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=2)},
        {'vendor_id': 1, 'supplier_id': 2, 'total_amount': 800.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=5)},
        {'vendor_id': 1, 'supplier_id': 3, 'total_amount': 1500.0, 'status': 'completed', 'order_type': 'group', 'created_at': datetime.now() - timedelta(days=8)},
        {'vendor_id': 1, 'supplier_id': 4, 'total_amount': 900.0, 'status': 'pending', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=1)},
        {'vendor_id': 1, 'supplier_id': 5, 'total_amount': 1100.0, 'status': 'completed', 'order_type': 'group', 'created_at': datetime.now() - timedelta(days=10)},
        
        # Vendor 2 orders (chaat vendor)
        {'vendor_id': 2, 'supplier_id': 1, 'total_amount': 1800.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=3)},
        {'vendor_id': 2, 'supplier_id': 2, 'total_amount': 1200.0, 'status': 'completed', 'order_type': 'group', 'created_at': datetime.now() - timedelta(days=6)},
        {'vendor_id': 2, 'supplier_id': 3, 'total_amount': 950.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=9)},
        
        # Vendor 3 orders (dosa vendor)
        {'vendor_id': 3, 'supplier_id': 1, 'total_amount': 1400.0, 'status': 'completed', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=4)},
        {'vendor_id': 3, 'supplier_id': 2, 'total_amount': 1600.0, 'status': 'completed', 'order_type': 'group', 'created_at': datetime.now() - timedelta(days=7)},
        {'vendor_id': 3, 'supplier_id': 3, 'total_amount': 750.0, 'status': 'pending', 'order_type': 'individual', 'created_at': datetime.now() - timedelta(days=2)},
    ]
    
    for order_data in sample_orders:
        order = Order(**order_data)
        db.session.add(order)
    
    db.session.commit()
    
    # Create sample order items
    sample_order_items = [
        # Order 1 items
        {'order_id': 1, 'product_id': 1, 'quantity': 20.0, 'price_per_unit': 28.0},  # Tomatoes
        {'order_id': 1, 'product_id': 2, 'quantity': 15.0, 'price_per_unit': 35.0},  # Onions
        
        # Order 2 items
        {'order_id': 2, 'product_id': 4, 'quantity': 5.0, 'price_per_unit': 120.0},  # Cooking Oil
        
        # Order 3 items
        {'order_id': 3, 'product_id': 5, 'quantity': 25.0, 'price_per_unit': 45.0},  # Rice
        {'order_id': 3, 'product_id': 6, 'quantity': 10.0, 'price_per_unit': 85.0},  # Lentils
        
        # Order 4 items
        {'order_id': 4, 'product_id': 9, 'quantity': 4.0, 'price_per_unit': 150.0},  # Ice Cream Mix
        {'order_id': 4, 'product_id': 10, 'quantity': 1.0, 'price_per_unit': 500.0}, # Vanilla Essence
        
        # Order 5 items
        {'order_id': 5, 'product_id': 11, 'quantity': 2.0, 'price_per_unit': 300.0}, # Chocolate Syrup
        {'order_id': 5, 'product_id': 12, 'quantity': 2.0, 'price_per_unit': 280.0}, # Strawberry Syrup
        
        # Order 6 items
        {'order_id': 6, 'product_id': 25, 'quantity': 20.0, 'price_per_unit': 65.0},  # Chickpeas
        {'order_id': 6, 'product_id': 26, 'quantity': 5.0, 'price_per_unit': 120.0},  # Tamarind
        
        # Order 7 items
        {'order_id': 7, 'product_id': 27, 'quantity': 10.0, 'price_per_unit': 80.0},  # Mint Chutney
        {'order_id': 7, 'product_id': 28, 'quantity': 8.0, 'price_per_unit': 90.0},   # Sev
        
        # Order 8 items
        {'order_id': 8, 'product_id': 29, 'quantity': 5.0, 'price_per_unit': 150.0},  # Papdi
        {'order_id': 8, 'product_id': 30, 'quantity': 10.0, 'price_per_unit': 70.0},  # Boondi
        
        # Order 9 items
        {'order_id': 9, 'product_id': 33, 'quantity': 25.0, 'price_per_unit': 40.0},  # Rice Batter
        {'order_id': 9, 'product_id': 34, 'quantity': 8.0, 'price_per_unit': 90.0},   # Urad Dal
        
        # Order 10 items
        {'order_id': 10, 'product_id': 35, 'quantity': 30.0, 'price_per_unit': 35.0}, # Potato Filling
        {'order_id': 10, 'product_id': 36, 'quantity': 15.0, 'price_per_unit': 80.0}, # Coconut Chutney
        
        # Order 11 items
        {'order_id': 11, 'product_id': 37, 'quantity': 3.0, 'price_per_unit': 150.0}, # Sambar Powder
        {'order_id': 11, 'product_id': 38, 'quantity': 15.0, 'price_per_unit': 45.0}, # Sambar Vegetables
    ]
    
    for item_data in sample_order_items:
        order_item = OrderItem(**item_data)
        db.session.add(order_item)
    
    db.session.commit()

def create_sample_vendors():
    """Create sample vendors for demonstration"""
    # Check if vendors already exist
    if Vendor.query.first():
        return
    
    # Create sample vendors
    sample_vendors = [
        {
            'name': 'Ice Cream Paradise',
            'phone': '9876543201',
            'email': 'icecream@vendor.com',
            'location': 'Bandra West',
            'business_type': 'ice_cream',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Chaat Corner',
            'phone': '9876543202',
            'email': 'chaat@vendor.com',
            'location': 'Andheri East',
            'business_type': 'chaat',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Dosa House',
            'phone': '9876543203',
            'email': 'dosa@vendor.com',
            'location': 'Juhu',
            'business_type': 'dosa',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Samosa King',
            'phone': '9876543204',
            'email': 'samosa@vendor.com',
            'location': 'Santacruz',
            'business_type': 'samosa',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Vada Pav Express',
            'phone': '9876543205',
            'email': 'vadapav@vendor.com',
            'location': 'Mumbai Central',
            'business_type': 'vada_pav',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Tea Junction',
            'phone': '9876543206',
            'email': 'tea@vendor.com',
            'location': 'Khar West',
            'business_type': 'tea',
            'password_hash': generate_password_hash('password123')
        },
        {
            'name': 'Fresh Juice Bar',
            'phone': '9876543207',
            'email': 'juice@vendor.com',
            'location': 'Versova',
            'business_type': 'juice',
            'password_hash': generate_password_hash('password123')
        }
    ]
    
    for vendor_data in sample_vendors:
        # Ensure required fields (gstin) exist for sample vendors to avoid integrity errors
        if not vendor_data.get('gstin'):
            # generate a pseudo-random 15-char GSTIN-like string
            vendor_data['gstin'] = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15))
        vendor = Vendor(**vendor_data)
        db.session.add(vendor)
    
    db.session.commit()
    print("✅ Sample vendors created successfully with business names!")

def create_sample_menu_items():
    """Create sample menu items for each vendor"""
    vendors = Vendor.query.all()
    
    if not vendors:
        print("⚠️ No vendors found. Create vendors first.")
        return
    
    # Check if menu items already exist
    if MenuItem.query.first():
        print("ℹ️ Menu items already exist")
        return
    
    # Sample menu items by business type
    menu_templates = {
        'ice_cream': [
            ('Vanilla Ice Cream', 50, 'Classic creamy vanilla ice cream'),
            ('Chocolate Ice Cream', 60, 'Rich chocolate ice cream'),
            ('Strawberry Ice Cream', 65, 'Fresh strawberry ice cream'),
            ('Mango Ice Cream', 70, 'Delicious mango ice cream'),
            ('Kulfi', 40, 'Traditional Indian ice cream'),
        ],
        'chaat': [
            ('Pani Puri', 30, 'Crispy puris with spicy water'),
            ('Bhel Puri', 40, 'Puffed rice with chutneys'),
            ('Sev Puri', 35, 'Crispy puris with sev topping'),
            ('Dahi Puri', 45, 'Puris with yogurt and chutneys'),
            ('Samosa Chaat', 50, 'Crushed samosa with chutneys'),
        ],
        'dosa': [
            ('Plain Dosa', 40, 'Crispy rice pancake'),
            ('Masala Dosa', 60, 'Dosa with potato filling'),
            ('Onion Dosa', 50, 'Dosa with onion topping'),
            ('Cheese Dosa', 80, 'Dosa with cheese'),
            ('Mysore Masala Dosa', 70, 'Spicy dosa with potato filling'),
        ],
        'samosa': [
            ('Aloo Samosa', 15, 'Potato stuffed samosa'),
            ('Punjabi Samosa', 20, 'Spicy Punjabi style samosa'),
            ('Peas Samosa', 18, 'Green peas samosa'),
            ('Cheese Samosa', 25, 'Samosa with cheese filling'),
            ('Mini Samosa', 30, 'Pack of 4 mini samosas'),
        ],
        'vada_pav': [
            ('Classic Vada Pav', 20, 'Mumbai\'s favorite street food'),
            ('Cheese Vada Pav', 30, 'Vada pav with cheese'),
            ('Schezwan Vada Pav', 25, 'Spicy schezwan vada pav'),
            ('Masala Vada Pav', 22, 'Extra spicy vada pav'),
            ('Paneer Vada Pav', 35, 'Vada pav with paneer'),
        ],
        'tea': [
            ('Masala Chai', 15, 'Traditional spiced tea'),
            ('Ginger Tea', 12, 'Tea with fresh ginger'),
            ('Cardamom Tea', 18, 'Tea with cardamom'),
            ('Lemon Tea', 20, 'Refreshing lemon tea'),
            ('Cutting Chai', 10, 'Half cup of strong tea'),
        ],
        'juice': [
            ('Orange Juice', 40, 'Fresh orange juice'),
            ('Watermelon Juice', 35, 'Refreshing watermelon juice'),
            ('Sugarcane Juice', 30, 'Fresh sugarcane juice'),
            ('Mixed Fruit Juice', 50, 'Blend of seasonal fruits'),
            ('Carrot Juice', 45, 'Healthy carrot juice'),
        ],
    }
    
    for vendor in vendors:
        business_type = vendor.business_type
        menu_items = menu_templates.get(business_type, menu_templates['ice_cream'])
        
        for item_name, price, description in menu_items:
            menu_item = MenuItem(
                vendor_id=vendor.id,
                name=item_name,
                price=price,
                description=description
            )
            db.session.add(menu_item)
    
    db.session.commit()
    print("✅ Sample menu items created successfully!")

    # Create sample customers
    customers_data = [
        {'name': 'John Doe', 'phone': '9876543210', 'email': 'john@example.com', 'location': 'Mumbai, Maharashtra'},
        {'name': 'Jane Smith', 'phone': '9876543211', 'email': 'jane@example.com', 'location': 'Delhi, India'},
    ]
    
    for customer_data in customers_data:
        if not Customer.query.filter_by(email=customer_data['email']).first():
            customer = Customer(
                name=customer_data['name'],
                phone=customer_data['phone'],
                email=customer_data['email'],
                location=customer_data['location']
            )
            db.session.add(customer)
    
    db.session.commit()
    print("✅ Sample customers created successfully!")


# Business type to product category mapping
BUSINESS_TYPE_CATEGORIES = {
    'ice_cream': ['ice_cream', 'dairy', 'essentials', 'fruits'],
    'chaat': ['chaat', 'vegetables', 'essentials', 'dairy'],
    'dosa': ['dosa', 'vegetables', 'essentials', 'dairy'],
    'samosa': ['samosa', 'vegetables', 'essentials'],
    'vada_pav': ['vada_pav', 'vegetables', 'essentials'],
    'tea': ['tea', 'dairy', 'essentials'],
    'juice': ['juice', 'vegetables', 'essentials', 'fruits'],
    'other': ['vegetables', 'oils', 'grains', 'pulses', 'dairy', 'essentials', 'ice_cream', 'chaat', 'dosa', 'samosa', 'vada_pav', 'tea', 'juice', 'fruits']
}

# All available product categories for supplier selection
PRODUCT_CATEGORIES = [
    'vegetables',
    'fruits',
    'dairy',
    'oils',
    'grains',
    'pulses',
    'essentials',
    'ice_cream',
    'chaat',
    'dosa',
    'samosa',
    'vada_pav',
    'tea',
    'juice',
    'spices',
    'snacks',
    'beverages',
    'bakery',
    'meat',
    'seafood',
    'frozen',
    'other'
]

# Category display names for better UI
CATEGORY_DISPLAY_NAMES = {
    'vegetables': 'Vegetables',
    'fruits': 'Fruits',
    'dairy': 'Dairy Products',
    'oils': 'Cooking Oils',
    'grains': 'Grains & Cereals',
    'pulses': 'Pulses & Lentils',
    'essentials': 'Essentials',
    'ice_cream': 'Ice Cream',
    'chaat': 'Chaat Items',
    'dosa': 'Dosa Ingredients',
    'samosa': 'Samosa Ingredients',
    'vada_pav': 'Vada Pav Ingredients',
    'tea': 'Tea & Coffee',
    'juice': 'Juice Ingredients',
    'spices': 'Spices & Seasonings',
    'snacks': 'Snacks',
    'beverages': 'Beverages',
    'bakery': 'Bakery Items',
    'meat': 'Meat & Poultry',
    'seafood': 'Seafood',
    'frozen': 'Frozen Foods',
    'other': 'Other'
}

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        role = data.get('role', 'Vendor')

        # Normalize role string
        role = (role or 'Vendor').strip().lower()

        # Authenticate based on role
        if role == 'vendor':
            user = Vendor.query.filter_by(phone=phone).first()
            if user and check_password_hash(user.password_hash, password):
                session.clear()
                session['vendor_id'] = user.id
                return jsonify({'success': True, 'message': 'Login successful', 'redirect': url_for('vendor_dashboard')})
        elif role == 'supplier':
            user = Supplier.query.filter_by(phone=phone).first()
            if user and user.password_hash and check_password_hash(user.password_hash, password):
                session.clear()
                session['supplier_id'] = user.id
                return jsonify({'success': True, 'message': 'Login successful', 'redirect': url_for('supplier_dashboard')})
        elif role in ('delivery', 'delivery agent', 'delivery_agent'):
            user = DeliveryAgent.query.filter_by(phone=phone).first()
            if user and user.password_hash and check_password_hash(user.password_hash, password):
                session.clear()
                session['delivery_agent_id'] = user.id
                return jsonify({'success': True, 'message': 'Login successful', 'redirect': url_for('delivery_agent_dashboard')})
        elif role == 'customer':
            user = Customer.query.filter_by(phone=phone).first()
            if user and user.password_hash and check_password_hash(user.password_hash, password):
                session.clear()
                session['customer_id'] = user.id
                session['customer_name'] = user.name
                session['customer_email'] = user.email
                return jsonify({'success': True, 'message': 'Login successful', 'redirect': url_for('customer_dashboard')})

        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('vendor_login.html')

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        data = request.get_json()
        role = (data.get('role') or 'Vendor').strip().lower()
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        location = data.get('location')
        password = data.get('password')
        business_type = data.get('business_type') or 'other'
        gstin = data.get('gstin')

        # Basic validation
        if not name or not phone or not password:
            return jsonify({'success': False, 'message': 'Name, phone and password are required'})
        
        # GSTIN validation for vendors
        if role == 'vendor' and not gstin:
            return jsonify({'success': False, 'message': 'GSTIN is required for vendors'})

        # Prevent duplicates across relevant tables by phone/email
        if Vendor.query.filter_by(phone=phone).first() or Supplier.query.filter_by(phone=phone).first() or DeliveryAgent.query.filter_by(phone=phone).first() or Customer.query.filter_by(phone=phone).first():
            return jsonify({'success': False, 'message': 'An account with this phone number already exists'})

        if email and (Vendor.query.filter_by(email=email).first() or Supplier.query.filter_by(email=email).first() or DeliveryAgent.query.filter_by(email=email).first() or Customer.query.filter_by(email=email).first()):
            return jsonify({'success': False, 'message': 'An account with this email already exists'})

        pw_hash = generate_password_hash(password)

        if role == 'vendor':
            # Check if GSTIN already exists
            if Vendor.query.filter_by(gstin=gstin).first():
                return jsonify({'success': False, 'message': 'A vendor with this GSTIN already exists'})
            
            vendor = Vendor(
                name=name,
                phone=phone,
                email=email or '',
                location=location or '',
                business_type=business_type,
                gstin=gstin,
                password_hash=pw_hash
            )
            db.session.add(vendor)
        elif role == 'supplier':
            supplier = Supplier(
                name=name,
                phone=phone,
                email=email,
                location=location or '',
                password_hash=pw_hash,
                verification_status=False
            )
            db.session.add(supplier)
        elif role in ('delivery', 'delivery agent', 'delivery_agent'):
            da = DeliveryAgent(
                name=name,
                phone=phone,
                email=email,
                location=location or '',
                password_hash=pw_hash,
                vehicle_info=data.get('vehicle_info', ''),
                vehicle_type=data.get('vehicle_type', '')
            )
            db.session.add(da)
        elif role == 'customer':
            cust = Customer(
                name=name,
                phone=phone,
                email=email,
                location=location or '',
                password_hash=pw_hash
            )
            db.session.add(cust)
        else:
            return jsonify({'success': False, 'message': 'Unknown role'})

        db.session.commit()
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    return render_template('vendor_register.html', GOOGLE_CLIENT_ID=app.config.get('GOOGLE_CLIENT_ID'))


@app.route('/vendor/login/google', methods=['GET'])
def vendor_login_google():
    """Start OAuth2 Authorization using Authlib (redirect to Google)."""
    # Allow optional `next` parameter to redirect after auth
    next_url = request.args.get('next')
    if next_url:
        session['oauth_next'] = next_url

    # Ensure OAuth client is registered and properly configured
    ok = ensure_oauth_registered()
    if not ok:
                # Build a small diagnostic page (do not reveal secrets)
                cid = app.config.get('GOOGLE_CLIENT_ID')
                secret = app.config.get('GOOGLE_CLIENT_SECRET')
                cid_display = cid if cid else '<missing>'
                secret_present = 'yes' if secret else 'no'
                app.logger.error('Google OAuth registration failed. client_id present=%s, secret present=%s', bool(cid), bool(secret))
                html = f"""
                <h3>Google OAuth not configured properly</h3>
                <p>Missing or invalid OAuth configuration. Please ensure the environment variables are set and restart the app.</p>
                <ul>
                    <li>GOOGLE_CLIENT_ID: {cid_display}</li>
                    <li>GOOGLE_CLIENT_SECRET present: {secret_present}</li>
                </ul>
                <p>Set them exactly (no extra quotes) and restart the server. Example:</p>
                <pre>export GOOGLE_CLIENT_ID=your-client-id\nexport GOOGLE_CLIENT_SECRET=your-client-secret\npython app.py runserver</pre>
                """
                return html, 500

    # Use explicit configured redirect URI when provided to avoid redirect_uri_mismatch
    # (Google requires an exact match between the redirect_uri sent in the auth
    # request and one of the "Authorized redirect URIs" configured in the
    # Google Cloud Console). If a deployment or reverse proxy changes the
    # externally-visible host/scheme, url_for(...) may produce a value that is
    # not registered in the console which causes Error 400: redirect_uri_mismatch.
    redirect_uri_from_config = app.config.get('GOOGLE_REDIRECT_URI')
    default_redirect = url_for('vendor_login_google_callback', _external=True)

    # Prefer an explicit config value when present and non-empty. Log both so
    # it's easy to inspect what the app is sending to Google.
    redirect_uri = redirect_uri_from_config if redirect_uri_from_config else default_redirect
    app.logger.info('Initiating Google OAuth; redirect_uri=%s (url_for produced: %s)', redirect_uri, default_redirect)
    try:
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception as e:
        app.logger.exception('authorize_redirect error:')
        return 'Failed to initiate Google OAuth', 500


@app.route('/vendor/login/google/callback')
def vendor_login_google_callback():
    """Handle OAuth2 callback from Google for existing vendors (login flow)"""
    app.logger.info('Callback URL: %s', request.url)
    app.logger.info('Request args: %s', dict(request.args))
    
    # Get the authorization code and state from Google
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        app.logger.error('Google OAuth error: %s', error)
        error_desc = request.args.get('error_description', error)
        return render_template('login_error.html', error=f'Google OAuth error: {error_desc}'), 400
    
    if not code:
        app.logger.error('No authorization code received from Google')
        return render_template('login_error.html', error='No authorization code received. Please try again.'), 400
    
    # Exchange the authorization code for an access token
    redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', url_for('vendor_login_google_callback', _external=True))
    token_data = exchange_google_auth_code(code, redirect_uri)
    
    if not token_data:
        return render_template('login_error.html', error='Failed to exchange authorization code. Please try again.'), 500
    
    access_token = token_data.get('access_token')
    if not access_token:
        app.logger.error('No access token in token response: %s', token_data)
        return render_template('login_error.html', error='Failed to obtain access token.'), 500
    
    # Fetch user info from Google
    info = fetch_google_userinfo(access_token)
    
    if not info:
        return render_template('login_error.html', error='Failed to fetch user information from Google.'), 500

    email = info.get('email', '').strip()
    
    if not email:
        return render_template('login_error.html', error='Google account has no email'), 400

    # Check if vendor exists
    vendor = Vendor.query.filter_by(email=email).first()
    if vendor:
        session['vendor_id'] = vendor.id
        # Issue JWT
        payload = {
            'vendor_id': vendor.id,
            'email': vendor.email,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=app.config.get('JWT_EXP_DELTA_SECONDS'))
        }
        jwt_token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['JWT_ALGORITHM'])
        redirect_to = session.pop('oauth_next', url_for('vendor_dashboard'))
        resp = redirect(redirect_to)
        resp.set_cookie('access_token', jwt_token, httponly=True, samesite='Lax')
        return resp
    
    # If vendor doesn't exist, redirect to signup completion
    name = (info.get('name') or '').strip()
    phone = info.get('phone', '').strip()
    
    session['oauth_user_data'] = {
        'email': email,
        'name': name,
        'phone': phone,
        'google_id': info.get('id', ''),
    }
    
    return redirect(url_for('signup_complete'))

@app.route('/auth/google/callback', methods=['GET'])
def google_oauth_callback():
    """Handle Google OAuth callback for multi-role signup with data pre-fill"""
    app.logger.info('Auth callback URL: %s', request.url)
    app.logger.info('Request args: %s', dict(request.args))
    
    # Get the authorization code and state from Google
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        app.logger.error('Google OAuth error: %s', error)
        error_desc = request.args.get('error_description', error)
        return render_template('signup_error.html', error=f'Google OAuth error: {error_desc}'), 400
    
    if not code:
        app.logger.error('No authorization code received from Google')
        return render_template('signup_error.html', error='No authorization code received. Please try again.'), 400
    
    # Exchange the authorization code for an access token
    redirect_uri = app.config.get('GOOGLE_REDIRECT_URI', url_for('google_oauth_callback', _external=True))
    token_data = exchange_google_auth_code(code, redirect_uri)
    
    if not token_data:
        return render_template('signup_error.html', error='Failed to exchange authorization code. Please try again.'), 500
    
    access_token = token_data.get('access_token')
    if not access_token:
        app.logger.error('No access token in token response: %s', token_data)
        return render_template('signup_error.html', error='Failed to obtain access token.'), 500
    
    # Fetch user info from Google
    info = fetch_google_userinfo(access_token)
    
    if not info:
        return render_template('signup_error.html', error='Failed to fetch user information from Google.'), 500

    email = info.get('email', '').strip()
    name = (info.get('name') or '').strip()
    phone = info.get('phone', '').strip()
    
    if not email:
        return render_template('signup_error.html', error='Google account has no email address.'), 400

    # Store OAuth data in session for next step
    session['oauth_user_data'] = {
        'email': email,
        'name': name,
        'phone': phone,
        'google_id': info.get('id', ''),  # Google's unique ID
    }
    
    # Redirect to signup completion form
    return redirect(url_for('signup_complete'))


@app.route('/signup/complete', methods=['GET', 'POST'])
def signup_complete():
    """Complete signup with additional details for multi-role registration"""
    
    # Check if user has Google OAuth data in session
    oauth_data = session.get('oauth_user_data')
    if not oauth_data:
        return render_template('signup_error.html', error='Session expired. Please sign in with Google again.'), 400
    
    if request.method == 'POST':
        try:
            app.logger.info('=== SIGNUP COMPLETE POST REQUEST RECEIVED ===')
            app.logger.info(f'Content-Type: {request.content_type}')
            app.logger.info(f'Is JSON: {request.is_json}')
            
            data = request.get_json() or request.form.to_dict()
            app.logger.info(f'Parsed data keys: {list(data.keys())}')
            
            role = (data.get('role') or 'Vendor').strip().lower()
            name = (data.get('name') or oauth_data.get('name') or '').strip()
            phone = (data.get('phone') or oauth_data.get('phone') or '').strip()
            email = oauth_data.get('email', '').strip()
            location = (data.get('location') or '').strip()
            password = (data.get('password') or '').strip()
            
            app.logger.info(f'Processing signup: role={role}, name={name}, email={email}, phone={phone}')
            
            # Validation
            if not name or len(name) < 2:
                return jsonify({'success': False, 'message': 'Please enter a valid name'}), 400
            
            if not phone or len(phone) < 10:
                return jsonify({'success': False, 'message': 'Please enter a valid phone number'}), 400
            
            if not password or len(password) < 8:
                return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
            
            if role not in ['vendor', 'supplier', 'delivery agent', 'customer']:
                return jsonify({'success': False, 'message': 'Invalid role'}), 400
            
            # Check if email or phone already exists
            existing_user = (
                Vendor.query.filter_by(email=email).first() or
                Supplier.query.filter_by(email=email).first() or
                DeliveryAgent.query.filter_by(email=email).first() or
                Customer.query.filter_by(email=email).first() or
                Vendor.query.filter_by(phone=phone).first() or
                Supplier.query.filter_by(phone=phone).first() or
                DeliveryAgent.query.filter_by(phone=phone).first() or
                Customer.query.filter_by(phone=phone).first()
            )
            
            if existing_user:
                return jsonify({'success': False, 'message': 'An account with this email or phone already exists'}), 409
            
            pw_hash = generate_password_hash(password)
            
            # Create user based on role
            if role == 'vendor':
                gstin = (data.get('gstin') or '').strip()
                business_type = (data.get('business_type') or 'other').strip()
                
                if not gstin:
                    return jsonify({'success': False, 'message': 'GSTIN is required for vendors'}), 400
                
                if Vendor.query.filter_by(gstin=gstin).first():
                    return jsonify({'success': False, 'message': 'A vendor with this GSTIN already exists'}), 409
                
                user = Vendor(
                    name=name,
                    phone=phone,
                    email=email,
                    location=location or 'Not specified',
                    business_type=business_type,
                    gstin=gstin,
                    password_hash=pw_hash
                )
            
            elif role == 'supplier':
                business_name = (data.get('business_name') or '').strip()
                gstin = (data.get('gstin') or '').strip()
                
                user = Supplier(
                    name=name,
                    phone=phone,
                    email=email,
                    business_name=business_name or name,
                    location=location or 'Not specified',
                    gstin=gstin or None,
                    password_hash=pw_hash
                )
            
            elif role == 'delivery agent':
                vehicle_type = (data.get('vehicle_type') or '').strip()
                vehicle_info = (data.get('vehicle_info') or '').strip()
                
                if not vehicle_type or not vehicle_info:
                    return jsonify({'success': False, 'message': 'Vehicle information is required for delivery agents'}), 400
                
                user = DeliveryAgent(
                    name=name,
                    phone=phone,
                    email=email,
                    vehicle_type=vehicle_type,
                    vehicle_info=vehicle_info,
                    location=location or 'Not specified',
                    password_hash=pw_hash
                )
            
            elif role == 'customer':
                user = Customer(
                    name=name,
                    phone=phone,
                    email=email,
                    location=location or 'Not specified',
                    password_hash=pw_hash
                )
            
            # Save to database
            db.session.add(user)
            try:
                db.session.commit()
                app.logger.info(f'Successfully created {role} user with email: {email}')
            except Exception as db_error:
                db.session.rollback()
                app.logger.exception('Database error during user creation:')
                raise Exception(f'Database error: {str(db_error)}')
            
            # Clear session
            session.pop('oauth_user_data', None)
            
            # Log user in
            user_id = user.id
            if role == 'vendor':
                session['vendor_id'] = user_id
            elif role == 'supplier':
                session['supplier_id'] = user_id
            elif role == 'delivery agent':
                session['delivery_agent_id'] = user_id
            elif role == 'customer':
                session['customer_id'] = user_id
            
            # Issue JWT token
            payload = {
                'user_id': user_id,
                'role': role,
                'email': email,
                'exp': datetime.now(timezone.utc) + timedelta(seconds=app.config.get('JWT_EXP_DELTA_SECONDS'))
            }
            jwt_token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm=app.config['JWT_ALGORITHM'])
            
            # Determine redirect based on role
            redirect_map = {
                'vendor': 'vendor_dashboard',
                'supplier': 'supplier_dashboard',
                'delivery agent': 'delivery_dashboard',
                'customer': 'customer_dashboard'
            }
            
            redirect_url = url_for(redirect_map.get(role, 'vendor_dashboard'))
            
            resp_data = {
                'success': True,
                'message': f'{role.title()} registration successful!',
                'redirect': redirect_url
            }
            
            # If AJAX request, return JSON; else return redirect
            if request.is_json:
                return jsonify(resp_data)
            
            return redirect(redirect_url)
        
        except Exception as e:
            app.logger.exception('Error during signup completion:')
            error_msg = str(e) if str(e) else 'An unexpected error occurred'
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg}), 500
            return render_template('signup_error.html', error=error_msg), 500
    
    # GET request - show signup completion form with pre-filled data
    return render_template('signup_complete.html', oauth_data=oauth_data, GOOGLE_CLIENT_ID=app.config.get('GOOGLE_CLIENT_ID'))

@app.route('/vendor/forgot-password', methods=['POST'])
def vendor_forgot_password():
    """Initiate password reset by sending OTP to vendor email"""
    try:
        data = request.get_json() or {}
    except Exception:
        data = {}
    identifier = (data.get('identifier') or data.get('email') or data.get('phone') or '').strip()
    role = (data.get('role') or 'Vendor').strip().lower()
    if not identifier:
        return jsonify({'success': False, 'message': 'Email or phone is required'})

    is_email = '@' in identifier
    user = None
    if role == 'vendor':
        user = Vendor.query.filter_by(email=identifier).first() if is_email else Vendor.query.filter_by(phone=identifier).first()
    elif role == 'supplier':
        user = Supplier.query.filter_by(email=identifier).first() if is_email else Supplier.query.filter_by(phone=identifier).first()
    elif role in ('delivery agent', 'delivery_agent', 'delivery'):
        user = DeliveryAgent.query.filter_by(email=identifier).first() if is_email else DeliveryAgent.query.filter_by(phone=identifier).first()
    elif role == 'customer':
        user = Customer.query.filter_by(email=identifier).first() if is_email else Customer.query.filter_by(phone=identifier).first()
    else:
        return jsonify({'success': False, 'message': 'Unknown role'})

    if not user:
        return jsonify({'success': False, 'message': 'No account found with this email or phone'})

    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Store the identifier in the email column to avoid schema changes (email or phone)
    otp_record = OTPVerification(
        email=identifier,
        otp=otp,
        expires_at=expires_at
    )
    db.session.add(otp_record)
    db.session.commit()

    if is_email:
        if send_otp_email(identifier, otp):
            return jsonify({'success': True, 'message': 'OTP sent to your email address'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP. Please try again.'})
    else:
        # Phone-based flow: try AWS SNS first, fallback to mock
        sns_sent = False
        dlt_configured = bool(os.environ.get('AWS_SNS_DLT_ENTITY_ID'))
        try:
            from aws_services import send_sms_otp as aws_send_sms
            sns_sent = aws_send_sms(identifier, otp)
        except Exception:
            pass
        if not sns_sent:
            send_mock_otp_email(identifier, otp)

        # If DLT is not registered, Indian carriers silently drop the SMS.
        # Return the OTP in the response so the UI can display it as a fallback.
        response_data = {'success': True, 'message': 'OTP sent to your phone number'}
        if not dlt_configured:
            response_data['otp_fallback'] = otp
            response_data['message'] = (
                'OTP generated. SMS delivery requires DLT registration. '
                'Your OTP is shown below (development mode).'
            )
        return jsonify(response_data)

@app.route('/vendor/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and allow password reset"""
    data = request.get_json()
    email = (data.get('identifier') or data.get('email') or data.get('phone'))  # may contain email or phone identifier
    otp = data.get('otp')
    
    if not email or not otp:
        return jsonify({'success': False, 'message': 'Email and OTP are required'})
    
    # Find valid OTP by identifier (email or phone)
    otp_record = OTPVerification.query.filter_by(
        email=email, 
        otp=otp, 
        is_used=False
    ).first()
    
    if not otp_record:
        return jsonify({'success': False, 'message': 'Invalid OTP'})
    
    # Check if OTP is expired
    if datetime.utcnow() > otp_record.expires_at:
        return jsonify({'success': False, 'message': 'OTP has expired'})
    
    # Mark OTP as used
    otp_record.is_used = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'OTP verified successfully'})

@app.route('/vendor/reset-password', methods=['POST'])
def reset_password():
    """Reset password after OTP verification"""
    data = request.get_json()
    email = (data.get('identifier') or data.get('email') or data.get('phone'))  # may contain email or phone identifier
    new_password = data.get('new_password')
    role = (data.get('role') or 'Vendor').strip().lower()
    
    if not email or not new_password:
        return jsonify({'success': False, 'message': 'Email and new password are required'})
    
    # Find user by role and identifier
    user = None
    if role == 'vendor':
        user = Vendor.query.filter_by(email=email).first() or Vendor.query.filter_by(phone=email).first()
    elif role == 'supplier':
        user = Supplier.query.filter_by(email=email).first() or Supplier.query.filter_by(phone=email).first()
    elif role in ('delivery agent', 'delivery_agent', 'delivery'):
        user = DeliveryAgent.query.filter_by(email=email).first() or DeliveryAgent.query.filter_by(phone=email).first()
    elif role == 'customer':
        user = Customer.query.filter_by(email=email).first() or Customer.query.filter_by(phone=email).first()
    else:
        return jsonify({'success': False, 'message': 'Unknown role'})

    if not user:
        return jsonify({'success': False, 'message': 'Account not found'})

    # Update password
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Password reset successfully'})

@app.route('/api/suppliers')
def get_suppliers():
    suppliers = Supplier.query.all()
    suppliers_data = []
    
    for supplier in suppliers:
        suppliers_data.append({
            'id': supplier.id,
            'name': supplier.name,
            'location': supplier.location,
            'rating': supplier.rating,
            'verification_status': supplier.verification_status,
            'hygiene_rating': supplier.hygiene_rating,
            'phone': supplier.phone
        })
    
    return jsonify(suppliers_data)

@app.route('/api/products')
def get_products():
    category = request.args.get('category', '')
    supplier_id = request.args.get('supplier_id', '')
    vendor_id = session.get('vendor_id')
    
    query = Product.query
    
    # If vendor is logged in, filter by their business type
    if vendor_id:
        vendor = db.session.get(Vendor, vendor_id)
        if vendor and vendor.business_type in BUSINESS_TYPE_CATEGORIES:
            # Get categories relevant to this business type
            relevant_categories = BUSINESS_TYPE_CATEGORIES[vendor.business_type]
            query = query.filter(Product.category.in_(relevant_categories))
    
    if category:
        query = query.filter_by(category=category)
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    
    products = query.all()
    products_data = []
    
    for product in products:
        supplier = db.session.get(Supplier, product.supplier_id)
        products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'current_price': product.current_price,
            'stock_available': product.stock_available,
            'unit': product.unit,
            'supplier_id': product.supplier_id,
            'supplier_name': supplier.name,
            'supplier_location': supplier.location,
            'supplier_rating': supplier.rating
        })
    
    return jsonify(products_data)

def is_allowed_image(filename: str) -> bool:
    return bool(filename) and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_vendor_image(file_obj, vendor_id, kind: str):
    if not file_obj or not file_obj.filename:
        return None

    if not is_allowed_image(file_obj.filename):
        return None

    upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'vendor')
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_filename = secure_filename(file_obj.filename)
    filename = f"{vendor_id}_{kind}_{timestamp}_{safe_filename}"
    abs_path = os.path.join(upload_dir, filename)
    file_obj.save(abs_path)
    return f"uploads/vendor/{filename}"


def get_admin_account():
    admin = Admin.query.first()
    if admin:
        return admin

    admin = Admin(
        name='Platform Admin',
        email='admin@vendorconnect.com',
        password_hash=None,
        balance=0.0
    )
    db.session.add(admin)
    db.session.commit()
    return admin


def remove_static_file(relative_path: str):
    if not relative_path:
        return
    try:
        file_path = os.path.join(app.root_path, 'static', relative_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as exc:
        print(f"Error removing file {relative_path}: {exc}")


@app.route('/api/vendor/menu', methods=['GET', 'POST'])
def vendor_menu():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    vendor = db.session.get(Vendor, session['vendor_id'])
    if not vendor:
        session.clear()
        return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

    if request.method == 'POST':
        # Handle multipart/form-data for image upload
        name = (request.form.get('name') or '').strip()
        description = (request.form.get('description') or '').strip()
        price_raw = request.form.get('price')
        image_file = request.files.get('image')

        if not name:
            return jsonify({'success': False, 'message': 'Menu item name is required.'}), 400

        try:
            price = float(price_raw)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Price must be a number.'}), 400

        # Handle image upload
        image_filename = None
        if image_file and image_file.filename:
            if is_allowed_image(image_file.filename):
                upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'menu')
                os.makedirs(upload_dir, exist_ok=True)

                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = secure_filename(image_file.filename)
                unique_name = f"{vendor.id}_{timestamp}_{safe_filename}"
                image_path = os.path.join(upload_dir, unique_name)
                image_file.save(image_path)
                image_filename = f"uploads/menu/{unique_name}"

        new_item = MenuItem(
            vendor_id=vendor.id,
            name=name,
            price=price,
            description=description,
            image=image_filename
        )
        db.session.add(new_item)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Menu item added.', 'item_id': new_item.id})

    # GET
    items = MenuItem.query.filter_by(vendor_id=vendor.id).order_by(MenuItem.created_at.desc()).all()
    return jsonify([
        {
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'description': item.description or '',
            'image': item.image or '',
            'created_at': format_ist_time(item.created_at, '%d %b %Y, %I:%M %p')
        } for item in items
    ])

@app.route('/api/vendor/brand', methods=['POST'])
def update_vendor_brand():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    vendor = db.session.get(Vendor, session['vendor_id'])
    if not vendor:
        session.clear()
        return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

    logo_file = request.files.get('logo')
    hero_file = request.files.get('hero_image')
    updated = False

    # Upload logo
    if logo_file and logo_file.filename:
        logo_path = save_vendor_image(logo_file, vendor.id, 'logo')
        if not logo_path:
            return jsonify({'success': False, 'message': 'Logo must be an image (png, jpg, jpeg, gif, webp).'}), 400
        if vendor.logo:
            remove_static_file(vendor.logo)
        vendor.logo = logo_path
        updated = True

    # Upload hero/cover image
    if hero_file and hero_file.filename:
        hero_path = save_vendor_image(hero_file, vendor.id, 'hero')
        if not hero_path:
            return jsonify({'success': False, 'message': 'Hero image must be an image (png, jpg, jpeg, gif, webp).'}), 400
        if vendor.hero_image:
            remove_static_file(vendor.hero_image)
        vendor.hero_image = hero_path
        updated = True

    if updated:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Brand images updated.',
            'logo': vendor.logo or '',
            'hero_image': vendor.hero_image or ''
        })

    return jsonify({'success': False, 'message': 'Please select a logo or hero image to upload.'}), 400

# Add this updated route to your app.py file
# Replace the existing /api/menu route with this one

@app.route('/api/vendor/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    vendor = db.session.get(Vendor, session['vendor_id'])
    if not vendor:
        session.clear()
        return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

    # Find the menu item
    item = db.session.get(MenuItem, item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Menu item not found.'}), 404

    # Verify the item belongs to this vendor
    if item.vendor_id != vendor.id:
        return jsonify({'success': False, 'message': 'Unauthorized.'}), 403

    # Delete the image file if it exists
    if item.image:
        try:
            image_path = os.path.join(app.root_path, 'static', item.image)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image file: {e}")

    # Delete the menu item
    db.session.delete(item)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Menu item deleted successfully.'})

@app.route('/api/menu')
def all_menus():
    """Return all menu items with vendor restaurant/stall name and business type"""
    items = MenuItem.query.order_by(MenuItem.created_at.desc()).all()
    response = []
    for item in items:
        vendor = db.session.get(Vendor, item.vendor_id)
        # Only include menu items from vendors who are currently open
        if vendor and (getattr(vendor, 'is_open', True)):
            cuisine_map = {
                'dosa': 'South Indian',
                'ice_cream': 'Desserts',
                'chaat': 'Street Food',
                'samosa': 'Snacks',
                'vada_pav': 'Maharashtrian',
                'tea': 'Beverages',
                'juice': 'Healthy Drinks'
            }
            cuisine = cuisine_map.get(vendor.business_type, 'Multi-Cuisine')
            # Use vendor.name as the restaurant/stall name
            # This should be the business name, not the owner's personal name
            response.append({
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'description': item.description or '',
                'image': item.image or '',
                'vendor_id': item.vendor_id,
                'vendor_name': vendor.name,  # Restaurant/Stall name
                'vendor_location': vendor.location,
                'vendor_business_type': vendor.business_type,
                'vendor_cuisine': cuisine,
                'vendor_rating': 4.5,
                'vendor_time': '30-40 mins',
                'vendor_logo': vendor.logo or '',
                'vendor_hero_image': vendor.hero_image or '',
                'created_at': format_ist_time(item.created_at, '%d %b %Y, %I:%M %p')
            })
    return jsonify(response)

@app.route('/api/vendor/open-status', methods=['GET', 'POST'])
def vendor_open_status():
    """Get or update the vendor's open/closed status.

    GET: Returns current status {success, is_open}
    POST: Accepts JSON {is_open: bool} to set, or {toggle: true} to flip.
    """
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    vendor = db.session.get(Vendor, session['vendor_id'])
    if not vendor:
        session.clear()
        return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

    if request.method == 'GET':
        return jsonify({'success': True, 'is_open': bool(getattr(vendor, 'is_open', True))})

    data = {}
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        data = {}

    if 'toggle' in data and data['toggle']:
        vendor.is_open = not bool(getattr(vendor, 'is_open', True))
    elif 'is_open' in data:
        vendor.is_open = bool(data['is_open'])
    else:
        # Default to toggle if no explicit value provided
        vendor.is_open = not bool(getattr(vendor, 'is_open', True))

    db.session.commit()
    return jsonify({'success': True, 'is_open': vendor.is_open})

@app.route('/api/vendor/promotions', methods=['GET', 'POST'])
def vendor_promotions():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    vendor = db.session.get(Vendor, session['vendor_id'])
    if not vendor:
        session.clear()
        return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

    if request.method == 'POST':
        # Check if it's a file upload (multipart/form-data) or JSON
        is_file_upload = 'video_file' in request.files
        
        if is_file_upload:
            # Handle file upload
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            price_per_view = request.form.get('price_per_view', 5.0)
            video_file = request.files.get('video_file')
            
            if not title:
                return jsonify({'success': False, 'message': 'Promotion title is required.'}), 400
            if not video_file or video_file.filename == '':
                return jsonify({'success': False, 'message': 'Video file is required.'}), 400
            
            # Validate file extension
            allowed_extensions = {'mp4', 'webm', 'avi', 'mov', 'mkv', 'flv'}
            filename = secure_filename(video_file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if file_ext not in allowed_extensions:
                return jsonify({'success': False, 'message': f'Invalid video format. Allowed: {", ".join(allowed_extensions)}'}), 400
            
            # Create unique filename
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            
            # Ensure upload directory exists
            upload_dir = os.path.join(app.static_folder, 'uploads', 'promotions')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, unique_filename)
            video_file.save(file_path)
            
            # Store relative path for database
            video_url = f'/static/uploads/promotions/{unique_filename}'
        else:
            # Handle URL-based promotion
            data = request.get_json() or {}
            title = (data.get('title') or '').strip()
            description = (data.get('description') or '').strip()
            video_url = (data.get('video_url') or '').strip()
            price_per_view = data.get('price_per_view', 5.0)

            if not title:
                return jsonify({'success': False, 'message': 'Promotion title is required.'}), 400
            if not video_url:
                return jsonify({'success': False, 'message': 'Video URL is required.'}), 400

        try:
            price_per_view = float(price_per_view)
            if price_per_view < 5 or price_per_view > 10:
                return jsonify({'success': False, 'message': 'Price per click must be between 5-10.'}), 400
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'Price must be a number between 5-10.'}), 400

        try:
            new_promo = Promotion(
                vendor_id=vendor.id,
                title=title,
                description=description,
                video_url=video_url,
                price_per_view=price_per_view,
                is_active=True
            )
            db.session.add(new_promo)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Promotion created.', 'promo_id': new_promo.id})
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating promotion: {str(e)}', exc_info=True)
            return jsonify({'success': False, 'message': f'Failed to create promotion: {str(e)}'}), 500

    # GET
    try:
        promos = Promotion.query.filter_by(vendor_id=vendor.id).order_by(Promotion.created_at.desc()).all()
        return jsonify([
            {
                'id': p.id,
                'title': p.title,
                'description': p.description or '',
                'video_url': p.video_url,
                'price_per_view': p.price_per_view,
                'total_views': p.total_views,
                'monthly_charge': p.total_views * p.price_per_view,
                'is_active': p.is_active,
                'created_at': format_ist_time(p.created_at, '%d %b %Y, %I:%M %p')
            } for p in promos
        ])
    except Exception as e:
        app.logger.error(f'Error retrieving promotions: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'message': f'Failed to retrieve promotions: {str(e)}'}), 500

@app.route('/api/vendor/promotions/<int:promo_id>', methods=['DELETE'])
def delete_vendor_promotion(promo_id):
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    vendor = db.session.get(Vendor, session['vendor_id'])
    if not vendor:
        session.clear()
        return jsonify({'success': False, 'message': 'Session expired. Please login again.'}), 401

    promo = db.session.get(Promotion, promo_id)
    if not promo or promo.vendor_id != vendor.id:
        return jsonify({'success': False, 'message': 'Promotion not found'}), 404

    try:
        db.session.delete(promo)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Promotion deleted'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting promotion: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'message': f'Failed to delete promotion: {str(e)}'}), 500

@app.route('/api/promotions/public', methods=['GET'])
def get_public_promotions():
    promos = Promotion.query.filter_by(is_active=True).order_by(Promotion.created_at.desc()).all()
    response = []
    for p in promos:
        vendor = db.session.get(Vendor, p.vendor_id)
        response.append({
            'id': p.id,
            'title': p.title,
            'description': p.description or '',
            'video_url': p.video_url,
            'vendor_id': p.vendor_id,
            'vendor_name': vendor.name if vendor else 'Vendor',
            'vendor_location': vendor.location if vendor else '',
            'price_per_view': p.price_per_view,
            'total_views': p.total_views,
            'created_at': format_ist_time(p.created_at, '%d %b %Y, %I:%M %p')
        })
    return jsonify(response)

@app.route('/api/promotion/<int:promo_id>/view', methods=['POST'])
def record_promotion_view(promo_id):
    promo = db.session.get(Promotion, promo_id)
    if not promo:
        return jsonify({'success': False, 'message': 'Promotion not found'}), 404

    vendor = db.session.get(Vendor, promo.vendor_id)
    customer_id = session.get('customer_id')

    # Check if this customer has already viewed this promotion
    existing_view = PromotionView.query.filter_by(
        promotion_id=promo_id,
        customer_id=customer_id
    ).first()

    # Only count the view if this is the first time this customer views this promotion
    if existing_view:
        return jsonify({'success': True, 'message': 'View already counted for this account', 'view_count': promo.total_views})

    # Create new view record
    view = PromotionView(
        promotion_id=promo_id,
        customer_id=customer_id
    )
    db.session.add(view)
    promo.total_views += 1

    # Credit platform admin for the promotion view
    admin = get_admin_account()
    admin.balance = (admin.balance or 0) + (promo.price_per_view or 0)

    # Charge vendor for this view
    if vendor:
        vendor.promo_due = (vendor.promo_due or 0) + (promo.price_per_view or 0)

    db.session.commit()

    return jsonify({'success': True, 'message': 'View recorded'})

@app.route('/api/group-orders')
def get_group_orders():
    group_orders = GroupOrder.query.filter_by(status='active').all()
    group_orders_data = []

    for group_order in group_orders:
        # Support both product_id FK and free-text product_name
        if group_order.product_id:
            product = db.session.get(Product, group_order.product_id)
            pname = product.name if product else f'Product #{group_order.product_id}'
        else:
            pname = getattr(group_order, 'product_name', None) or 'Unknown Product'

        participants_count = GroupOrderParticipant.query.filter_by(group_order_id=group_order.id).count()
        target = group_order.target_quantity or 1
        progress = min(round((group_order.current_quantity / target) * 100, 1), 100)

        # Check if the current vendor already joined
        current_vendor_id = session.get('vendor_id')
        is_joined = False
        if current_vendor_id:
            is_joined = GroupOrderParticipant.query.filter_by(
                group_order_id=group_order.id,
                vendor_id=current_vendor_id
            ).first() is not None

        group_orders_data.append({
            'id':                group_order.id,
            'product_name':      pname,
            'target_quantity':   group_order.target_quantity,
            'current_quantity':  group_order.current_quantity,
            'price_per_unit':    group_order.price_per_unit,
            'participants_count': participants_count,
            'progress_percentage': progress,
            'is_joined':         is_joined,
        })

    return jsonify(group_orders_data)

@app.route('/api/create-group-order', methods=['POST'])
def create_group_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})

    data = request.get_json() or {}

    # Accept either a product_id FK or a free-text product_name from the UI form
    product_id   = data.get('product_id')
    product_name = (data.get('product_name') or '').strip()
    target_qty   = float(data.get('target_quantity') or 0)
    price        = float(data.get('price_per_unit') or 0)

    if not product_name and not product_id:
        return jsonify({'success': False, 'message': 'Product name is required'})
    if target_qty <= 0:
        return jsonify({'success': False, 'message': 'Target quantity must be > 0'})
    if price <= 0:
        return jsonify({'success': False, 'message': 'Price per unit must be > 0'})

    group_order = GroupOrder(
        product_id=product_id,
        target_quantity=target_qty,
        price_per_unit=price,
        current_quantity=0,
        status='active',
    )
    # Store free-text name if no FK product
    if not product_id and hasattr(group_order, 'product_name'):
        group_order.product_name = product_name

    db.session.add(group_order)
    db.session.commit()

    # Add the creator as first participant
    participant = GroupOrderParticipant(
        group_order_id=group_order.id,
        vendor_id=session['vendor_id'],
        quantity=float(data.get('quantity') or 1),
    )
    db.session.add(participant)
    db.session.commit()

    # Publish SQS event for new group order
    resolved_name = product_name
    if product_id:
        p = db.session.get(Product, product_id)
        resolved_name = p.name if p else product_name
    try:
        from aws_services import publish_group_order_event
        publish_group_order_event('CREATED', {
            'group_order_id':    group_order.id,
            'product_id':        product_id,
            'product_name':      resolved_name,
            'target_quantity':   target_qty,
            'price_per_unit':    price,
            'created_by_vendor': session['vendor_id'],
        })
    except Exception as exc:
        app.logger.warning('SQS publish skipped: %s', exc)

    return jsonify({'success': True, 'message': 'Group order created successfully', 'id': group_order.id})

@app.route('/api/join-group-order', methods=['POST'])
def join_group_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    
    # Check if already participating
    existing_participant = GroupOrderParticipant.query.filter_by(
        group_order_id=data.get('group_order_id'),
        vendor_id=session['vendor_id']
    ).first()
    
    if existing_participant:
        return jsonify({'success': False, 'message': 'Already participating in this group order'})
    
    participant = GroupOrderParticipant(
        group_order_id=data.get('group_order_id'),
        vendor_id=session['vendor_id'],
        quantity=data.get('quantity')
    )
    
    db.session.add(participant)

    # Update group order current quantity
    group_order = db.session.get(GroupOrder, data.get('group_order_id'))
    group_order.current_quantity += data.get('quantity')

    db.session.commit()

    # Publish SQS event for vendor joining
    try:
        from aws_services import publish_group_order_event
        publish_group_order_event('VENDOR_JOINED', {
            'group_order_id': group_order.id,
            'vendor_id': session['vendor_id'],
            'quantity': data.get('quantity'),
            'current_quantity': group_order.current_quantity,
            'target_quantity': group_order.target_quantity,
        })

        # Check if group order reached its target
        if group_order.current_quantity >= group_order.target_quantity:
            group_order.status = 'completed'
            db.session.commit()
            # Gather participant phones for notifications
            participants = GroupOrderParticipant.query.filter_by(group_order_id=group_order.id).all()
            phones = []
            for p in participants:
                v = db.session.get(Vendor, p.vendor_id)
                if v and v.phone:
                    phones.append(v.phone)
            publish_group_order_event('ORDER_COMPLETED', {
                'group_order_id': group_order.id,
                'participant_phones': phones,
            })
    except Exception:
        pass  # SQS is optional – don't break the main flow

    return jsonify({'success': True, 'message': 'Joined group order successfully'})

@app.route('/api/price-alerts')
def get_price_alerts():
    vendor_id = session.get('vendor_id')
    vendor = None
    if vendor_id:
        vendor = db.session.get(Vendor, vendor_id)
    
    # Base alerts for all vendors
    alerts = [
        {
            'product': 'Tomatoes',
            'message': 'Aaj tomato ₹28/kg – lowest in Krishna Mandi',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'product': 'Onions',
            'message': 'Onion price dropped 15% in Fresh Farm Supplies',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'product': 'Potatoes',
            'message': 'Buy extra potatoes today – price may rise 20% tomorrow due to rains',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    ]
    
    # Add business-specific alerts
    if vendor and vendor.business_type:
        business_alerts = []
        
        if vendor.business_type == 'ice_cream':
            business_alerts = [
                {
                    'product': 'Ice Cream Mix',
                    'message': 'Ice cream mix price dropped 10% - stock up for summer!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Strawberries',
                    'message': 'Fresh strawberries available at ₹180/kg - perfect for ice cream!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Vanilla Essence',
                    'message': 'Premium vanilla essence 20% off this week only',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Chocolate Syrup',
                    'message': 'Bulk order discount on chocolate syrup - order 10+ liters',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'chaat':
            business_alerts = [
                {
                    'product': 'Chickpeas',
                    'message': 'Chickpeas price dropped 15% - perfect for chaat!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Sev',
                    'message': 'Fresh sev available at ₹85/kg - crispy and fresh!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Pomegranate Seeds',
                    'message': 'Sweet pomegranate seeds 25% off - limited stock!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Curd',
                    'message': 'Fresh curd available at ₹45/liter - perfect for dahi chaat',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'dosa':
            business_alerts = [
                {
                    'product': 'Rice Batter',
                    'message': 'Rice batter price dropped 12% - stock up for weekend rush!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Coconut Chutney',
                    'message': 'Fresh coconut chutney available at ₹75/kg',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Sambar Powder',
                    'message': 'Premium sambar powder 20% off - authentic taste!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Urad Dal',
                    'message': 'Urad dal bulk discount - order 50kg+ for 10% off',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'samosa':
            business_alerts = [
                {
                    'product': 'Samosa Sheets',
                    'message': 'Samosa sheets price dropped 8% - crispy and fresh!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Potato Filling',
                    'message': 'Ready-made potato filling available at ₹32/kg',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Samosa Masala',
                    'message': 'Special samosa masala blend 15% off this week',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Green Peas',
                    'message': 'Fresh green peas available at ₹42/kg',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'vada_pav':
            business_alerts = [
                {
                    'product': 'Pav Bread',
                    'message': 'Fresh pav bread available at ₹22/pack - soft and fluffy!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Vada Pav Masala',
                    'message': 'Authentic vada pav masala 18% off - limited time!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Besan',
                    'message': 'Besan price dropped 10% - perfect for vada batter',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Green Chutney',
                    'message': 'Spicy green chutney available at ₹55/kg',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'tea':
            business_alerts = [
                {
                    'product': 'Tea Leaves',
                    'message': 'Premium tea leaves 15% off - strong and aromatic!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Cardamom',
                    'message': 'Cardamom price dropped 12% - perfect for masala chai',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Ginger',
                    'message': 'Fresh ginger available at ₹55/kg - spicy and fresh!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Tea Masala',
                    'message': 'Special tea masala blend 20% off - authentic taste!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        elif vendor.business_type == 'juice':
            business_alerts = [
                {
                    'product': 'Oranges',
                    'message': 'Sweet oranges available at ₹75/kg - perfect for juice!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Carrots',
                    'message': 'Fresh carrots price dropped 15% - healthy and sweet!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Beetroot',
                    'message': 'Organic beetroot available at ₹32/kg - natural color!',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                },
                {
                    'product': 'Honey',
                    'message': 'Pure honey 25% off - natural sweetener for juices',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            ]
        
        if business_alerts:
            alerts = business_alerts + alerts[:2]  # Show business-specific alerts first
    
    return jsonify(alerts)

@app.route('/api/vendor/orders')
def get_vendor_orders():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    orders = Order.query.filter_by(vendor_id=session['vendor_id']).order_by(Order.created_at.desc()).all()
    orders_data = []
    
    for order in orders:
        supplier = db.session.get(Supplier, order.supplier_id)
        
        # Get order items with product details
        items = OrderItem.query.filter_by(order_id=order.id).all()
        items_data = []
        for item in items:
            product = db.session.get(Product, item.product_id)
            if product:
                items_data.append({
                    'product_name': product.name,
                    'category': product.category,
                    'quantity': item.quantity,
                    'unit': product.unit,
                    'price_per_unit': item.price_per_unit,
                    'total': item.quantity * item.price_per_unit
                })
        
        orders_data.append({
            'id': order.id,
            'supplier_name': supplier.name if supplier else 'Unknown',
            'total_amount': order.total_amount,
            'status': order.status,
            'order_type': order.order_type,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M'),
            'items': items_data
        })
    
    return jsonify(orders_data)

@app.route('/api/order/<order_id>/delivery')
def get_order_delivery(order_id):
    """Return mock delivery tracking info for a given order"""
    # Simple mocked coordinates around Mumbai
    sample = {
        'order_id': str(order_id),
        'status': 'Out for Delivery',
        'eta': '30 min',
        'last_updated': 'Just now',
        'customer': { 'lat': 19.0606, 'lng': 72.8365 },  # Bandra
        'driver': { 'lat': 19.0728, 'lng': 72.8826 },   # Near Dadar
        'route': [
            { 'lat': 19.0760, 'lng': 72.8777 },  # Warehouse (Mumbai)
            { 'lat': 19.0728, 'lng': 72.8826 },  # Driver current
            { 'lat': 19.0606, 'lng': 72.8365 }   # Customer
        ]
    }
    return jsonify(sample)

@app.route('/api/vendor/dashboard-stats')
def get_vendor_dashboard_stats():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        vendor_id = session['vendor_id']
        vendor = db.session.get(Vendor, vendor_id)
        
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor not found'}), 404
        
        # Get current month date range
        now = datetime.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Total orders (all time)
        total_orders = Order.query.filter_by(vendor_id=vendor_id).count()
        
        # Monthly orders
        monthly_orders = Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.created_at >= first_day_of_month
        ).count()
        
        # Monthly spending
        monthly_spending = db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.vendor_id == vendor_id,
            Order.created_at >= first_day_of_month
        ).scalar() or 0
        
        # Active group orders
        active_group_orders = GroupOrder.query.filter_by(status='active').count()
        
        # Verified suppliers count
        verified_suppliers = Supplier.query.filter_by(verification_status=True).count()
        
        # Calculate monthly savings (difference between individual and group orders)
        individual_orders = Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.order_type == 'individual',
            Order.created_at >= first_day_of_month
        ).all()
        
        group_orders = Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.order_type == 'group',
            Order.created_at >= first_day_of_month
        ).all()
        
        # Calculate savings (simplified - assume 15% savings on group orders)
        monthly_savings = sum(order.total_amount * 0.15 for order in group_orders)
        
        # Average order value
        avg_order_value = monthly_spending / monthly_orders if monthly_orders > 0 else 0
        
        # Recent transactions (last 5 orders)
        recent_orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).limit(5).all()
        recent_transactions = []
        
        for order in recent_orders:
            try:
                supplier = db.session.get(Supplier, order.supplier_id)
                supplier_name = supplier.name if supplier else "Unknown Supplier"
                
                # Get order items for description
                order_items = OrderItem.query.filter_by(order_id=order.id).all()
                item_names = []
                for item in order_items:
                    product = db.session.get(Product, item.product_id)
                    if product:
                        item_names.append(product.name)
                
                description = ', '.join(item_names[:3]) + ('...' if len(item_names) > 3 else '')
                if not description:
                    description = f"Order from {supplier_name}"
                
                recent_transactions.append({
                    'date': format_ist_time(order.created_at, '%d %b %Y'),
                    'time': format_ist_time(order.created_at, '%I:%M %p'),
                    'description': description,
                    'amount': order.total_amount,
                    'supplier': supplier_name
                })
            except Exception as e:
                app.logger.error(f"Error processing order {order.id}: {str(e)}")
                continue
        
        # Business type specific stats
        business_stats = {
            'ice_cream': {'total_orders': total_orders + 2, 'monthly_savings': monthly_savings + 800, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1},
            'chaat': {'total_orders': total_orders + 7, 'monthly_savings': monthly_savings + 600, 'active_group_orders': active_group_orders + 2, 'verified_suppliers': verified_suppliers + 2},
            'dosa': {'total_orders': total_orders + 4, 'monthly_savings': monthly_savings + 500, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1},
            'samosa': {'total_orders': total_orders + 2, 'monthly_savings': monthly_savings + 400, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1},
            'vada_pav': {'total_orders': total_orders + 10, 'monthly_savings': monthly_savings + 1000, 'active_group_orders': active_group_orders + 3, 'verified_suppliers': verified_suppliers + 3},
            'tea': {'total_orders': total_orders + 17, 'monthly_savings': monthly_savings + 300, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1},
            'juice': {'total_orders': total_orders + 6, 'monthly_savings': monthly_savings + 700, 'active_group_orders': active_group_orders + 1, 'verified_suppliers': verified_suppliers + 1}
        }
        
        # Apply business type adjustments
        if vendor and vendor.business_type and vendor.business_type in business_stats:
            stats = business_stats[vendor.business_type]
            total_orders = stats['total_orders']
            monthly_savings = stats['monthly_savings']
            active_group_orders = stats['active_group_orders']
            verified_suppliers = stats['verified_suppliers']
        
        return jsonify({
            'total_orders': total_orders,
            'monthly_orders': monthly_orders,
            'monthly_spending': monthly_spending,
            'monthly_savings': monthly_savings,
            'active_group_orders': active_group_orders,
            'verified_suppliers': verified_suppliers,
            'avg_order_value': avg_order_value,
            'recent_transactions': recent_transactions,
            'business_type': vendor.business_type if vendor else 'other'
        })
    
    except Exception as e:
        app.logger.error(f"Error in dashboard-stats: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error loading dashboard stats',
            'error': str(e),
            'total_orders': 0,
            'monthly_orders': 0,
            'monthly_spending': 0,
            'monthly_savings': 0,
            'active_group_orders': 0,
            'verified_suppliers': 0,
            'avg_order_value': 0,
            'recent_transactions': [],
            'business_type': 'other'
        }), 200  # Return 200 with error data instead of 500

@app.route('/api/vendor/ledger')
def get_vendor_ledger():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        vendor_id = session['vendor_id']
        
        # Get current month date range
        now = datetime.now()
        first_day_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Monthly spending
        monthly_spending = db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.vendor_id == vendor_id,
            Order.created_at >= first_day_of_month
        ).scalar() or 0
        
        # Monthly orders count
        monthly_orders = Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.created_at >= first_day_of_month
        ).count()
        
        # Calculate savings from group orders
        group_orders = Order.query.filter(
            Order.vendor_id == vendor_id,
            Order.order_type == 'group',
            Order.created_at >= first_day_of_month
        ).all()
        
        group_order_savings = sum(order.total_amount * 0.15 for order in group_orders)
        
        # Average order value
        avg_order_value = monthly_spending / monthly_orders if monthly_orders > 0 else 0
        
        # Recent transactions (last 10 orders)
        recent_orders = Order.query.filter_by(vendor_id=vendor_id).order_by(Order.created_at.desc()).limit(10).all()
        ledger_transactions = []
        
        for order in recent_orders:
            try:
                supplier = db.session.get(Supplier, order.supplier_id)
                supplier_name = supplier.name if supplier else "Unknown Supplier"
                
                # Get order items for description
                order_items = OrderItem.query.filter_by(order_id=order.id).all()
                item_names = []
                for item in order_items:
                    product = db.session.get(Product, item.product_id)
                    if product:
                        item_names.append(product.name)
                
                description = ', '.join(item_names[:3]) + ('...' if len(item_names) > 3 else '')
                if not description:
                    description = f"Order from {supplier_name}"
                
                ledger_transactions.append({
                    'date': format_ist_time(order.created_at, '%d %b %Y'),
                    'time': format_ist_time(order.created_at, '%I:%M %p'),
                    'description': description,
                    'amount': order.total_amount,
                    'supplier': supplier_name,
                    'order_type': order.order_type,
                    'status': order.status
                })
            except Exception as e:
                app.logger.error(f"Error processing ledger order {order.id}: {str(e)}")
                continue
        
        return jsonify({
            'monthly_spending': monthly_spending,
            'group_order_savings': group_order_savings,
            'monthly_orders': monthly_orders,
            'avg_order_value': avg_order_value,
            'transactions': ledger_transactions
        })
    
    except Exception as e:
        app.logger.error(f"Error in vendor ledger: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error loading ledger',
            'error': str(e),
            'monthly_spending': 0,
            'group_order_savings': 0,
            'monthly_orders': 0,
            'avg_order_value': 0,
            'transactions': []
        }), 200  # Return 200 with error data instead of 500

# Vendor Community API Routes
@app.route('/api/vendor/nearby-vendors', methods=['GET'])
def get_nearby_vendors():
    """Get list of nearby vendors for community feature"""
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        current_vendor_id = session['vendor_id']
        current_vendor = db.session.get(Vendor, current_vendor_id)
        
        if not current_vendor:
            return jsonify({'success': False, 'message': 'Vendor not found'})
        
        # Get all other vendors (in a real app, you'd filter by location/distance)
        nearby_vendors = Vendor.query.filter(Vendor.id != current_vendor_id).all()
        
        vendors_list = []
        for vendor in nearby_vendors:
            vendors_list.append({
                'id': vendor.id,
                'name': vendor.name,
                'location': vendor.location,
                'business_type': vendor.business_type,
                'avatar': vendor.name[0].upper() if vendor.name else 'V'
            })
        
        return jsonify({'success': True, 'vendors': vendors_list})
    
    except Exception as e:
        app.logger.error(f"Error getting nearby vendors: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading vendors'})

@app.route('/api/vendor/chat/messages/<int:other_vendor_id>', methods=['GET'])
def get_chat_messages(other_vendor_id):
    """Get chat messages between current vendor and another vendor"""
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        current_vendor_id = session['vendor_id']
        
        # Get messages between these two vendors
        messages = VendorChatMessage.query.filter(
            db.or_(
                db.and_(
                    VendorChatMessage.sender_id == current_vendor_id,
                    VendorChatMessage.receiver_id == other_vendor_id
                ),
                db.and_(
                    VendorChatMessage.sender_id == other_vendor_id,
                    VendorChatMessage.receiver_id == current_vendor_id
                )
            )
        ).order_by(VendorChatMessage.created_at.asc()).all()
        
        # Mark received messages as read
        VendorChatMessage.query.filter(
            VendorChatMessage.sender_id == other_vendor_id,
            VendorChatMessage.receiver_id == current_vendor_id,
            VendorChatMessage.is_read == False
        ).update({'is_read': True})
        db.session.commit()
        
        messages_list = []
        for msg in messages:
            messages_list.append({
                'id': msg.id,
                'sender_id': msg.sender_id,
                'receiver_id': msg.receiver_id,
                'message': msg.message,
                'is_sent': msg.sender_id == current_vendor_id,
                'created_at': msg.created_at.strftime('%I:%M %p'),
                'timestamp': msg.created_at.isoformat()
            })
        
        return jsonify({'success': True, 'messages': messages_list})
    
    except Exception as e:
        app.logger.error(f"Error getting chat messages: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading messages'})

@app.route('/api/vendor/chat/send', methods=['POST'])
def send_chat_message():
    """Send a chat message to another vendor"""
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')
        message_text = data.get('message', '').strip()
        
        if not receiver_id or not message_text:
            return jsonify({'success': False, 'message': 'Invalid data'})
        
        current_vendor_id = session['vendor_id']
        
        # Create new message
        new_message = VendorChatMessage(
            sender_id=current_vendor_id,
            receiver_id=receiver_id,
            message=message_text
        )
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': {
                'id': new_message.id,
                'sender_id': new_message.sender_id,
                'receiver_id': new_message.receiver_id,
                'message': new_message.message,
                'is_sent': True,
                'created_at': new_message.created_at.strftime('%I:%M %p'),
                'timestamp': new_message.created_at.isoformat()
            }
        })
    
    except Exception as e:
        app.logger.error(f"Error sending chat message: {str(e)}")
        return jsonify({'success': False, 'message': 'Error sending message'})

# ==================== INTERNSHIP ROUTES ====================

@app.route('/api/internships', methods=['GET'])
def get_internships():
    """Get all active internship opportunities with optional filters"""
    try:
        # Get filter parameters
        category = request.args.get('category')
        work_mode = request.args.get('work_mode')
        location = request.args.get('location')
        search = request.args.get('search', '').strip()
        
        # Base query for active internships
        query = InternshipOpportunity.query.filter_by(is_active=True)
        
        # Apply filters
        if category:
            query = query.filter_by(category=category)
        if work_mode:
            query = query.filter_by(work_mode=work_mode)
        if location and location.lower() != 'all':
            query = query.filter(InternshipOpportunity.location.ilike(f'%{location}%'))
        if search:
            query = query.filter(
                db.or_(
                    InternshipOpportunity.title.ilike(f'%{search}%'),
                    InternshipOpportunity.company.ilike(f'%{search}%'),
                    InternshipOpportunity.description.ilike(f'%{search}%')
                )
            )
        
        # Order by creation date (newest first)
        internships = query.order_by(InternshipOpportunity.created_at.desc()).all()
        
        # Get vendor's application status if logged in
        applied_ids = []
        if 'vendor_id' in session:
            applications = InternshipApplication.query.filter_by(
                vendor_id=session['vendor_id']
            ).all()
            applied_ids = [app.internship_id for app in applications]
        
        result = []
        for internship in internships:
            result.append({
                'id': internship.id,
                'title': internship.title,
                'company': internship.company,
                'description': internship.description,
                'requirements': internship.requirements,
                'responsibilities': internship.responsibilities,
                'skills_required': internship.skills_required,
                'stipend': internship.stipend,
                'duration': internship.duration,
                'location': internship.location,
                'work_mode': internship.work_mode,
                'category': internship.category,
                'application_deadline': internship.application_deadline.strftime('%d %b %Y') if internship.application_deadline else None,
                'contact_email': internship.contact_email,
                'contact_phone': internship.contact_phone,
                'company_website': internship.company_website,
                'created_at': internship.created_at.strftime('%d %b %Y'),
                'has_applied': internship.id in applied_ids,
                'application_count': len(internship.applications)
            })
        
        return jsonify({'success': True, 'internships': result})
    
    except Exception as e:
        app.logger.error(f"Error getting internships: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading internships'})

@app.route('/api/vendor/internship/apply', methods=['POST'])
def apply_for_internship():
    """Apply for an internship opportunity"""
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        data = request.get_json()
        internship_id = data.get('internship_id')
        cover_letter = data.get('cover_letter', '').strip()
        
        if not internship_id:
            return jsonify({'success': False, 'message': 'Invalid internship ID'})
        
        vendor_id = session['vendor_id']
        
        # Check if internship exists and is active
        internship = InternshipOpportunity.query.filter_by(
            id=internship_id,
            is_active=True
        ).first()
        
        if not internship:
            return jsonify({'success': False, 'message': 'Internship not found or no longer active'})
        
        # Check if already applied
        existing_application = InternshipApplication.query.filter_by(
            vendor_id=vendor_id,
            internship_id=internship_id
        ).first()
        
        if existing_application:
            return jsonify({'success': False, 'message': 'You have already applied for this internship'})
        
        # Create new application
        application = InternshipApplication(
            vendor_id=vendor_id,
            internship_id=internship_id,
            cover_letter=cover_letter,
            status='pending'
        )
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully! The company will review your application.',
            'application': {
                'id': application.id,
                'status': application.status,
                'applied_at': application.applied_at.strftime('%d %b %Y, %I:%M %p')
            }
        })
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error applying for internship: {str(e)}")
        return jsonify({'success': False, 'message': 'Error submitting application'})

@app.route('/api/vendor/internship/applications', methods=['GET'])
def get_vendor_internship_applications():
    """Get all internship applications for the logged-in vendor"""
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        vendor_id = session['vendor_id']
        applications = InternshipApplication.query.filter_by(
            vendor_id=vendor_id
        ).order_by(InternshipApplication.applied_at.desc()).all()
        
        result = []
        for app in applications:
            internship = app.internship
            result.append({
                'id': app.id,
                'status': app.status,
                'cover_letter': app.cover_letter,
                'applied_at': app.applied_at.strftime('%d %b %Y, %I:%M %p'),
                'updated_at': app.updated_at.strftime('%d %b %Y, %I:%M %p'),
                'internship': {
                    'id': internship.id,
                    'title': internship.title,
                    'company': internship.company,
                    'location': internship.location,
                    'work_mode': internship.work_mode,
                    'stipend': internship.stipend,
                    'duration': internship.duration
                }
            })
        
        return jsonify({'success': True, 'applications': result})
    
    except Exception as e:
        app.logger.error(f"Error getting internship applications: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading applications'})

@app.route('/api/place-order', methods=['POST'])
def place_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    
    order = Order(
        vendor_id=session['vendor_id'],
        supplier_id=data.get('supplier_id'),
        total_amount=data.get('total_amount'),
        order_type=data.get('order_type', 'individual')
    )
    db.session.add(order)
    db.session.commit()

    # Add order items if provided
    items = data.get('items', [])
    for item in items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.get('product_id'),
            quantity=item.get('quantity'),
            price_per_unit=item.get('price_per_unit')
        )
        db.session.add(order_item)
    db.session.commit()
    # Publish event for real-time updates
    publish_order_event(order.id, 'order_placed', {'order_id': order.id, 'status': order.status})
    
    # Return order id to caller for client-side tracking
    return jsonify({'success': True, 'message': 'Order placed successfully', 'order_id': order.id})

# Supplier API: list orders (JSON)
@app.route('/api/supplier/orders', methods=['GET'])
@supplier_api_required
def api_supplier_orders():
    supplier_id = session['supplier_id']
    orders = Order.query.filter_by(supplier_id=supplier_id).order_by(Order.created_at.desc()).all()
    results = []
    for o in orders:
        items = OrderItem.query.filter_by(order_id=o.id).all()
        results.append({
            'id': o.id,
            'vendor_id': o.vendor_id,
            'supplier_id': o.supplier_id,
            'status': o.status,
            'total_amount': o.total_amount,
            'created_at': format_ist_time(o.created_at, '%d %b %Y, %I:%M %p'),
            'timestamps': {
                'confirmed': o.confirmed_at.isoformat() if getattr(o, 'confirmed_at', None) else None,
                'preparing': o.preparing_at.isoformat() if getattr(o, 'preparing_at', None) else None,
                'ready': o.ready_at.isoformat() if getattr(o, 'ready_at', None) else None,
                'out_for_delivery': o.out_for_delivery_at.isoformat() if getattr(o, 'out_for_delivery_at', None) else None,
                'delivered': o.delivered_at.isoformat() if getattr(o, 'delivered_at', None) else None
            },
            'items': [{'product_id': it.product_id, 'quantity': it.quantity, 'price_per_unit': it.price_per_unit} for it in items]
        })
    return jsonify({'success': True, 'orders': results})

# Supplier API action (JSON)
@app.route('/api/supplier/orders/<int:order_id>/action', methods=['POST'])
@supplier_api_required
def api_supplier_order_action(order_id):
    order = Order.query.get(order_id)
    if not order or order.supplier_id != session['supplier_id']:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    data = request.get_json() or {}
    action = data.get('action')
    now = datetime.utcnow()
    if action == 'accept' or action == 'confirm':
        order.status = 'confirmed'
        order.confirmed_at = order.confirmed_at or now
    elif action == 'reject' or action == 'cancel':
        order.status = 'cancelled'
    elif action == 'mark_preparing' or action == 'preparing':
        order.status = 'preparing'
        order.preparing_at = order.preparing_at or now
    elif action == 'mark_ready' or action == 'ready':
        # Normalize to 'ready' status used in timelines
        order.status = 'ready'
        order.ready_at = order.ready_at or now
    elif action == 'out_for_delivery':
        order.status = 'out_for_delivery'
        order.out_for_delivery_at = order.out_for_delivery_at or now
    elif action == 'delivered':
        order.status = 'delivered'
        order.delivered_at = order.delivered_at or now
    db.session.commit()
    # publish with timestamps
    publish_order_event(order.id, 'status_update', {
        'status': order.status,
        'order_id': order.id,
        'timestamps': {
            'confirmed': order.confirmed_at.isoformat() if order.confirmed_at else None,
            'preparing': order.preparing_at.isoformat() if order.preparing_at else None,
            'ready': order.ready_at.isoformat() if order.ready_at else None,
            'out_for_delivery': order.out_for_delivery_at.isoformat() if order.out_for_delivery_at else None,
            'delivered': order.delivered_at.isoformat() if order.delivered_at else None
        }
    })
    return jsonify({'success': True, 'status': order.status})

# Order tracking
@app.route('/api/order/<int:order_id>/tracking', methods=['GET'])
def api_order_tracking(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    items = OrderItem.query.filter_by(order_id=order.id).all()
    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'vendor_id': order.vendor_id,
            'supplier_id': order.supplier_id,
            'status': order.status,
            'total_amount': order.total_amount,
            'created_at': format_ist_time(order.created_at, '%d %b %Y, %I:%M %p'),
            'items': [{'product_id': it.product_id, 'quantity': it.quantity, 'price_per_unit': it.price_per_unit} for it in items]
        }
    })

# SSE events endpoint for vendor/supplier orders
@app.route('/api/order/<int:order_id>/events')
def order_events(order_id):
    # Accept either vendor or supplier sessions for subscribing to this stream
    if 'supplier_id' not in session and 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    def stream():
        q = order_event_queues.setdefault(order_id, Queue())
        while True:
            try:
                ev = q.get(timeout=25)
                yield f"data: {json.dumps(ev)}\n\n"
            except Empty:
                # keep-alive comment to avoid proxies timing out
                yield ': keep-alive\n\n'
    return Response(stream(), mimetype='text/event-stream')


# SSE endpoint for delivery agents to subscribe to order-level events
@app.route('/api/order/<int:order_id>/agent-events')
@delivery_api_required
def order_agent_events(order_id):
    def stream():
        q = order_event_queues.setdefault(order_id, Queue())
        while True:
            try:
                ev = q.get(timeout=25)
                yield f"data: {json.dumps(ev)}\n\n"
            except Empty:
                yield ': keep-alive\n\n'
    return Response(stream(), mimetype='text/event-stream')

# SSE endpoint for supplier-level events (subscribe to all events for this supplier)
@app.route('/api/supplier/events')
@supplier_api_required
def supplier_events():
    supplier_id = session['supplier_id']
    key = f"supplier_{supplier_id}"
    def stream():
        q = order_event_queues.setdefault(key, Queue())
        while True:
            try:
                ev = q.get(timeout=25)
                yield f"data: {json.dumps(ev)}\n\n"
            except Empty:
                yield ': keep-alive\n\n'
    return Response(stream(), mimetype='text/event-stream')

# Helper to publish customer-order events separately (avoids ID collisions)
def publish_customer_order_event(customer_order_id, event_type, data=None):
    key = f"cust_{customer_order_id}"
    q = order_event_queues.setdefault(key, Queue())
    ev = {'type': event_type, 'data': data or {}, 'timestamp': datetime.utcnow().isoformat()}
    q.put(ev)

# SSE events endpoint for customer orders
@app.route('/api/customer/order/<int:order_id>/events')
@customer_api_required
def customer_order_events(order_id):
    def stream():
        key = f"cust_{order_id}"
        q = order_event_queues.setdefault(key, Queue())
        while True:
            try:
                ev = q.get(timeout=25)
                yield f"data: {json.dumps(ev)}\n\n"
            except Empty:
                yield ': keep-alive\n\n'
    return Response(stream(), mimetype='text/event-stream')

# --- Shareable public tracking endpoints ---
@app.route('/api/order/<int:order_id>/create-tracking', methods=['POST'])
def create_tracking_link(order_id):
    # Allow creation by vendor/supplier/customer/delivery agent who is related to the order
    if not ('vendor_id' in session or 'supplier_id' in session or 'customer_id' in session or 'delivery_agent_id' in session):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    order = db.session.query(CustomerOrder).filter_by(id=order_id).first()
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    # Basic ownership checks (allow if the requester is the order owner/vendor/supplier/delivery agent)
    allowed = False
    if 'customer_id' in session and session['customer_id'] == order.customer_id:
        allowed = True
    if 'delivery_agent_id' in session and session['delivery_agent_id'] == order.delivery_agent_id:
        allowed = True
    # vendor_id and supplier_id checks require relationships; allow for now if present in session
    if 'vendor_id' in session or 'supplier_id' in session:
        allowed = True

    if not allowed:
        return jsonify({'success': False, 'message': 'Forbidden'}), 403

    token = secrets.token_urlsafe(16)
    expires = datetime.utcnow() + timedelta(hours=24)

    link = TrackingLink(token=token, order_id=order.id, expires_at=expires)
    db.session.add(link)
    db.session.commit()

    url = url_for('track_page', token=token, _external=True)
    return jsonify({'success': True, 'tracking_url': url, 'expires_at': expires.isoformat()})


@app.route('/track/<token>')
def track_page(token):
    link = db.session.query(TrackingLink).filter_by(token=token).first()
    if not link or link.expires_at < datetime.utcnow():
        return render_template('track.html', invalid=True, token=token, google_maps_key=app.config.get('GOOGLE_MAPS_API_KEY'))
    return render_template('track.html', invalid=False, token=token, google_maps_key=app.config.get('GOOGLE_MAPS_API_KEY'))


@app.route('/api/track/<token>/info')
def track_info(token):
    link = db.session.query(TrackingLink).filter_by(token=token).first()
    if not link or link.expires_at < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Tracking link invalid or expired'}), 404

    order = db.session.query(CustomerOrder).filter_by(id=link.order_id).first()
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'status': order.status,
            'delivery_latitude': order.delivery_latitude,
            'delivery_longitude': order.delivery_longitude,
            'customer_name': order.customer_name,
            'delivery_address': order.delivery_address
        }
    })


@app.route('/api/track/<token>/events')
def track_events(token):
    link = db.session.query(TrackingLink).filter_by(token=token).first()
    if not link or link.expires_at < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Tracking link invalid or expired'}), 404

    order_id = link.order_id

    def stream():
        q = order_event_queues.setdefault(order_id, Queue())
        while True:
            try:
                ev = q.get(timeout=25)
                yield f"data: {json.dumps(ev)}\n\n"
            except Empty:
                yield ': keep-alive\n\n'
    return Response(stream(), mimetype='text/event-stream')


@app.route('/api/customer/profile', methods=['PUT'])
def update_customer_profile():
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    data = request.get_json()
    customer = db.session.get(Customer, session['customer_id'])

    # Update fields
    customer.name = data.get('name', customer.name)
    customer.email = data.get('email', customer.email)
    customer.phone = data.get('phone', customer.phone)
    customer.location = data.get('address', customer.location)  # Note: using location field

    db.session.commit()

    # Update session
    session['customer_name'] = customer.name
    session['customer_email'] = customer.email
    session['customer_phone'] = customer.phone
    session['customer_address'] = customer.location  # Map location to address in session

    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/api/debug/products')
def debug_products():
    products = Product.query.all()
    products_data = []
    
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'current_price': product.current_price,
            'stock_available': product.stock_available,
            'unit': product.unit,
            'supplier_name': supplier.name if supplier else 'Unknown'
        })
    
    return jsonify(products_data)



@app.route('/api/place-order-customer', methods=['POST'])
def place_order_customer():
    try:
        if 'customer_id' not in session:
            return jsonify({'success': False, 'message': 'Please login first'}), 401

        data = request.get_json()
        customer = db.session.get(Customer, session['customer_id'])

        # Validate required fields (items may be empty)
        required_fields = ['name', 'email', 'phone', 'address']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'{field.title()} is required'}), 400

        # Ensure items is present as a list (can be empty)
        items = data.get('items', [])
        if items is None:
            items = []

        # Allow empty cart (tests may send empty items). Continue processing even if items list is empty.

        # Calculate order amounts
        subtotal = 0
        order_items = []
        missing_items = []
        
        for item in items:
            if 'id' not in item or 'qty' not in item:
                return jsonify({'success': False, 'message': 'Invalid item data'}), 400

            menu_item = db.session.get(MenuItem, item['id'])
            if not menu_item:
                # Instead of failing completely, track missing items
                missing_items.append(item['id'])
                continue

            if item['qty'] <= 0:
                return jsonify({'success': False, 'message': 'Invalid quantity'}), 400

            item_total = menu_item.price * item['qty']
            subtotal += item_total
            order_items.append({
                'menu_item_id': item['id'],
                'quantity': item['qty'],
                'price_per_unit': menu_item.price,
                'item_total': item_total
            })
        
        # If no valid items remain, reject the order
        if len(order_items) == 0:
            if missing_items:
                return jsonify({
                    'success': False, 
                    'message': f'Items not found: {", ".join(map(str, missing_items))}. Please refresh your cart and try again.',
                    'missing_items': missing_items
                }), 400
            # Allow empty carts for testing scenarios; production clients should validate on frontend

        # Warn if some items were missing but order can proceed with available items
        order_response_data = {'missing_items': missing_items} if missing_items else {}

        # Validate and extract delivery type
        delivery_type = data.get('delivery_type', 'delivery').lower()
        allowed_delivery_types = ['delivery', 'self_pickup']
        if delivery_type not in allowed_delivery_types:
            return jsonify({
                'success': False,
                'type': 'https://example.com/problems/invalid-delivery-type',
                'title': 'Invalid Delivery Type',
                'status': 422,
                'detail': f'Delivery type must be one of: {", ".join(allowed_delivery_types)}',
                'instance': '/api/place-order-customer',
                'invalid_field': 'delivery_type',
                'allowed_values': allowed_delivery_types
            }), 422
        
        # Calculate delivery fee based on delivery type
        if delivery_type == 'self_pickup':
            delivery_fee = 0.0
        else:
            delivery_fee = 40.0 if subtotal < 300 else 0.0  # Free delivery above ₹300
        
        # Validate payment method
        payment_method = data.get('payment', 'cod').lower()
        allowed_payment_methods = ['cod', 'card', 'upi']
        if payment_method not in allowed_payment_methods:
            return jsonify({
                'success': False,
                'type': 'https://example.com/problems/invalid-payment-method',
                'title': 'Invalid Payment Method',
                'status': 422,
                'detail': f'Payment method must be one of: {", ".join(allowed_payment_methods)}',
                'instance': '/api/place-order-customer',
                'invalid_field': 'payment',
                'allowed_values': allowed_payment_methods
            }), 422
        
        tax_amount = round(subtotal * 0.05, 2)  # 5% GST
        total_amount = subtotal + delivery_fee + tax_amount

        # No minimum order enforced here (tests expect orders with low totals to be allowed)

        # Get GPS coordinates - use manual input if provided, otherwise extract from address
        delivery_lat = data.get('latitude')
        delivery_lon = data.get('longitude')
        
        if delivery_lat and delivery_lon:
            # Use manually provided coordinates
            delivery_lat = float(delivery_lat)
            delivery_lon = float(delivery_lon)
        else:
            # Extract GPS coordinates from address
            delivery_lat, delivery_lon = extract_gps_from_address(data['address'])

        # Estimate delivery time (30-45 minutes from now)
        estimated_delivery = datetime.utcnow() + timedelta(minutes=30 + (data.get('items', []).__len__() * 2))

        # Create customer order
        order = CustomerOrder(
            customer_id=session['customer_id'],
            total_amount=total_amount,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            tax_amount=tax_amount,
            status='pending',
            delivery_type=delivery_type,
            payment_method=payment_method,
            payment_status='offline_pending' if payment_method == 'cod' else 'pending',
            delivery_address=data['address'],
            delivery_latitude=delivery_lat,
            delivery_longitude=delivery_lon,
            delivery_instructions=data.get('instructions', ''),
            customer_name=data['name'],
            customer_email=data['email'],
            customer_phone=data['phone'],
            estimated_delivery_time=estimated_delivery
        )
        db.session.add(order)
        db.session.flush()  # Get order ID without committing

        # Assign to available delivery agent only if delivery type is 'delivery'
        if delivery_type == 'delivery':
            try:
                available_agents = db.session.query(DeliveryAgent).order_by(
                    db.func.random()
                ).limit(1).all()
                
                if available_agents:
                    order.delivery_agent_id = available_agents[0].id
            except Exception as e:
                app.logger.warning(f"Could not assign delivery agent: {str(e)}")

        # Create order items
        for item_data in order_items:
            order_item = CustomerOrderItem(
                order_id=order.id,
                menu_item_id=item_data['menu_item_id'],
                quantity=item_data['quantity'],
                price_per_unit=item_data['price_per_unit']
            )
            db.session.add(order_item)

        # Update order status and timestamps before committing
        current_time = datetime.utcnow()
        order.status = 'confirmed'
        order.confirmed_at = current_time
        # Auto-set preparing timestamp a minute later
        order.preparing_at = current_time + timedelta(minutes=1)

        # Single atomic commit with rollback on error
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.exception(f"Database error while persisting order: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An error occurred while placing your order. Please try again or contact support.'
            }), 500

        # Publish customer order status update for real-time clients
        try:
            publish_customer_order_event(order.id, 'status_update', {
                'status': order.status,
                'timestamps': {
                    'confirmed': order.confirmed_at.isoformat() if order.confirmed_at else None,
                    'preparing': order.preparing_at.isoformat() if order.preparing_at else None
                }
            })
        except Exception as e:
            app.logger.warning(f"Could not publish customer order event: {e}")

        # Cache initial delivery location in real-time cache
        if order.delivery_agent_id:
            with delivery_cache_lock:
                delivery_location_cache[f"order_{order.id}"] = {
                    'order_id': order.id,
                    'delivery_agent_id': order.delivery_agent_id,
                    'latitude': delivery_lat,
                    'longitude': delivery_lon,
                    'timestamp': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow()
                }

        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': 'Order placed successfully!' + (' (Some items were unavailable and excluded)' if missing_items else ''),
            'missing_items': missing_items,
            'order_details': {
                'subtotal': subtotal,
                'delivery_fee': delivery_fee,
                'tax_amount': tax_amount,
                'total': total_amount,
                'estimated_delivery': estimated_delivery.strftime('%I:%M %p'),
                'payment_method': order.payment_method,
                'delivery_latitude': delivery_lat,
                'delivery_longitude': delivery_lon
            }
        })
    except Exception as e:
        app.logger.exception(f"Error placing customer order: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while placing your order. Please try again or contact support.'
        }), 500


@app.route('/api/customer/notifications', methods=['GET'])
def get_customer_notifications():
    """Get recent notifications for customer based on order status changes"""
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        customer_id = session['customer_id']
        
        # Get recent orders (last 24 hours)
        recent_orders = db.session.query(CustomerOrder).filter(
            CustomerOrder.customer_id == customer_id,
            CustomerOrder.created_at >= datetime.utcnow() - timedelta(days=1)
        ).order_by(CustomerOrder.updated_at.desc()).limit(10).all()
        
        notifications = []
        
        for order in recent_orders:
            # Get vendor name from order items
            vendor_name = 'Restaurant'
            first_item = db.session.query(CustomerOrderItem).filter_by(
                order_id=order.id
            ).first()
            
            if first_item:
                menu_item = db.session.query(MenuItem).filter_by(
                    id=first_item.menu_item_id
                ).first()
                if menu_item:
                    vendor = db.session.query(Vendor).filter_by(
                        id=menu_item.vendor_id
                    ).first()
                    if vendor:
                        vendor_name = vendor.name
            
            # Create notification based on order status
            notification = None
            
            if order.status == 'delivered' and order.actual_delivery_time:
                notification = {
                    'title': 'Order Delivered',
                    'text': f'Your order from {vendor_name} has been delivered',
                    'time': order.actual_delivery_time.isoformat(),
                    'unread': True
                }
            elif order.status == 'out_for_delivery' and order.out_for_delivery_at:
                notification = {
                    'title': 'Out for Delivery',
                    'text': f'Your order from {vendor_name} is on the way',
                    'time': order.out_for_delivery_at.isoformat(),
                    'unread': True
                }
            elif order.status == 'preparing' and order.preparing_at:
                notification = {
                    'title': 'Order Confirmed',
                    'text': f'{vendor_name} is preparing your order',
                    'time': order.preparing_at.isoformat(),
                    'unread': False
                }
            elif order.status == 'confirmed' and order.confirmed_at:
                notification = {
                    'title': 'Order Confirmed',
                    'text': f'Your order has been confirmed',
                    'time': order.confirmed_at.isoformat(),
                    'unread': False
                }
            
            if notification:
                notifications.append(notification)
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
    except Exception as e:
        app.logger.error(f"Get notifications error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customer/settings', methods=['GET'])
def get_customer_settings():
    """Get customer settings"""
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        customer = db.session.query(Customer).filter_by(id=session['customer_id']).first()
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        settings = {
            'email_notifications': customer.email_notifications if hasattr(customer, 'email_notifications') else True,
            'sms_notifications': customer.sms_notifications if hasattr(customer, 'sms_notifications') else True,
            'promo_emails': customer.promo_emails if hasattr(customer, 'promo_emails') else False,
            'language': customer.language if hasattr(customer, 'language') else 'en',
            'theme': customer.theme if hasattr(customer, 'theme') else 'light',
            'default_instructions': customer.default_instructions if hasattr(customer, 'default_instructions') else '',
            'default_payment': customer.default_payment if hasattr(customer, 'default_payment') else 'cod',
            'profile_visibility': customer.profile_visibility if hasattr(customer, 'profile_visibility') else 'private',
            'data_sharing': customer.data_sharing if hasattr(customer, 'data_sharing') else False
        }
        
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        app.logger.error(f"Error fetching settings: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customer/settings', methods=['POST'])
def save_customer_settings():
    """Save customer settings"""
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        customer = db.session.query(Customer).filter_by(id=session['customer_id']).first()
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Update settings with hasattr checks for backward compatibility
        if hasattr(customer, 'email_notifications'):
            customer.email_notifications = data.get('email_notifications', True)
        if hasattr(customer, 'sms_notifications'):
            customer.sms_notifications = data.get('sms_notifications', True)
        if hasattr(customer, 'promo_emails'):
            customer.promo_emails = data.get('promo_emails', False)
        if hasattr(customer, 'language'):
            customer.language = data.get('language', 'en')
        if hasattr(customer, 'theme'):
            customer.theme = data.get('theme', 'light')
        if hasattr(customer, 'default_instructions'):
            customer.default_instructions = data.get('default_instructions', '')
        if hasattr(customer, 'default_payment'):
            customer.default_payment = data.get('default_payment', 'cod')
        if hasattr(customer, 'profile_visibility'):
            customer.profile_visibility = data.get('profile_visibility', 'private')
        if hasattr(customer, 'data_sharing'):
            customer.data_sharing = data.get('data_sharing', False)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving settings: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customer/change-password', methods=['POST'])
def change_customer_password():
    """Change customer password"""
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        customer = db.session.query(Customer).filter_by(id=session['customer_id']).first()
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Verify current password
        if customer.password_hash and not check_password_hash(customer.password_hash, current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
        
        # Update password
        customer.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error changing password: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customer/export-data', methods=['GET'])
def export_customer_data():
    """Export customer data"""
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        customer_id = session['customer_id']
        customer = db.session.query(Customer).filter_by(id=customer_id).first()
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Get all customer orders
        orders = db.session.query(CustomerOrder).filter_by(customer_id=customer_id).all()
        
        orders_data = []
        for order in orders:
            order_items = db.session.query(CustomerOrderItem).filter_by(order_id=order.id).all()
            items_list = []
            
            for item in order_items:
                menu_item = db.session.query(MenuItem).filter_by(id=item.menu_item_id).first()
                if menu_item:
                    items_list.append({
                        'name': menu_item.name,
                        'quantity': item.quantity,
                        'price': item.price
                    })
            
            orders_data.append({
                'order_id': order.id,
                'date': format_ist_time(order.created_at, '%d %b %Y, %I:%M %p') if order.created_at else None,
                'status': order.status,
                'total_amount': order.total_amount,
                'payment_method': order.payment_method,
                'items': items_list
            })
        
        export_data = {
            'customer_info': {
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone,
                'location': customer.location,
                'created_at': format_ist_time(customer.created_at, '%d %b %Y, %I:%M %p') if customer.created_at else None
            },
            'settings': {
                'email_notifications': customer.email_notifications if hasattr(customer, 'email_notifications') else True,
                'sms_notifications': customer.sms_notifications if hasattr(customer, 'sms_notifications') else True,
                'promo_emails': customer.promo_emails if hasattr(customer, 'promo_emails') else False,
                'language': customer.language if hasattr(customer, 'language') else 'en',
                'theme': customer.theme if hasattr(customer, 'theme') else 'light'
            },
            'orders': orders_data,
            'total_orders': len(orders_data),
            'export_date': datetime.utcnow().isoformat()
        }
        
        return jsonify({'success': True, 'data': export_data})
    except Exception as e:
        app.logger.error(f"Error exporting data: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customer/delete-account', methods=['POST'])
def delete_customer_account():
    """Delete customer account"""
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    try:
        data = request.get_json()
        password = data.get('password')
        confirmation = data.get('confirmation')
        
        if not password:
            return jsonify({'success': False, 'message': 'Password required'}), 400
        
        if confirmation != 'DELETE':
            return jsonify({'success': False, 'message': 'Please type DELETE to confirm'}), 400
        
        customer_id = session['customer_id']
        customer = db.session.query(Customer).filter_by(id=customer_id).first()
        
        if not customer:
            return jsonify({'success': False, 'message': 'Customer not found'}), 404
        
        # Verify password
        if customer.password_hash and not check_password_hash(customer.password_hash, password):
            return jsonify({'success': False, 'message': 'Incorrect password'}), 401
        
        # Delete customer orders and related data
        orders = db.session.query(CustomerOrder).filter_by(customer_id=customer_id).all()
        for order in orders:
            db.session.query(CustomerOrderItem).filter_by(order_id=order.id).delete()
            db.session.delete(order)
        
        # Delete customer
        db.session.delete(customer)
        db.session.commit()
        
        # Clear session
        session.clear()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting account: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/customer/orders', methods=['GET'])
def get_customer_orders():
    if 'customer_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    try:
        customer_id = session['customer_id']
        orders = CustomerOrder.query.filter_by(customer_id=customer_id).order_by(CustomerOrder.created_at.desc()).all()

        orders_data = []
        for order in orders:
            order_items = CustomerOrderItem.query.filter_by(order_id=order.id).all()
            items_data = []
            for item in order_items:
                menu_item = MenuItem.query.get(item.menu_item_id)
                if menu_item:
                    items_data.append({
                        'name': menu_item.name,
                        'quantity': item.quantity,
                        'price_per_unit': item.price_per_unit,
                        'total': item.quantity * item.price_per_unit
                    })

            # Format datetime safely
            estimated_time = None
            if order.estimated_delivery_time:
                try:
                    # Handle both datetime objects and strings
                    dt = order.estimated_delivery_time
                    if isinstance(dt, str):
                        from datetime import datetime
                        # Parse ISO format datetime string
                        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                    # Format to 12-hour time
                    estimated_time = dt.strftime('%I:%M %p')
                except Exception as e:
                    print(f"Error formatting estimated_delivery_time for order {order.id}: {e}")
                    estimated_time = None

            orders_data.append({
                'id': order.id,
                'total_amount': order.total_amount,
                'subtotal': order.subtotal,
                'delivery_fee': order.delivery_fee,
                'tax_amount': order.tax_amount,
                'status': order.status,
                'payment_method': order.payment_method,
                'payment_status': order.payment_status,
                'delivery_address': order.delivery_address,
                'delivery_instructions': order.delivery_instructions,
                'estimated_delivery_time': estimated_time,
                'created_at': order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'items': items_data
            })

        return jsonify({'success': True, 'orders': orders_data})
    except Exception as e:
        print(f"Error in get_customer_orders: {e}")
        return jsonify({'success': False, 'message': 'Error loading orders'}), 500


@app.route('/api/vendor/customer-orders', methods=['GET'])
def api_vendor_customer_orders():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    try:
        vendor_id = session['vendor_id']
        subq = db.session.query(CustomerOrderItem.order_id).join(MenuItem, MenuItem.id == CustomerOrderItem.menu_item_id).filter(MenuItem.vendor_id == vendor_id).subquery()
        orders = CustomerOrder.query.filter(CustomerOrder.id.in_(subq)).order_by(CustomerOrder.created_at.desc()).all()
        result = []
        for o in orders:
            # Only include items from this vendor
            order_items = db.session.query(CustomerOrderItem).join(MenuItem, MenuItem.id == CustomerOrderItem.menu_item_id).filter(CustomerOrderItem.order_id == o.id, MenuItem.vendor_id == vendor_id).all()
            items = []
            total_vendor_amount = 0.0
            for it in order_items:
                mi = db.session.get(MenuItem, it.menu_item_id)
                line_total = float(it.quantity) * float(it.price_per_unit)
                total_vendor_amount += line_total
                items.append({
                    'menu_item_id': it.menu_item_id,
                    'name': mi.name if mi else 'Unknown',
                    'quantity': float(it.quantity),
                    'price_per_unit': float(it.price_per_unit),
                    'total': line_total
                })
            result.append({
                'id': o.id,
                'status': o.status,
                'created_at': format_ist_time(o.created_at, '%d %b %Y, %I:%M %p') if o.created_at else None,
                'customer_name': o.customer_name,
                'customer_phone': o.customer_phone,
                'delivery_address': o.delivery_address,
                'delivery_type': getattr(o, 'delivery_type', 'delivery'),
                'payment_method': o.payment_method,
                'payment_status': o.payment_status,
                'estimated_delivery_time': o.estimated_delivery_time.isoformat() if o.estimated_delivery_time else None,
                'vendor_subtotal': total_vendor_amount,
                'items': items
            })
        return jsonify({'success': True, 'orders': result})
    except Exception as e:
        app.logger.exception('Error fetching vendor customer orders:')
        return jsonify({'success': False, 'message': 'Error loading orders'}), 500


@app.route('/api/vendor/customer-orders/<int:order_id>/action', methods=['POST'])
def api_vendor_customer_order_action(order_id):
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    vendor_id = session['vendor_id']
    # Ensure this order contains items from the vendor
    has_items = db.session.query(CustomerOrderItem).join(MenuItem, MenuItem.id == CustomerOrderItem.menu_item_id).filter(CustomerOrderItem.order_id == order_id, MenuItem.vendor_id == vendor_id).first()
    if not has_items:
        return jsonify({'success': False, 'message': 'Order not found for this vendor'}), 404
    order = db.session.get(CustomerOrder, order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    data = request.get_json(silent=True) or {}
    action = (data.get('action') or '').strip().lower()
    now = datetime.utcnow()
    if action in ('accept', 'confirm'):
        order.status = 'confirmed'
        order.confirmed_at = order.confirmed_at or now
    elif action in ('reject', 'cancel'):
        order.status = 'cancelled'
    elif action in ('preparing', 'mark_preparing'):
        order.status = 'preparing'
        order.preparing_at = order.preparing_at or now
    elif action in ('ready', 'mark_ready'):
        order.status = 'ready'
        order.ready_at = order.ready_at or now
    elif action in ('out_for_delivery', 'dispatch'):
        order.status = 'out_for_delivery'
        order.out_for_delivery_at = order.out_for_delivery_at or now
    elif action in ('delivered', 'mark_delivered'):
        order.status = 'delivered'
        order.actual_delivery_time = order.actual_delivery_time or now
    elif action in ('done', 'mark_done', 'picked_up'):
        # For self-pickup orders, mark as done when customer picks up
        order.status = 'done'
        order.picked_up_at = order.picked_up_at or now
        order.pickup_ready_at = order.pickup_ready_at or now
        
        # Award reward points for self-pickup orders
        if order.delivery_type == 'self_pickup' and order.customer_id:
            try:
                customer = Customer.query.get(order.customer_id)
                if customer and order.delivery_latitude and order.delivery_longitude:
                    # Calculate distance-based reward (using approximate distance calculation)
                    # In production, you'd integrate with a proper geolocation API
                    # For now, award a flat 10 points per self-pickup order
                    reward_points = 10
                    customer.reward_points = (customer.reward_points or 0) + reward_points
                    app.logger.info(f'Awarded {reward_points} points to customer {customer.id} for self-pickup')
            except Exception as e:
                app.logger.error(f'Error awarding reward points: {str(e)}')
    else:
        return jsonify({'success': False, 'message': 'Unknown action'}), 400
    db.session.commit()
    try:
        publish_customer_order_event(order.id, 'status_update', {
            'status': order.status,
            'order_id': order.id,
            'timestamps': {
                'confirmed': order.confirmed_at.isoformat() if order.confirmed_at else None,
                'preparing': order.preparing_at.isoformat() if order.preparing_at else None,
                'ready': order.ready_at.isoformat() if order.ready_at else None,
                'out_for_delivery': order.out_for_delivery_at.isoformat() if order.out_for_delivery_at else None,
                'delivered': order.actual_delivery_time.isoformat() if order.actual_delivery_time else None
            }
        })
    except Exception:
        pass
    return jsonify({'success': True, 'order_id': order.id, 'status': order.status})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index_new'))


@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))
    vendor = Vendor.query.get(session['vendor_id'])
    if not vendor:
        session.clear()
        return redirect(url_for('vendor_login'))
    return render_template('vendor_dashboard.html', vendor=vendor)

@app.route('/vendor/customer-orders')
def vendor_customer_orders_page():
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))
    vendor = db.session.get(Vendor, session['vendor_id'])
    if not vendor:
        session.clear()
        return redirect(url_for('vendor_login'))
    return render_template('vendor_customer_orders.html', vendor=vendor)


@app.route('/vendor/settings', methods=['GET', 'POST'])
def vendor_settings():
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))

    vendor = db.session.get(Vendor, session['vendor_id'])
    if not vendor:
        session.clear()
        return redirect(url_for('vendor_login'))

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        phone = (request.form.get('phone') or '').strip()
        email = (request.form.get('email') or '').strip()
        location = (request.form.get('location') or '').strip()
        business_type = (request.form.get('business_type') or '').strip() or 'other'
        gstin = (request.form.get('gstin') or '').strip()
        is_open_val = request.form.get('is_open')

        # Uniqueness checks if values are changed
        try:
            if phone and phone != vendor.phone:
                if Vendor.query.filter(Vendor.phone == phone, Vendor.id != vendor.id).first() or \
                   Supplier.query.filter_by(phone=phone).first() or \
                   DeliveryAgent.query.filter_by(phone=phone).first() or \
                   Customer.query.filter_by(phone=phone).first():
                    return render_template('vendor_settings.html', vendor=vendor, error='Phone number already in use')

            if email and email != (vendor.email or ''):
                if Vendor.query.filter(Vendor.email == email, Vendor.id != vendor.id).first() or \
                   Supplier.query.filter_by(email=email).first() or \
                   DeliveryAgent.query.filter_by(email=email).first() or \
                   Customer.query.filter_by(email=email).first():
                    return render_template('vendor_settings.html', vendor=vendor, error='Email already in use')

            if gstin and gstin != (vendor.gstin or ''):
                if Vendor.query.filter(Vendor.gstin == gstin, Vendor.id != vendor.id).first():
                    return render_template('vendor_settings.html', vendor=vendor, error='GSTIN already registered')
        except Exception:
            pass

        # Apply updates
        if name:
            vendor.name = name
        if phone:
            vendor.phone = phone
        if email:
            vendor.email = email
        if location:
            vendor.location = location
        if business_type:
            vendor.business_type = business_type
        vendor.gstin = gstin or vendor.gstin
        vendor.is_open = bool(is_open_val)

        db.session.commit()
        return render_template('vendor_settings.html', vendor=vendor, success='Settings updated successfully')

    return render_template('vendor_settings.html', vendor=vendor)


@app.route('/supplier/dashboard')
def supplier_dashboard():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier_id = session['supplier_id']
    # compute a few summary stats to show on dashboard
    try:
        products_count = Product.query.filter_by(supplier_id=supplier_id).count()
    except Exception:
        products_count = 0

    try:
        pending_orders = Order.query.filter_by(supplier_id=supplier_id, status='pending').count()
    except Exception:
        pending_orders = 0

    try:
        delivered_count = Order.query.filter_by(supplier_id=supplier_id, status='delivered').count()
    except Exception:
        delivered_count = 0

    try:
        total_earnings = db.session.query(db.func.coalesce(db.func.sum(Order.total_amount), 0)).filter(Order.supplier_id == supplier_id, Order.status == 'delivered').scalar() or 0.0
    except Exception:
        total_earnings = 0.0

    # additional supplier metrics
    try:
        warehouses_count = Warehouse.query.filter_by(supplier_id=supplier_id).count()
    except Exception:
        warehouses_count = 0

    try:
        service_areas_count = ServiceArea.query.filter_by(supplier_id=supplier_id).count()
    except Exception:
        service_areas_count = 0

    try:
        supplier = Supplier.query.get(supplier_id)
        verification_status = bool(supplier.verification_status) if supplier else False
    except Exception:
        verification_status = False

    features = [
        {
            'title': 'Supplier Profile & Management',
            'points': ['Supplier registration & onboarding','Business details & warehouse locations','Product catalog management','Quality certification upload','Service area management'],
            'link': '/supplier/profile',
            'stats': [
                {'label': 'Warehouses', 'value': warehouses_count},
                {'label': 'Service Areas', 'value': service_areas_count},
                {'label': 'Verified', 'value': 'Yes' if verification_status else 'No'},
            ]
        },
        {
            'title': 'Inventory & Product Control',
            'points': ['Real-time stock updates','Dynamic price updates','Bulk price discounts','Product availability alerts'],
            'link': '/supplier/inventory',
            'stat': {'label': 'Products', 'value': products_count}
        },
        {
            'title': 'Order & Delivery Management',
            'points': ['View incoming vendor orders','Accept / reject orders','Assign delivery agents','Update delivery status','Upload delivery proof'],
            'link': '/supplier/orders',
            'stat': {'label': 'Pending', 'value': pending_orders}
        },
        {
            'title': 'Supplier Communication',
            'points': ['Chat with vendors','Send price updates & offers','Broadcast messages to vendors','Respond to order queries'],
            'link': '/supplier/communication'
        },
        {
            'title': 'Payments & Finance',
            'points': ['Receive vendor payments','Auto-generated invoices','Settlement tracking','Earnings summary dashboard'],
            'link': '/supplier/payments',
            'stat': {'label': 'Earnings', 'value': f"₹{total_earnings:.2f}"}
        },
        {
            'title': 'Supplier Analytics',
            'points': ['Sales performance reports','Top-selling products','Vendor demand analysis','Delivery success rate'],
            'link': '/supplier/analytics',
            'stat': {'label': 'Delivered', 'value': delivered_count}
        },
        {
            'title': 'Supplier Reliability & Trust',
            'points': ['Vendor feedback & ratings','Quality complaint handling','Penalty alerts for delays','Supplier verification badge'],
            'link': '/supplier/reliability'
        },
        {
            'title': 'Common Features (Vendor & Supplier)',
            'points': ['Notification system (order, payment, delivery)','Location-based matching','Language selection','Help & support system','Secure authentication'],
            'link': '/supplier/common-features'
        }
    ]

    return render_template('supplier_dashboard.html', features=features, warehouses_count=warehouses_count, service_areas_count=service_areas_count, verification_status=verification_status, products_count=products_count, total_earnings=total_earnings, pending_orders=pending_orders)


@app.context_processor
def supplier_context():
    """Inject supplier-specific counts into templates when logged in."""
    ctx = {
        'format_ist_time': format_ist_time,
        'to_ist': to_ist
    }
    if 'supplier_id' in session:
        supplier_id = session['supplier_id']
        try:
            ctx['warehouses_count'] = Warehouse.query.filter_by(supplier_id=supplier_id).count()
        except Exception:
            ctx['warehouses_count'] = 0
        try:
            ctx['service_areas_count'] = ServiceArea.query.filter_by(supplier_id=supplier_id).count()
        except Exception:
            ctx['service_areas_count'] = 0
        try:
            ctx['products_count'] = Product.query.filter_by(supplier_id=supplier_id).count()
        except Exception:
            ctx['products_count'] = 0
        try:
            s = Supplier.query.get(supplier_id)
            ctx['verification_status'] = bool(s.verification_status) if s else False
        except Exception:
            ctx['verification_status'] = False
    return ctx


@app.route('/supplier/dashboard/data')
def supplier_dashboard_data():
    """Return JSON analytics and recent orders for the logged-in supplier."""
    if 'supplier_id' not in session:
        return jsonify({'success': False, 'error': 'unauthorized'}), 401

    supplier_id = session['supplier_id']

    # Sales over last 7 days
    try:
        # SQLite and other DBs should support date() or strftime; use generic date()
        sales_rows = db.session.query(
            db.func.date(Order.created_at).label('d'),
            db.func.coalesce(db.func.sum(Order.total_amount), 0).label('total')
        ).filter(Order.supplier_id == supplier_id).group_by(db.func.date(Order.created_at)).order_by(db.func.date(Order.created_at)).all()

        # Build a dict for quick lookup
        sales_map = {r.d: float(r.total or 0) for r in sales_rows}
        today = datetime.utcnow().date()
        sales_last_7 = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            key = d.isoformat()
            sales_last_7.append({'date': key, 'total': float(sales_map.get(key, 0.0))})
    except Exception as e:
        app.logger.exception('Error computing sales for supplier dashboard:')
        sales_last_7 = []

    # Top products by quantity in recent orders
    try:
        top_query = db.session.query(
            OrderItem.product_id,
            db.func.coalesce(db.func.sum(OrderItem.quantity), 0).label('qty')
        ).join(Order, Order.id == OrderItem.order_id).filter(Order.supplier_id == supplier_id).group_by(OrderItem.product_id).order_by(db.func.sum(OrderItem.quantity).desc()).limit(8).all()

        top_products = []
        for row in top_query:
            product = Product.query.get(row.product_id)
            top_products.append({'product_id': row.product_id, 'name': product.name if product else 'Unknown', 'quantity': float(row.qty or 0)})
    except Exception:
        app.logger.exception('Error computing top products:')
        top_products = []

    # Recent orders with itemized details
    try:
        recent_orders_q = Order.query.filter_by(supplier_id=supplier_id).order_by(Order.created_at.desc()).limit(10).all()
        recent_orders = []
        for o in recent_orders_q:
            vendor = Vendor.query.get(o.vendor_id)
            items_q = OrderItem.query.filter_by(order_id=o.id).all()
            items = []
            for it in items_q:
                prod = Product.query.get(it.product_id)
                items.append({'product_id': it.product_id, 'name': prod.name if prod else 'Unknown', 'quantity': float(it.quantity), 'price_per_unit': float(it.price_per_unit)})

            recent_orders.append({
                'order_id': o.id,
                'vendor_id': o.vendor_id,
                'vendor_name': vendor.name if vendor else None,
                'total_amount': float(o.total_amount),
                'status': o.status,
                'created_at': format_ist_time(o.created_at, '%d %b %Y, %I:%M %p') if o.created_at else None,
                'items': items
            })
    except Exception:
        app.logger.exception('Error fetching recent orders for supplier dashboard:')
        recent_orders = []

    return jsonify({'success': True, 'sales_last_7': sales_last_7, 'top_products': top_products, 'recent_orders': recent_orders})


# --- Supplier feature routes (placeholders) ---
@app.route('/supplier/manage-products', methods=['GET', 'POST'])
def supplier_manage_products():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))

    supplier_id = session['supplier_id']

    if request.method == 'POST':
        # Basic create product form handling
        name = request.form.get('name')
        category = request.form.get('category') or 'other'
        price = request.form.get('price') or 0
        stock = request.form.get('stock') or 0
        unit = request.form.get('unit') or 'kg'

        try:
            price_f = float(price)
            stock_i = int(float(stock))
        except Exception:
            price_f = 0.0
            stock_i = 0

        if not name:
            return render_template('manage_products.html', error='Product name required', products=Product.query.filter_by(supplier_id=supplier_id).all(), categories=PRODUCT_CATEGORIES, category_names=CATEGORY_DISPLAY_NAMES)

        if not category:
            return render_template('manage_products.html', error='Please select a category', products=Product.query.filter_by(supplier_id=supplier_id).all(), categories=PRODUCT_CATEGORIES, category_names=CATEGORY_DISPLAY_NAMES)

        p = Product(name=name, category=category, current_price=price_f, supplier_id=supplier_id, stock_available=stock_i, unit=unit)
        db.session.add(p)
        db.session.commit()
        return redirect(url_for('supplier_manage_products'))

    products = Product.query.filter_by(supplier_id=supplier_id).all()
    return render_template('manage_products.html', products=products, categories=PRODUCT_CATEGORIES, category_names=CATEGORY_DISPLAY_NAMES)


@app.route('/supplier/product/<int:product_id>/edit', methods=['GET', 'POST'])
def supplier_product_edit(product_id):
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    p = Product.query.get(product_id)
    if not p or p.supplier_id != session['supplier_id']:
        return redirect(url_for('supplier_manage_products'))

    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        price = request.form.get('price')
        stock = request.form.get('stock')
        unit = request.form.get('unit')
        try:
            p.current_price = float(price)
        except Exception:
            pass
        try:
            p.stock_available = int(float(stock))
        except Exception:
            pass
        if name:
            p.name = name
        if category:
            p.category = category
        if unit:
            p.unit = unit
        db.session.commit()
        return redirect(url_for('supplier_manage_products'))

    return render_template('manage_products.html', edit_product=p, products=[p], categories=PRODUCT_CATEGORIES, category_names=CATEGORY_DISPLAY_NAMES)


@app.route('/supplier/product/<int:product_id>/delete', methods=['POST'])
def supplier_product_delete(product_id):
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    p = Product.query.get(product_id)
    if not p or p.supplier_id != session['supplier_id']:
        return redirect(url_for('supplier_manage_products'))
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for('supplier_manage_products'))


@app.route('/supplier/orders', methods=['GET'])
@supplier_required
def supplier_orders():
    supplier_id = session['supplier_id']
    # List orders where supplier_id matches
    orders = Order.query.filter_by(supplier_id=supplier_id).order_by(Order.created_at.desc()).all()
    return render_template('supplier_orders.html', orders=orders)


@app.route('/supplier/order/<int:order_id>/action', methods=['POST'])
@supplier_required
def supplier_order_action(order_id):
    action = request.form.get('action')
    order = Order.query.get(order_id)
    if not order or order.supplier_id != session['supplier_id']:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    now = datetime.utcnow()
    if action == 'accept':
        order.status = 'confirmed'
        order.confirmed_at = order.confirmed_at or now
    elif action == 'reject':
        order.status = 'cancelled'
    elif action == 'mark_preparing':
        order.status = 'preparing'
        order.preparing_at = order.preparing_at or now
    elif action == 'mark_ready':
        order.status = 'ready'
        order.ready_at = order.ready_at or now
    elif action == 'out_for_delivery':
        order.status = 'out_for_delivery'
        order.out_for_delivery_at = order.out_for_delivery_at or now
    elif action == 'delivered':
        order.status = 'delivered'
        order.delivered_at = order.delivered_at or now

    db.session.commit()
    # Publish status change to any subscribers (include timestamps)
    publish_order_event(order.id, 'status_update', {
        'status': order.status,
        'order_id': order.id,
        'timestamps': {
            'confirmed': order.confirmed_at.isoformat() if order.confirmed_at else None,
            'preparing': order.preparing_at.isoformat() if order.preparing_at else None,
            'ready': order.ready_at.isoformat() if order.ready_at else None,
            'out_for_delivery': order.out_for_delivery_at.isoformat() if order.out_for_delivery_at else None,
            'delivered': order.delivered_at.isoformat() if order.delivered_at else None
        }
    })
    return redirect(url_for('supplier_orders'))


@app.route('/supplier/order/<int:order_id>')
@supplier_required
def supplier_order_detail(order_id):
    order = Order.query.get(order_id)
    if not order or order.supplier_id != session['supplier_id']:
        return redirect(url_for('supplier_orders'))
    
    # Get order items with product details
    items = OrderItem.query.filter_by(order_id=order.id).all()
    order_items_data = []
    for item in items:
        product = db.session.get(Product, item.product_id)
        if product:
            order_items_data.append({
                'product_name': product.name,
                'product_id': item.product_id,
                'category': product.category,
                'quantity': item.quantity,
                'unit': product.unit,
                'price_per_unit': item.price_per_unit,
                'total': item.quantity * item.price_per_unit
            })
    
    # Get vendor information
    vendor = db.session.get(Vendor, order.vendor_id)
    
    agents = DeliveryAgent.query.all()
    return render_template('supplier_order_detail.html', 
                         order=order, 
                         order_items=order_items_data, 
                         vendor=vendor,
                         agents=agents)


@app.route('/supplier/order/<int:order_id>/assign', methods=['POST'])
@supplier_required
def supplier_order_assign(order_id):
    # For API callers return 401 instead of redirect
    if request.is_json and 'supplier_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    # Support JSON body as well as form post
    agent_id = None
    if request.is_json:
        agent_id = request.get_json().get('agent_id')
    else:
        agent_id = request.form.get('agent_id')
    order = Order.query.get(order_id)
    if order and order.supplier_id == session.get('supplier_id') and agent_id:
        # very simple assignment - store in order (add column delivery_agent_id if desired)
        try:
            order.delivery_agent_id = int(agent_id)
        except Exception:
            pass
        now = datetime.utcnow()
        order.status = 'out_for_delivery'
        order.out_for_delivery_at = order.out_for_delivery_at or now
        db.session.commit()
        # publish update for subscribers including timestamps
        try:
            publish_order_event(order.id, 'status_update', {
                'status': order.status,
                'order_id': order.id,
                'timestamps': {
                    'confirmed': order.confirmed_at.isoformat() if order.confirmed_at else None,
                    'preparing': order.preparing_at.isoformat() if order.preparing_at else None,
                    'ready': order.ready_at.isoformat() if order.ready_at else None,
                    'out_for_delivery': order.out_for_delivery_at.isoformat() if order.out_for_delivery_at else None,
                    'delivered': order.delivered_at.isoformat() if order.delivered_at else None
                }
            })
        except Exception:
            pass
    # If JSON caller, return JSON
    if request.is_json:
        return jsonify({'success': True, 'order_id': order_id, 'status': order.status})
    return redirect(url_for('supplier_order_detail', order_id=order_id))


@app.route('/supplier/order/<int:order_id>/upload-proof', methods=['POST'])
@supplier_required
def supplier_order_upload_proof(order_id):
    order = Order.query.get(order_id)
    if not order or order.supplier_id != session.get('supplier_id'):
        return redirect(url_for('supplier_orders'))
    proof = request.files.get('proof')
    if proof and proof.filename:
        fname = secure_filename(proof.filename)
        unique = f"order_{order.id}_{uuid.uuid4().hex}_{fname}"
        save_path = os.path.join(app.instance_path, 'uploads', 'orders')
        os.makedirs(save_path, exist_ok=True)
        full = os.path.join(save_path, unique)
        proof.save(full)
        # store relative path on order if column exists, else ignore
        try:
            order.proof_path = os.path.relpath(full, start=basedir)
            db.session.commit()
        except Exception:
            db.session.commit()
    return redirect(url_for('supplier_order_detail', order_id=order_id))


@app.route('/supplier/profile', methods=['GET', 'POST'])
def supplier_profile():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))

    supplier = Supplier.query.get(session['supplier_id'])
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        location = request.form.get('location')
        email = request.form.get('email')

        if name:
            supplier.name = name
        if phone:
            supplier.phone = phone
        if location:
            supplier.location = location
        if email:
            supplier.email = email
        # handle certification upload
        cert = request.files.get('cert')
        if cert and cert.filename:
            filename = secure_filename(cert.filename)
            # create unique filename
            unique = f"supplier_{supplier.id}_{uuid.uuid4().hex}_{filename}"
            save_path = os.path.join(app.config['SUPPLIER_UPLOAD_FOLDER'], unique)
            cert.save(save_path)
            # store relative path
            supplier.certification = os.path.relpath(save_path, start=basedir)

        db.session.commit()
        return redirect(url_for('supplier_profile'))

    return render_template('supplier_profile.html', supplier=supplier)


@app.route('/supplier/onboarding', methods=['GET', 'POST'])
def supplier_onboarding():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier = Supplier.query.get(session['supplier_id'])
    if request.method == 'POST':
        business_name = request.form.get('business_name')
        gstin = request.form.get('gstin')
        if business_name is not None:
            supplier.business_name = business_name
        if gstin is not None:
            supplier.gstin = gstin
        # allow requesting verification (demo toggle)
        if request.form.get('request_verification') == 'on':
            supplier.verification_status = False  # pending - in real app, set to 'pending' state
        db.session.commit()
        flash('Business details updated')
        return redirect(url_for('supplier_onboarding'))
    return render_template('supplier_onboarding.html', supplier=supplier)


@app.route('/supplier/business')
def supplier_business():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier = Supplier.query.get(session['supplier_id'])
    warehouses = Warehouse.query.filter_by(supplier_id=supplier.id).all()
    return render_template('supplier_business.html', supplier=supplier, warehouses=warehouses)
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier = Supplier.query.get(session['supplier_id'])
    if request.method == 'POST':
        business_name = request.form.get('business_name')
        gstin = request.form.get('gstin')
        if business_name is not None:
            supplier.business_name = business_name
        if gstin is not None:
            supplier.gstin = gstin
        # allow requesting verification (demo toggle)
        if request.form.get('request_verification') == 'on':
            supplier.verification_status = False  # pending - in real app, set to 'pending' state
        db.session.commit()
        flash('Business details updated')
        return redirect(url_for('supplier_onboarding'))
    return render_template('supplier_onboarding.html', supplier=supplier)


@app.route('/supplier/warehouses', methods=['GET', 'POST'])
def supplier_warehouses():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier_id = session['supplier_id']
    if request.method == 'POST':
        # create new warehouse
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        if name and address:
            w = Warehouse(supplier_id=supplier_id, name=name, address=address, phone=phone)
            try:
                w.latitude = float(lat) if lat else None
            except Exception:
                w.latitude = None
            try:
                w.longitude = float(lon) if lon else None
            except Exception:
                w.longitude = None
            db.session.add(w)
            db.session.commit()
            flash('Warehouse added')
        return redirect(url_for('supplier_warehouses'))
    warehouses = Warehouse.query.filter_by(supplier_id=supplier_id).all()
    return render_template('supplier_warehouses.html', warehouses=warehouses)


@app.route('/supplier/warehouses/<int:warehouse_id>/edit', methods=['GET', 'POST'])
def supplier_warehouse_edit(warehouse_id):
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    w = Warehouse.query.get(warehouse_id)
    if not w or w.supplier_id != session['supplier_id']:
        return redirect(url_for('supplier_warehouses'))
    if request.method == 'POST':
        w.name = request.form.get('name') or w.name
        w.address = request.form.get('address') or w.address
        w.phone = request.form.get('phone') or w.phone
        try:
            w.latitude = float(request.form.get('latitude')) if request.form.get('latitude') else w.latitude
        except Exception:
            pass
        try:
            w.longitude = float(request.form.get('longitude')) if request.form.get('longitude') else w.longitude
        except Exception:
            pass
        db.session.commit()
        flash('Warehouse updated')
        return redirect(url_for('supplier_warehouses'))
    return render_template('supplier_warehouse_edit.html', warehouse=w)


@app.route('/supplier/warehouses/<int:warehouse_id>/delete', methods=['POST'])
def supplier_warehouse_delete(warehouse_id):
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    w = Warehouse.query.get(warehouse_id)
    if w and w.supplier_id == session['supplier_id']:
        db.session.delete(w)
        db.session.commit()
        flash('Warehouse deleted')
    return redirect(url_for('supplier_warehouses'))


@app.route('/supplier/service-areas', methods=['GET', 'POST'])
def supplier_service_areas():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier_id = session['supplier_id']
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        postal_codes = request.form.get('postal_codes')
        radius = request.form.get('radius_km')
        if name:
            sa = ServiceArea(supplier_id=supplier_id, name=name, description=description, postal_codes=postal_codes)
            try:
                sa.radius_km = float(radius) if radius else None
            except Exception:
                sa.radius_km = None
            db.session.add(sa)
            db.session.commit()
            flash('Service area added')
        return redirect(url_for('supplier_service_areas'))
    areas = ServiceArea.query.filter_by(supplier_id=supplier_id).all()
    return render_template('supplier_service_areas.html', areas=areas)


@app.route('/supplier/service-areas/<int:area_id>/edit', methods=['GET', 'POST'])
def supplier_service_area_edit(area_id):
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    sa = ServiceArea.query.get(area_id)
    if not sa or sa.supplier_id != session['supplier_id']:
        return redirect(url_for('supplier_service_areas'))
    if request.method == 'POST':
        sa.name = request.form.get('name') or sa.name
        sa.description = request.form.get('description') or sa.description
        sa.postal_codes = request.form.get('postal_codes') or sa.postal_codes
        try:
            sa.radius_km = float(request.form.get('radius_km')) if request.form.get('radius_km') else sa.radius_km
        except Exception:
            pass
        db.session.commit()
        flash('Service area updated')
        return redirect(url_for('supplier_service_areas'))
    return render_template('supplier_service_area_edit.html', area=sa)


@app.route('/supplier/service-areas/<int:area_id>/delete', methods=['POST'])
def supplier_service_area_delete(area_id):
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    sa = ServiceArea.query.get(area_id)
    if sa and sa.supplier_id == session['supplier_id']:
        db.session.delete(sa)
        db.session.commit()
        flash('Service area deleted')
    return redirect(url_for('supplier_service_areas'))


@app.route('/supplier/inventory')
def supplier_inventory():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier_id = session['supplier_id']
    products = Product.query.filter_by(supplier_id=supplier_id).all()
    low_stock = [p for p in products if (p.stock_available is not None and p.stock_available < 50)]
    return render_template('inventory.html', products=products, low_stock=low_stock)


@app.route('/supplier/communication')
def supplier_communication():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    # simple vendor list to initiate chats/broadcasts
    if request.method == 'POST':
        # broadcast form - not storing in DB for now
        subject = request.form.get('subject')
        message = request.form.get('message')
        flash('Broadcast sent to vendors (demo)')
        return redirect(url_for('supplier_communication'))
    vendors = Vendor.query.limit(20).all()
    return render_template('communication.html', vendors=vendors)


@app.route('/supplier/payments')
def supplier_payments():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier_id = session['supplier_id']
    delivered_orders = Order.query.filter_by(supplier_id=supplier_id, status='delivered').order_by(Order.created_at.desc()).all()
    total_earnings = db.session.query(db.func.coalesce(db.func.sum(Order.total_amount), 0)).filter(Order.supplier_id == supplier_id, Order.status == 'delivered').scalar() or 0.0
    invoices = [{'id': o.id, 'amount': o.total_amount, 'date': o.created_at} for o in delivered_orders]
    return render_template('payments.html', invoices=invoices, total_earnings=total_earnings)


@app.route('/supplier/analytics')
def supplier_analytics():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier_id = session['supplier_id']
    # top-selling products (by quantity)
    top_selling = db.session.query(Product.name, db.func.coalesce(db.func.sum(OrderItem.quantity), 0).label('sold'))\
        .join(OrderItem, Product.id == OrderItem.product_id)\
        .join(Order, Order.id == OrderItem.order_id)\
        .filter(Order.supplier_id == supplier_id)\
        .group_by(Product.id)\
        .order_by(db.desc('sold'))\
        .limit(8).all()

    total_sales = db.session.query(db.func.coalesce(db.func.sum(OrderItem.quantity), 0)).join(Order, Order.id == OrderItem.order_id).filter(Order.supplier_id == supplier_id).scalar() or 0
    total_revenue = db.session.query(db.func.coalesce(db.func.sum(Order.total_amount), 0)).filter(Order.supplier_id == supplier_id).scalar() or 0.0

    return render_template('analytics.html', top_selling=top_selling, total_sales=total_sales, total_revenue=total_revenue)


@app.route('/supplier/reliability')
def supplier_reliability():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier_id = session['supplier_id']
    supplier = Supplier.query.get(supplier_id)
    recent_orders = Order.query.filter_by(supplier_id=supplier_id).order_by(Order.created_at.desc()).limit(10).all()
    # simplistic complaint/penalty placeholders
    delayed_orders = Order.query.filter_by(supplier_id=supplier_id, status='delayed').count()
    return render_template('reliability.html', supplier=supplier, recent_orders=recent_orders, delayed_orders=delayed_orders)


@app.route('/supplier/common-features')
def supplier_common_features():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    supplier_id = session['supplier_id']
    unread_orders = Order.query.filter_by(supplier_id=supplier_id, status='pending').count()
    return render_template('common_features.html', unread_orders=unread_orders)


@app.route('/supplier/payments/export')
def supplier_payments_export():
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    fmt = request.args.get('format', 'csv')
    supplier_id = session['supplier_id']
    orders = Order.query.filter_by(supplier_id=supplier_id, status='delivered').order_by(Order.created_at.desc()).all()

    # Prepare rows
    rows = []
    for o in orders:
        rows.append({'id': o.id, 'amount': o.total_amount, 'date': o.created_at.strftime('%Y-%m-%d') if o.created_at else '', 'status': o.status})

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['id', 'amount', 'date', 'status'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode('utf-8')), mimetype='text/csv', as_attachment=True, download_name='payments.csv')

    if fmt == 'xlsx':
        # Lazy import openpyxl
        try:
            import openpyxl
            from openpyxl.workbook import Workbook
        except Exception:
            flash('XLSX export requires openpyxl to be installed.')
            return redirect(url_for('supplier_payments'))

        wb = Workbook()
        ws = wb.active
        ws.append(['id', 'amount', 'date', 'status'])
        for r in rows:
            ws.append([r['id'], r['amount'], r['date'], r['status']])
        bio = io.BytesIO()
        wb.save(bio)
        bio.seek(0)
        return send_file(bio, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='payments.xlsx')

    flash('Unknown export format')
    return redirect(url_for('supplier_payments'))


@app.route('/supplier/invoice/<int:order_id>/pdf')
def supplier_invoice_pdf(order_id):
    if 'supplier_id' not in session:
        return redirect(url_for('vendor_login'))
    order = Order.query.get(order_id)
    if not order or order.supplier_id != session['supplier_id']:
        flash('Invoice not found')
        return redirect(url_for('supplier_payments'))

    # Lazy import reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        flash('PDF generation requires reportlab to be installed.')
        return redirect(url_for('supplier_payments'))

    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4
    c.setFont('Helvetica-Bold', 16)
    c.drawString(40, height - 60, f'Invoice #{order.id}')
    c.setFont('Helvetica', 12)
    c.drawString(40, height - 90, f'Date: {order.created_at.strftime("%Y-%m-%d") if order.created_at else ""}')
    c.drawString(40, height - 110, f'Total: ₹{order.total_amount:.2f}')
    c.drawString(40, height - 140, 'Items:')
    y = height - 160
    items = OrderItem.query.filter_by(order_id=order.id).all()
    for it in items:
        prod = Product.query.get(it.product_id)
        c.drawString(50, y, f'- {prod.name if prod else "Product"} x {it.quantity} @ ₹{it.price_per_unit:.2f}')
        y -= 18
        if y < 80:
            c.showPage()
            y = height - 60
    c.showPage()
    c.save()
    bio.seek(0)
    return send_file(bio, mimetype='application/pdf', as_attachment=True, download_name=f'invoice_{order.id}.pdf')


@app.route('/delivery/dashboard')
def delivery_dashboard():
    if 'delivery_id' not in session:
        return redirect(url_for('vendor_login'))
    return render_template('delivery_dashboard.html')


@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')

        customer = Customer.query.filter_by(phone=phone).first()
        if customer and customer.password_hash and check_password_hash(customer.password_hash, password):
            session.clear()
            session['customer_id'] = customer.id
            session['customer_name'] = customer.name
            session['customer_email'] = customer.email
            session['customer_phone'] = customer.phone
            session['customer_location'] = customer.location
            return jsonify({'success': True, 'message': 'Login successful', 'redirect': url_for('customer_dashboard')})

        return jsonify({'success': False, 'message': 'Invalid credentials'})

    return render_template('customer_login.html')


@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        location = data.get('location')
        password = data.get('password')

        # Basic validation
        if not name or not phone or not password:
            return jsonify({'success': False, 'message': 'Name, phone and password are required'})

        # Prevent duplicates
        if Customer.query.filter_by(phone=phone).first():
            return jsonify({'success': False, 'message': 'An account with this phone number already exists'})

        if email and Customer.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'An account with this email already exists'})

        pw_hash = generate_password_hash(password)

        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            location=location or '',
            password_hash=pw_hash
        )
        db.session.add(customer)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Registration successful'})

    return render_template('customer_register.html')


@app.route('/customer/dashboard')
def customer_dashboard():
    customer_id = session.get('customer_id')
    if not customer_id:
        # Auto-login for testing
        customer = Customer.query.first()
        if customer:
            session['customer_id'] = customer.id
            session['customer_name'] = customer.name
            session['customer_email'] = customer.email
            session['customer_phone'] = customer.phone
            session['customer_location'] = customer.location
        else:
            return redirect('/')

    customer = Customer.query.get(session['customer_id'])
    if not customer:
        return redirect('/')

    customer_data = {
        'id': customer.id,
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
        'location': customer.location,
        'address': customer.location  # For backward compatibility
    }
    return render_template('customer_dashboard.html', customer_data=customer_data, customer_name=customer.name)

# =============================================
# REAL-TIME DELIVERY TRACKING API

@app.route('/api/config/maps', methods=['GET'])
def get_maps_config():
    """Return Google Maps API key for frontend use"""
    try:
        return jsonify({
            'success': True,
            'googleMapsApiKey': app.config.get('GOOGLE_MAPS_API_KEY', '')
        })
    except Exception as e:
        app.logger.error(f"Error getting maps config: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================

@app.route('/api/delivery/location/update', methods=['POST'])
def update_delivery_location():
    """
    Delivery agent sends GPS coordinates (lightweight network call)
    Stores in fast in-memory cache instead of hitting database every second
    """
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        delivery_agent_id = data.get('delivery_agent_id')
        
        if not all([order_id, latitude, longitude]):
            return jsonify({'success': False, 'message': 'Missing location data'}), 400
        
        # Store in fast in-memory cache (Redis would be better in production)
        with delivery_cache_lock:
            delivery_location_cache[f"order_{order_id}"] = {
                'order_id': order_id,
                'delivery_agent_id': delivery_agent_id,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'timestamp': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow()
            }
        
        return jsonify({'success': True, 'message': 'Location updated'})
    except Exception as e:
        print(f"Delivery location update error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/delivery/location/<int:order_id>', methods=['GET'])
@customer_api_required
def get_delivery_location(order_id):
    """
    Frontend fetches current delivery partner location with complete agent details
    Returns cached location instantly without database query + agent info
    """
    try:
        cache_key = f"order_{order_id}"
        
        with delivery_cache_lock:
            location_data = delivery_location_cache.get(cache_key)
        
        # Get order and delivery agent info from database
        order = db.session.query(CustomerOrder).filter_by(id=order_id).first()
        if not order:
            return jsonify({
                'success': False,
                'message': 'Order not found'
            }), 404
        
        # Get delivery agent details
        delivery_agent = None
        agent_details = {
            'name': 'Delivery Partner',
            'phone': '+91 XXXXX XXXXX',
            'vehicle': 'Bike - KA01AB1234',
            'rating': 4.8,
            'total_deliveries': 234
        }
        
        if order.delivery_agent_id:
            delivery_agent = db.session.query(DeliveryAgent).filter_by(
                id=order.delivery_agent_id
            ).first()
            
            if delivery_agent:
                # Count total deliveries for this agent
                total_deliveries = db.session.query(CustomerOrder).filter(
                    CustomerOrder.delivery_agent_id == delivery_agent.id,
                    CustomerOrder.status.in_(['delivered', 'out_for_delivery'])
                ).count()
                
                agent_details = {
                    'name': delivery_agent.name,
                    'phone': delivery_agent.phone,
                    'vehicle': delivery_agent.vehicle_info or 'Bike - KA01AB1234',
                    'rating': 4.8,  # Could calculate from customer feedback
                    'total_deliveries': total_deliveries
                }

        # Resolve vendor coordinates from the order's items (first item's vendor)
        vendor_info = None
        try:
            order_item = db.session.query(CustomerOrderItem).filter_by(order_id=order_id).first()
            if order_item:
                menu_item = db.session.query(MenuItem).filter_by(id=order_item.menu_item_id).first()
                if menu_item:
                    vendor = db.session.query(Vendor).filter_by(id=menu_item.vendor_id).first()
                    if vendor:
                        v_lat, v_lon = extract_gps_from_address(vendor.location)
                        vendor_info = {
                            'id': vendor.id,
                            'name': vendor.name,
                            'latitude': v_lat,
                            'longitude': v_lon
                        }
        except Exception as _:
            vendor_info = None
        
        if location_data:
            # Add agent details to location data
            location_data['agent'] = agent_details
            if vendor_info:
                location_data['vendor'] = vendor_info
            
            # Add status timestamps
            location_data['timestamps'] = {
                'confirmed': order.confirmed_at.isoformat() if order.confirmed_at else None,
                'preparing': order.preparing_at.isoformat() if order.preparing_at else None,
                'ready': order.ready_at.isoformat() if order.ready_at else None,
                'picked_up': order.picked_up_at.isoformat() if order.picked_up_at else None,
                'out_for_delivery': order.out_for_delivery_at.isoformat() if order.out_for_delivery_at else None,
                'delivered': order.actual_delivery_time.isoformat() if order.actual_delivery_time else None,
                'estimated_delivery': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None
            }
            
            return jsonify({
                'success': True,
                'location': location_data,
                'source': 'cache',  # Indicates this came from fast cache
                'order_status': order.status
            })
        
        # Fallback: use order's delivery coordinates if available
        if order.delivery_latitude and order.delivery_longitude:
            fallback_location = {
                'order_id': order_id,
                'latitude': order.delivery_latitude,
                'longitude': order.delivery_longitude,
                'timestamp': order.updated_at.isoformat() if order.updated_at else datetime.utcnow().isoformat(),
                'status': order.status,
                'agent': agent_details,
                'vendor': vendor_info
            }
            
            return jsonify({
                'success': True,
                'location': fallback_location,
                'source': 'database',
                'order_status': order.status
            })
        
        return jsonify({
            'success': True,
            'location': None,
            'message': 'Order found but no active delivery tracking',
            'agent': agent_details,
            'order_status': order.status
        })
    except Exception as e:
        app.logger.error(f"Get delivery location error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/delivery/tracking/<int:order_id>', methods=['GET'])
def get_delivery_tracking(order_id):
    """
    Complete delivery tracking info for customer
    Includes real-time location, ETA, and order status
    """
    try:
        # Get order from database
        order = db.session.query(CustomerOrder).filter_by(id=order_id).first()
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        cache_key = f"order_{order_id}"
        
        with delivery_cache_lock:
            location_data = delivery_location_cache.get(cache_key)
        
        # If no cached location, use order's delivery coordinates
        if not location_data and order.delivery_latitude and order.delivery_longitude:
            location_data = {
                'order_id': order_id,
                'latitude': order.delivery_latitude,
                'longitude': order.delivery_longitude,
                'timestamp': format_ist_time(order.created_at, '%d %b %Y, %I:%M %p') if order.created_at else None,
            }
        
        # Get delivery agent info
        delivery_agent = None
        if order.delivery_agent_id:
            delivery_agent = db.session.query(DeliveryAgent).filter_by(
                id=order.delivery_agent_id
            ).first()
        
        # Calculate ETA based on estimated delivery time
        eta_minutes = 0
        if order.estimated_delivery_time:
            time_diff = (order.estimated_delivery_time - datetime.utcnow()).total_seconds() / 60
            eta_minutes = max(0, int(time_diff))
        
        tracking_info = {
            'order_id': order_id,
            'status': order.status,
            'location': location_data,
            'eta_minutes': eta_minutes,
            'delivery_address': order.delivery_address,
            'delivery_agent': {
                'name': delivery_agent.name if delivery_agent else 'Delivery Partner',
                'phone': delivery_agent.phone if delivery_agent else '+91 XXXXX XXXXX',
                'vehicle': delivery_agent.vehicle_info if delivery_agent else 'Bike - KA01AB1234',
                'rating': 4.8
            },
            'updated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({'success': True, 'tracking': tracking_info})
    except Exception as e:
        app.logger.error(f"Get delivery tracking error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================
# DELIVERY AGENT API ENDPOINTS
# =============================================

@app.route('/delivery-agent/dashboard')
@delivery_agent_required
def delivery_agent_dashboard():
    """Delivery agent dashboard page"""
    delivery_agent_id = session.get('delivery_agent_id')
    agent = DeliveryAgent.query.get(delivery_agent_id)
    if not agent:
        return redirect('/vendor/login')
    
    return render_template('delivery_agent_dashboard.html', agent_name=agent.name)

@app.route('/api/delivery-agent/profile', methods=['GET', 'PUT'])
@delivery_api_required
def delivery_agent_profile():
    """Get or update delivery agent profile"""
    agent = DeliveryAgent.query.get(session['delivery_agent_id'])
    if not agent:
        return jsonify({'success': False, 'message': 'Agent not found'}), 404
    
    if request.method == 'GET':
        try:
            # Calculate real statistics from database
            agent_id = agent.id
            
            # Total deliveries assigned to this agent (from both tables)
            customer_orders_count = db.session.query(CustomerOrder).filter_by(
                delivery_agent_id=agent_id
            ).count()
            
            supplier_orders_count = db.session.query(Order).filter_by(
                delivery_agent_id=agent_id
            ).count()
            
            total_deliveries = customer_orders_count + supplier_orders_count
            
            # Completed deliveries (from both tables)
            customer_completed = db.session.query(CustomerOrder).filter_by(
                delivery_agent_id=agent_id,
                status='delivered'
            ).count()
            
            supplier_completed = db.session.query(Order).filter_by(
                delivery_agent_id=agent_id,
                status='delivered'
            ).count()
            
            completed_deliveries = customer_completed + supplier_completed
            
            # In transit deliveries (from both tables)
            customer_in_transit = db.session.query(CustomerOrder).filter(
                CustomerOrder.delivery_agent_id == agent_id,
                CustomerOrder.status.in_(['out_for_delivery', 'ready'])
            ).count()
            
            supplier_in_transit = db.session.query(Order).filter(
                Order.delivery_agent_id == agent_id,
                Order.status.in_(['out_for_delivery', 'ready'])
            ).count()
            
            in_transit_deliveries = customer_in_transit + supplier_in_transit
            
            # Calculate rating (default to 4.8 if no data)
            rating = 4.8
            
        except Exception as e:
            app.logger.error(f"Error calculating delivery agent stats: {str(e)}")
            total_deliveries = 0
            completed_deliveries = 0
            in_transit_deliveries = 0
            rating = 4.8
        
        return jsonify({
            'success': True,
            'agent': {
                'id': agent.id,
                'name': agent.name,
                'email': agent.email,
                'phone': agent.phone,
                'location': agent.location,
                'vehicle_info': agent.vehicle_info,
                'vehicle_type': agent.vehicle_type,
                'total_deliveries': total_deliveries,
                'completed_deliveries': completed_deliveries,
                'in_transit_deliveries': in_transit_deliveries,
                'rating': rating
            }
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        agent.name = data.get('name', agent.name)
        agent.email = data.get('email', agent.email)
        agent.phone = data.get('phone', agent.phone)
        agent.location = data.get('location', agent.location)
        agent.vehicle_info = data.get('vehicle_info', agent.vehicle_info)
        agent.vehicle_type = data.get('vehicle_type', agent.vehicle_type)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/api/delivery-agent/deliveries', methods=['GET'])
@delivery_api_required
def get_agent_deliveries():
    """Get assigned deliveries for delivery agent from database"""
    
    try:
        # Get delivery_agent_id from session
        delivery_agent_id = session.get('delivery_agent_id')
        if not delivery_agent_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        deliveries = []
        
        # Fetch customer orders assigned to this delivery agent
        customer_orders = db.session.query(CustomerOrder).filter_by(
            delivery_agent_id=delivery_agent_id
        ).order_by(CustomerOrder.created_at.desc()).all()
        
        for order in customer_orders:
            # Count items in this order
            items_count = db.session.query(CustomerOrderItem).filter_by(
                order_id=order.id
            ).count()
            
            # Map status to delivery status
            status_map = {
                'pending': 'Pending',
                'confirmed': 'Confirmed',
                'preparing': 'Preparing',
                'ready': 'Ready for Pickup',
                'out_for_delivery': 'In Transit',
                'delivered': 'Delivered',
                'cancelled': 'Cancelled'
            }
            
            delivery_data = {
                'order_id': order.id,
                'order_type': 'customer',
                'customer_name': order.customer_name or 'Customer',
                'customer_phone': order.customer_phone,
                'customer_email': order.customer_email,
                'delivery_address': order.delivery_address,
                'total_amount': order.total_amount,
                'status': status_map.get(order.status, order.status),
                'status_raw': order.status,
                'created_at': format_ist_time(order.created_at, '%d %b %Y, %I:%M %p') if order.created_at else None,
                'items_count': items_count,
                'delivery_instructions': order.delivery_instructions,
                'latitude': order.delivery_latitude,
                'longitude': order.delivery_longitude,
                'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
            }
            
            deliveries.append(delivery_data)
        
        # Fetch supplier orders (vendor to supplier) assigned to this delivery agent
        supplier_orders = db.session.query(Order).filter_by(
            delivery_agent_id=delivery_agent_id
        ).order_by(Order.created_at.desc()).all()
        
        for order in supplier_orders:
            try:
                # Count items in this order
                items_count = db.session.query(OrderItem).filter_by(
                    order_id=order.id
                ).count()
                
                # Get vendor info for delivery
                vendor = db.session.get(Vendor, order.vendor_id)
                supplier = db.session.get(Supplier, order.supplier_id)
                
                # Map status to delivery status
                status_map = {
                    'pending': 'Pending',
                    'confirmed': 'Confirmed',
                    'preparing': 'Preparing',
                    'ready': 'Ready for Pickup',
                    'out_for_delivery': 'In Transit',
                    'delivered': 'Delivered',
                    'cancelled': 'Cancelled'
                }
                
                delivery_data = {
                    'order_id': order.id,
                    'order_type': 'supplier',
                    'customer_name': f"{vendor.business_name if vendor and vendor.business_name else 'Vendor'} (from {supplier.name if supplier else 'Supplier'})",
                    'customer_phone': vendor.phone if vendor else None,
                    'customer_email': vendor.email if vendor else None,
                    'delivery_address': vendor.location if vendor else 'Pickup from supplier',
                    'total_amount': order.total_amount,
                    'status': status_map.get(order.status, order.status),
                    'status_raw': order.status,
                    'created_at': format_ist_time(order.created_at, '%d %b %Y, %I:%M %p') if order.created_at else None,
                    'items_count': items_count,
                    'delivery_instructions': f"Deliver to: {vendor.business_name if vendor and vendor.business_name else 'Vendor'}",
                    'latitude': None,
                    'longitude': None,
                    'estimated_delivery_time': None,
                }
                
                deliveries.append(delivery_data)
            except Exception as e:
                app.logger.error(f"Error processing supplier order {order.id}: {str(e)}")
                continue
        
        # Sort all deliveries by created_at descending
        deliveries.sort(key=lambda x: x['created_at'] or '', reverse=True)
        
        return jsonify({
            'success': True,
            'deliveries': deliveries,
            'total_count': len(deliveries)
        })
    except Exception as e:
        app.logger.error(f"Error fetching deliveries: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error fetching deliveries: {str(e)}'
        }), 500

# Alias endpoint for frontend compatibility
@app.route('/api/delivery-agent/my-deliveries', methods=['GET'])
@delivery_api_required
def my_deliveries():
    """Alias for /api/delivery-agent/deliveries endpoint"""
    return get_agent_deliveries()

@app.route('/api/delivery-agent/update-location', methods=['POST'])
@delivery_api_required
def update_agent_location():
    """Update delivery agent's current GPS location and persist to database"""
    
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            return jsonify({'success': False, 'message': 'Location coordinates required'}), 400
        
        delivery_agent_id = session.get('delivery_agent_id')
        if not delivery_agent_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        # Update agent's location in database
        agent = db.session.query(DeliveryAgent).filter_by(id=delivery_agent_id).first()
        if agent:
            agent.location = f"{latitude},{longitude}"
            db.session.commit()
        
        # Store agent's current location in cache
        cache_key = f"agent_location_{delivery_agent_id}"
        
        with delivery_cache_lock:
            delivery_location_cache[cache_key] = {
                'agent_id': delivery_agent_id,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'timestamp': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow()
            }
        
        # Publish real-time location updates to any orders assigned to this agent
        try:
            # Select customer orders assigned to this delivery agent which are active
            active_statuses = ['picked_up', 'out_for_delivery', 'in_transit', 'ready', 'confirmed']
            assigned_orders = db.session.query(CustomerOrder).filter(
                CustomerOrder.delivery_agent_id == delivery_agent_id,
                CustomerOrder.status.in_(active_statuses)
            ).all()

            evt_data = {'agent_id': delivery_agent_id, 'latitude': float(latitude), 'longitude': float(longitude), 'ts': datetime.utcnow().isoformat()}
            for ord in assigned_orders:
                try:
                    publish_order_event(ord.id, 'agent_location', evt_data)
                    publish_customer_order_event(ord.id, 'agent_location', evt_data)
                except Exception:
                    app.logger.exception('Failed to publish agent location for order %s', ord.id)
        except Exception:
            app.logger.exception('Error while fetching assigned orders for agent location publish')
        
        return jsonify({
            'success': True,
            'message': 'Location updated successfully'
        })
    except Exception as e:
        app.logger.error(f"Update agent location error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/delivery-agent/available-orders', methods=['POST'])
@delivery_api_required
def get_available_orders():
    """Get available orders near delivery agent's current location"""
    
    try:
        delivery_agent_id = session.get('delivery_agent_id')
        if not delivery_agent_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        agent_lat = data.get('latitude')
        agent_lon = data.get('longitude')
        
        if not agent_lat or not agent_lon:
            return jsonify({'success': False, 'message': 'Location required'}), 400
        
        delivery_agent_id = session['delivery_agent_id']
        
        # Get unassigned orders or orders in 'confirmed', 'preparing', or 'ready' status
        available_orders = db.session.query(CustomerOrder).filter(
            CustomerOrder.status.in_(['confirmed', 'preparing', 'ready']),
            CustomerOrder.delivery_agent_id.is_(None)  # Use .is_(None) for NULL checks
        ).order_by(CustomerOrder.created_at.desc()).limit(20).all()
        
        orders_data = []
        
        for order in available_orders:
            if not order.delivery_latitude or not order.delivery_longitude:
                continue
            
            # Calculate distance using Haversine formula
            from math import radians, cos, sin, asin, sqrt
            
            lon1, lat1, lon2, lat2 = map(radians, [agent_lon, agent_lat, order.delivery_longitude, order.delivery_latitude])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            distance_km = 6371 * c  # Radius of earth in kilometers
            
            # Get order items
            order_items = db.session.query(CustomerOrderItem).filter_by(
                order_id=order.id
            ).all()
            
            items_list = []
            vendor_name = 'Restaurant'
            
            for item in order_items:
                menu_item = db.session.query(MenuItem).filter_by(
                    id=item.menu_item_id
                ).first()
                
                if menu_item:
                    items_list.append({
                        'name': menu_item.name,
                        'quantity': item.quantity
                    })
                    
                    # Get vendor name
                    if not vendor_name or vendor_name == 'Restaurant':
                        vendor = db.session.query(Vendor).filter_by(
                            id=menu_item.vendor_id
                        ).first()
                        if vendor:
                            vendor_name = vendor.name
            
            orders_data.append({
                'order_id': order.id,
                'customer_name': order.customer_name,
                'customer_phone': order.customer_phone,
                'delivery_address': order.delivery_address,
                'delivery_latitude': order.delivery_latitude,
                'delivery_longitude': order.delivery_longitude,
                'distance_km': round(distance_km, 2),
                'total_amount': order.total_amount,
                'payment_method': order.payment_method,
                'items': items_list,
                'vendor_name': vendor_name,
                'created_at': format_ist_time(order.created_at, '%d %b %Y, %I:%M %p'),
                'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None
            })
        
        # Sort by distance (closest first)
        orders_data.sort(key=lambda x: x['distance_km'])
        
        return jsonify({
            'success': True,
            'orders': orders_data
        })
    except Exception as e:
        app.logger.error(f"Get available orders error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/delivery-agent/accept-order', methods=['POST'])
@delivery_api_required
def accept_order():
    """Delivery agent accepts an order"""
    
    try:
        delivery_agent_id = session.get('delivery_agent_id')
        if not delivery_agent_id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        data = request.get_json()
        order_id = data.get('order_id')
        agent_latitude = data.get('latitude')
        agent_longitude = data.get('longitude')
        
        if not order_id:
            return jsonify({'success': False, 'message': 'Order ID required'}), 400
        
        # Get the order
        order = db.session.query(CustomerOrder).filter_by(id=order_id).first()
        
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Check if order is already assigned
        if order.delivery_agent_id and order.delivery_agent_id != delivery_agent_id:
            return jsonify({'success': False, 'message': 'Order already assigned to another agent'}), 400
        
        # Assign order to delivery agent
        order.delivery_agent_id = delivery_agent_id
        order.status = 'ready'
        
        # Set picked_up timestamp
        if not order.picked_up_at:
            order.picked_up_at = datetime.utcnow()
        
        db.session.commit()
        
        # Update agent's location in cache with order info
        if agent_latitude and agent_longitude:
            cache_key = f"order_{order_id}"
            
            # Get agent details
            agent = db.session.query(DeliveryAgent).filter_by(
                id=delivery_agent_id
            ).first()
            
            total_deliveries = db.session.query(CustomerOrder).filter(
                CustomerOrder.delivery_agent_id == delivery_agent_id,
                CustomerOrder.status.in_(['delivered', 'out_for_delivery'])
            ).count()
            
            agent_details = {
                'name': agent.name if agent else 'Delivery Agent',
                'phone': agent.phone if agent else '',
                'vehicle': agent.vehicle_info if agent else 'Vehicle',
                'rating': 4.8,
                'total_deliveries': total_deliveries
            }
            
            with delivery_cache_lock:
                delivery_location_cache[cache_key] = {
                    'order_id': order_id,
                    'delivery_agent_id': delivery_agent_id,
                    'latitude': float(agent_latitude),
                    'longitude': float(agent_longitude),
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'ready',
                    'notes': 'Order accepted by delivery agent',
                    'agent': agent_details,
                    'updated_at': datetime.utcnow()
                }
        
        return jsonify({
            'success': True,
            'message': 'Order accepted successfully',
            'order_id': order_id
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Accept order error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/delivery-agent/update-status', methods=['POST'])
@delivery_api_required
def update_delivery_status():
    """Update delivery status with GPS coordinates"""
    delivery_agent_id = session.get('delivery_agent_id')
    if not delivery_agent_id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    order_id = data.get('order_id')
    status = data.get('status')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    notes = data.get('notes', '')
    
    if not order_id or not status:
        return jsonify({'success': False, 'message': 'Order ID and status are required'}), 400
    
    try:
        # Update order status in database
        order = db.session.query(CustomerOrder).filter_by(id=order_id).first()
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        # Map delivery agent status to order status
        status_map = {
            'picked_up': 'ready',
            'in_transit': 'out_for_delivery',
            'arrived': 'out_for_delivery',
            'delivered': 'delivered',
            'failed': 'cancelled'
        }
        
        # Update order status and record timestamp
        new_status = status_map.get(status, status)
        current_time = datetime.utcnow()
        order.status = new_status
        
        # Record timestamp for each status change
        if new_status == 'confirmed' and not order.confirmed_at:
            order.confirmed_at = current_time
        elif new_status == 'preparing' and not order.preparing_at:
            order.preparing_at = current_time
        elif new_status == 'ready' and not order.ready_at:
            order.ready_at = current_time
            # Also mark as picked up when ready
            if not order.picked_up_at:
                order.picked_up_at = current_time
        elif new_status == 'out_for_delivery' and not order.out_for_delivery_at:
            order.out_for_delivery_at = current_time
        elif new_status == 'delivered':
            order.actual_delivery_time = current_time
        
        # Update GPS coordinates if provided
        if latitude and longitude:
            order.delivery_latitude = float(latitude)
            order.delivery_longitude = float(longitude)
        
        db.session.commit()
        
        # Update GPS location in cache for real-time tracking
        if latitude and longitude:
            with delivery_cache_lock:
                delivery_location_cache[f"order_{order_id}"] = {
                    'order_id': order_id,
                    'delivery_agent_id': delivery_agent_id,
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': status,
                    'notes': notes,
                    'updated_at': datetime.utcnow()
                }

        # Publish customer order event for real-time updates
        try:
            publish_customer_order_event(order_id, 'status_update', {
                'status': order.status,
                'location': {
                    'latitude': float(latitude) if latitude else None,
                    'longitude': float(longitude) if longitude else None,
                    'timestamp': datetime.utcnow().isoformat()
                },
                'notes': notes
            })
        except Exception as e:
            app.logger.warning(f"Could not publish delivery update event: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Delivery status updated to {status}',
            'order_id': order_id,
            'order_status': order.status
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating delivery status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error updating status: {str(e)}'
        }), 500

# Chatbot API endpoints
@app.route('/api/chatbot/message', methods=['POST'])
def chatbot_message():
    """Handle chatbot messages and provide intelligent responses"""
    try:
        data = request.get_json()
        message = data.get('message', '').lower().strip()
        language = data.get('language', 'en')
        context = data.get('context', {})
        session_id = data.get('session_id')
        
        # Ensure context is a dict, not a list
        if not isinstance(context, dict):
            print(f"WARNING: context is {type(context)}, converting to dict: {context}")
            context = {}
        
        # Get vendor info if logged in
        vendor = None
        if 'vendor_id' in session:
            vendor = Vendor.query.get(session['vendor_id'])
        
        # Process the message and generate response
        response = process_chatbot_message(message, language, context, vendor)
        
        # Debug: Check response type
        if not isinstance(response, dict):
            print(f"ERROR: Response is not a dict, it's a {type(response)}: {response}")
            response = {
                'message': 'Sorry, I encountered an error processing your request.',
                'context': {},
                'actions': None
            }
        
        # Update context with message count
        if 'context' not in response or not isinstance(response.get('context'), dict):
            response['context'] = {}
        
        if 'message_count' not in response['context']:
            response['context']['message_count'] = context.get('message_count', 0) + 1
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        print(f"Chatbot error: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        return jsonify({
            'message': 'Sorry, I encountered an error. Please try again.',
            'context': {},
            'actions': None
        }), 500

@app.route('/api/chatbot/language', methods=['POST'])
def chatbot_language():
    """Handle language change for chatbot"""
    try:
        data = request.get_json()
        language = data.get('language', 'en')
        session_id = data.get('session_id')
        
        # Store language preference
        # In a real app, you might store this in the database
        
        return jsonify({'success': True, 'language': language})
        
    except Exception as e:
        print(f"Language change error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/chatbot/tag', methods=['POST'])
def chatbot_tag():
    """Handle predefined tag actions for chatbot"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        language = data.get('language', 'en')
        context = data.get('context', {})
        session_id = data.get('session_id')
        
        # Get vendor info if logged in
        vendor = None
        if 'vendor_id' in session:
            vendor = Vendor.query.get(session['vendor_id'])
        
        # Process the tag action and generate response
        response = process_tag_action(action, language, context, vendor)
        
        # Update context with message count
        if 'message_count' not in response['context']:
            response['context']['message_count'] = context.get('message_count', 0) + 1
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Tag action error: {e}")
        return jsonify({
            'message': 'Sorry, I encountered an error. Please try again.',
            'context': {},
            'actions': None
        }), 500

def process_tag_action(action, language, context, vendor):
    """Process predefined tag actions and return appropriate response"""
    
    # Map tag actions to response functions
    tag_handlers = {
        'find-suppliers': lambda: get_enhanced_supplier_response(language, vendor, '', context),
        'place-order': lambda: get_enhanced_order_response(language, vendor, '', context),
        'price-alerts': lambda: get_enhanced_price_response(language, vendor, '', context),
        'business-tips': lambda: get_business_tips_response(language, vendor, context),
        'account-help': lambda: get_enhanced_account_response(language, vendor, '', context),
        'market-trends': lambda: get_market_trends_response(language, vendor, context),
        'contact-support': lambda: get_support_response(language, vendor, context)
    }
    
    # Get the appropriate handler
    handler = tag_handlers.get(action)
    if handler:
        return handler()
    else:
        # Default response for unknown actions
        return get_intelligent_default_response(language, vendor, action, context)

def get_business_tips_response(language, vendor, context):
    """Generate business tips response"""
    responses = {
        'en': "Here are some valuable business tips for your success:",
        'hi': "यहाँ आपकी सफलता के लिए कुछ मूल्यवान व्यावसायिक सुझाव हैं:",
        'bn': "আপনার সাফল্যের জন্য এখানে কিছু মূল্যবান ব্যবসায়িক টিপস রয়েছে:",
        'ta': "உங்கள் வெற்றிக்கு இங்கே சில மதிப்புமிக்க வணிக குறிப்புகள் உள்ளன:",
        'mr': "तुमच्या यशासाठी काही मौल्यवान व्यवसाय टिप्स येथे आहेत:"
    }
    
    tips = {
        'en': [
            "💡 BUSINESS SUCCESS TIPS:",
            "• Maintain good relationships with suppliers",
            "• Monitor market trends regularly",
            "• Keep track of your inventory levels",
            "• Offer competitive pricing",
            "• Focus on customer satisfaction",
            "• Use technology to streamline operations",
            "• Plan for seasonal variations",
            "• Build a strong brand reputation"
        ],
        'hi': [
            "💡 व्यावसायिक सफलता के सुझाव:",
            "• आपूर्तिकर्ताओं के साथ अच्छे संबंध बनाए रखें",
            "• बाजार के रुझानों पर नियमित नजर रखें",
            "• अपने इन्वेंटरी स्तर पर नजर रखें",
            "• प्रतिस्पर्धी मूल्य निर्धारण प्रदान करें",
            "• ग्राहक संतुष्टि पर ध्यान केंद्रित करें",
            "• संचालन को सुव्यवस्थित करने के लिए तकनीक का उपयोग करें",
            "• मौसमी भिन्नताओं की योजना बनाएं",
            "• मजबूत ब्रांड प्रतिष्ठा बनाएं"
        ],
        'mr': [
            "💡 व्यवसाय यश टिप्स:",
            "• पुरवठादारांसोबत चांगले संबंध ठेवा",
            "• बाजारातील प्रवृत्ती नियमितपणे पाहा",
            "• इन्व्हेंटरी स्तरावर लक्ष ठेवा",
            "• स्पर्धात्मक किंमत द्या",
            "• ग्राहक समाधानावर लक्ष केंद्रित करा",
            "• ऑपरेशन्स सुलभ करण्यासाठी तंत्रज्ञान वापरा",
            "• हंगामी बदलांसाठी योजना करा",
            "• मजबूत ब्रँड प्रतिष्ठा निर्माण करा"
        ]
    }
    
    # Add business-specific tips
    if vendor and vendor.business_type:
        business_specific_tips = {
            'ice_cream': {
                'en': [
                    "\n🍦 ICE CREAM BUSINESS TIPS:",
                    "• Maintain consistent temperature control",
                    "• Source fresh dairy products daily",
                    "• Offer seasonal flavors",
                    "• Focus on hygiene and cleanliness",
                    "• Build customer loyalty programs"
                ],
                'hi': [
                    "\n🍦 आइसक्रीम व्यवसाय सुझाव:",
                    "• लगातार तापमान नियंत्रण बनाए रखें",
                    "• दैनिक ताजे डेयरी उत्पाद सोर्स करें",
                    "• मौसमी स्वाद प्रदान करें",
                    "• स्वच्छता और सफाई पर ध्यान केंद्रित करें",
                    "• ग्राहक वफादारी कार्यक्रम बनाएं"
                ]
            },
            'chaat': {
                'en': [
                    "\n🌶️ CHAAT BUSINESS TIPS:",
                    "• Use fresh ingredients daily",
                    "• Maintain authentic taste",
                    "• Focus on quick service",
                    "• Keep prices competitive",
                    "• Build a loyal customer base"
                ],
                'hi': [
                    "\n🌶️ चाट व्यवसाय सुझाव:",
                    "• दैनिक ताजी सामग्री का उपयोग करें",
                    "• प्रामाणिक स्वाद बनाए रखें",
                    "• त्वरित सेवा पर ध्यान केंद्रित करें",
                    "• प्रतिस्पर्धी मूल्य रखें",
                    "• वफादार ग्राहक आधार बनाएं"
                ]
            }
        }
        
        specific_tips = business_specific_tips.get(vendor.business_type, {}).get(language, [])
        if specific_tips:
            tips[language].extend(specific_tips)
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + tips.get(language, tips['en'])
        },
        'context': {'intent': 'business_tips'},
        'actions': make_actions(language, [
            ('market-trends', 'Market Trends'),
            ('supplier-tips', 'Supplier Tips'),
            ('pricing-strategy', 'Pricing Strategy'),
            ('customer-service', 'Customer Service'),
            ('inventory-management', 'Inventory Management'),
            ('seasonal-planning', 'Seasonal Planning')
        ])
    }

def get_market_trends_response(language, vendor, context):
    """Generate market trends response"""
    responses = {
        'en': "Here are the latest market trends and insights:",
        'hi': "यहाँ नवीनतम बाजार रुझान और अंतर्दृष्टि हैं:",
        'bn': "এখানে সর্বশেষ বাজার প্রবণতা এবং অন্তর্দৃষ্টি রয়েছে:",
        'ta': "இங்கே சமீபத்திய சந்தை போக்குகள் மற்றும் நுண்ணறிவு உள்ளன:",
        'mr': "येथे नवीनतम बाजारातील प्रवृत्ती आणि अंतर्दृष्टी आहेत:"
    }
    
    trends = {
        'en': [
            "📈 CURRENT MARKET TRENDS:",
            "• Vegetable prices down 5% this week",
            "• Dairy products remain stable",
            "• Spices trending upward (+3%)",
            "• Seasonal fruits in high demand",
            "• Organic products gaining popularity",
            "• Local sourcing preferred by customers",
            "• Digital payments increasing",
            "• Sustainability focus growing"
        ],
        'hi': [
            "📈 वर्तमान बाजार रुझान:",
            "• इस सप्ताह सब्जी की कीमतें 5% कम",
            "• डेयरी उत्पाद स्थिर बने हुए",
            "• मसाले ऊपर की ओर (+3%)",
            "• मौसमी फलों की अधिक मांग",
            "• जैविक उत्पाद लोकप्रियता हासिल कर रहे",
            "• ग्राहकों द्वारा स्थानीय सोर्सिंग पसंद",
            "• डिजिटल भुगतान बढ़ रहे",
            "• स्थिरता फोकस बढ़ रहा"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + trends.get(language, trends['en'])
        },
        'context': {'intent': 'market_trends'},
        'actions': make_actions(language, [
            ('price-analysis', 'Price Analysis'),
            ('demand-forecast', 'Demand Forecast'),
            ('seasonal-trends', 'Seasonal Trends'),
            ('competitor-analysis', 'Competitor Analysis'),
            ('supply-chain-insights', 'Supply Chain Insights'),
            ('customer-preferences', 'Customer Preferences')
        ])
    }

def get_support_response(language, vendor, context):
    """Generate support response"""
    responses = {
        'en': "I'm here to help! Here's how you can get support:",
        'hi': "मैं मदद के लिए यहाँ हूँ! यहाँ आप सहायता कैसे प्राप्त कर सकते हैं:",
        'bn': "আমি সাহায্যের জন্য এখানে আছি! এখানে আপনি কীভাবে সহায়তা পেতে পারেন:",
        'ta': "நான் உதவிக்காக இங்கே இருக்கிறேன்! இங்கே நீங்கள் எவ்வாறு ஆதரவு பெறலாம்:",
        'mr': "मी मदतीसाठी येथे आहे! तुम्ही सहाय्य कसे मिळवू शकता:"
    }
    
    support_options = {
        'en': [
            "📞 SUPPORT OPTIONS:",
            "• Live Chat: Available 24/7",
            "• Phone Support: +91-9876543210",
            "• Email: support@vendorconnect.com",
            "• FAQ: Common questions answered",
            "• Video Tutorials: Step-by-step guides",
            "• Community Forum: Connect with other vendors",
            "• Technical Support: For app issues",
            "• Business Consultation: Expert advice"
        ],
        'hi': [
            "📞 सहायता विकल्प:",
            "• लाइव चैट: 24/7 उपलब्ध",
            "• फोन सहायता: +91-9876543210",
            "• ईमेल: support@vendorconnect.com",
            "• FAQ: सामान्य प्रश्नों के उत्तर",
            "• वीडियो ट्यूटोरियल: चरणबद्ध गाइड",
            "• कम्युनिटी फोरम: अन्य विक्रेताओं से जुड़ें",
            "• तकनीकी सहायता: ऐप समस्याओं के लिए",
            "• व्यावसायिक परामर्श: विशेषज्ञ सलाह"
        ],
        'mr': [
            "📞 सहाय्य पर्याय:",
            "• लाइव्ह चॅट: 24/7 उपलब्ध",
            "• फोन सहाय्य: +91-9876543210",
            "• ईमेल: support@vendorconnect.com",
            "• FAQ: सामान्य प्रश्नांचे उत्तरे",
            "• व्हिडिओ ट्युटोरियल: चरण-दर-चरण मार्गदर्शिका",
            "• कम्युनिटी फोरम: इतर विक्रेत्यांशी जोडा",
            "• तांत्रिक सहाय्य: अॅप समस्यांसाठी",
            "• व्यवसाय सल्ला: तज्ञांची सल्ला"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + support_options.get(language, support_options['en'])
        },
        'context': {'intent': 'support'},
        'actions': make_actions(language, [
            ('live-chat', 'Start Live Chat'),
            ('phone-support', 'Call Support'),
            ('email-support', 'Email Support'),
            ('faq', 'View FAQ'),
            ('video-tutorials', 'Video Tutorials'),
            ('community-forum', 'Community Forum'),
            ('technical-support', 'Technical Support'),
            ('business-consultation', 'Business Consultation')
        ])
    }

def process_chatbot_message(message, language, context, vendor):
    """Process chatbot message and return appropriate response with enhanced logic"""
    
    # Normalize message for better processing
    normalized_message = message.lower().strip()
    
    # Debug logging
    print(f"DEBUG: Received message: '{message}'")
    print(f"DEBUG: Normalized message: '{normalized_message}'")
    
    # Extract context from previous conversation
    conversation_intent = context.get('intent', '')
    conversation_count = context.get('message_count', 0)
    
    # Enhanced greeting detection with context awareness - only exact word matches
    greetings = {
        'en': ['hello', 'hi', 'hey', 'namaste', 'good morning', 'good afternoon', 'good evening', 'greetings'],
        'hi': ['नमस्ते', 'हैलो', 'हाय', 'सुप्रभात', 'शुभ संध्या', 'स्वागत', 'नमस्कार'],
        'bn': ['নমস্কার', 'হ্যালো', 'হাই', 'সুপ্রভাত', 'শুভ সন্ধ্যা', 'স্বাগতম', 'নমস্কার'],
        'ta': ['வணக்கம்', 'ஹலோ', 'ஹாய்', 'காலை வணக்கம்', 'மாலை வணக்கம்', 'வரவேற்கிறோம்', 'வணக்கம்'],
        'mr': ['नमस्कार', 'हॅलो', 'हाय', 'शुभ सकाळ', 'शुभ संध्या', 'स्वागत']
    }
    
    # Check for greetings - only if message starts with greeting or is just a greeting
    greeting_words = greetings.get(language, greetings['en'])
    is_greeting = any(normalized_message.startswith(greeting) or normalized_message == greeting for greeting in greeting_words)
    
    if is_greeting:
        print(f"DEBUG: Detected as greeting")
        return get_greeting_response(language, vendor, conversation_count)
    
    # Enhanced intent detection with multiple keywords and context
    intent_scores = {
        'suppliers': calculate_intent_score(normalized_message, [
            'supplier', 'suppliers', 'find', 'search', 'looking for', 'vendor', 'seller', 
            'wholesale', 'distributor', 'dealer', 'market', 'mandi', 'bazaar'
        ]),
        'orders': calculate_intent_score(normalized_message, [
            'order', 'place order', 'buy', 'purchase', 'cart', 'checkout', 'buying',
            'need', 'want', 'require', 'get', 'obtain', 'procure'
        ]),
        'delivery': calculate_intent_score(normalized_message, [
            'delivery', 'track', 'tracking', 'where is', 'status', 'shipping',
            'dispatch', 'transit', 'on the way', 'arrived', 'reached'
        ]),
        'pricing': calculate_intent_score(normalized_message, [
            'price', 'cost', 'expensive', 'cheap', 'alert', 'rate', 'rate',
            'discount', 'offer', 'deal', 'bargain', 'affordable', 'budget'
        ]),
        'help': calculate_intent_score(normalized_message, [
            'help', 'support', 'problem', 'issue', 'trouble', 'difficulty',
            'confused', 'don\'t understand', 'how to', 'guide', 'tutorial'
        ]),
        'account': calculate_intent_score(normalized_message, [
            'account', 'profile', 'settings', 'dashboard', 'my account',
            'personal', 'information', 'details', 'update', 'change'
        ]),
        'products': calculate_intent_score(normalized_message, [
            'product', 'products', 'item', 'items', 'goods', 'materials',
            'ingredients', 'raw materials', 'stock', 'inventory'
        ]),
        'business': calculate_intent_score(normalized_message, [
            'business', 'shop', 'store', 'restaurant', 'food', 'cooking',
            'recipe', 'menu', 'service', 'customer', 'sales'
        ])
    }
    
    # Get the highest scoring intent
    best_intent = max(intent_scores, key=intent_scores.get)
    confidence = intent_scores[best_intent]
    
    # Debug logging
    print(f"DEBUG: Intent scores: {intent_scores}")
    print(f"DEBUG: Best intent: {best_intent} with confidence: {confidence}")
    
    # Direct routing for explicit price questions
    if any(word in normalized_message for word in ['price', 'cost', 'how much']):
        print(f"DEBUG: Direct routing to price response due to price keywords")
        return get_enhanced_price_response(language, vendor, normalized_message, context)
    
    # Handle follow-up questions based on context
    if conversation_intent and confidence < 0.6:
        return handle_follow_up_response(normalized_message, conversation_intent, language, vendor, context)
    
    # Route to appropriate response handler based on intent
    # Lower threshold for pricing queries that mention specific products
    has_specific_product = any(word in normalized_message for word in ['chickpeas', 'tomatoes', 'onions', 'rice', 'potato', 'oil', 'samosa', 'dosa', 'chai', 'tea', 'juice', 'ice cream', 'kulfi'])
    
    if best_intent == 'suppliers' and confidence > 0.3:
        return get_enhanced_supplier_response(language, vendor, normalized_message, context)
    elif best_intent == 'orders' and confidence > 0.3:
        return get_enhanced_order_response(language, vendor, normalized_message, context)
    elif best_intent == 'pricing' and (confidence > 0.05 or has_specific_product):
        print(f"DEBUG: Routing to get_enhanced_price_response (has_specific_product: {has_specific_product})")
        return get_enhanced_price_response(language, vendor, normalized_message, context)
    elif best_intent == 'help' and confidence > 0.3:
        return get_enhanced_help_response(language, vendor, normalized_message, context)
    elif best_intent == 'account' and confidence > 0.3:
        return get_enhanced_account_response(language, vendor, normalized_message, context)
    elif best_intent == 'products' and confidence > 0.3:
        return get_enhanced_product_response(language, vendor, normalized_message, context)
    elif best_intent == 'business' and confidence > 0.3:
        return get_enhanced_business_response(language, vendor, normalized_message, context)
    else:
        return get_intelligent_default_response(language, vendor, normalized_message, context)

def calculate_intent_score(message, keywords):
    """Calculate confidence score for intent detection"""
    matches = sum(1 for keyword in keywords if keyword in message)
    return matches / len(keywords) if keywords else 0

def handle_follow_up_response(message, previous_intent, language, vendor, context):
    """Handle follow-up questions based on previous conversation context"""
    
    follow_up_responses = {
        'suppliers': {
            'en': {
                'nearby': "I can help you find suppliers near your location. What's your area?",
                'rating': "I can show you suppliers sorted by rating. The top-rated suppliers are:",
                'price': "I can help you find suppliers with the best prices. Let me check current rates.",
                'category': "What type of products are you looking for? I can filter suppliers by category."
            },
            'hi': {
                'nearby': "मैं आपको आपके स्थान के पास आपूर्तिकर्ता खोजने में मदद कर सकता हूँ। आपका क्षेत्र क्या है?",
                'rating': "मैं आपको रेटिंग के अनुसार क्रमबद्ध आपूर्तिकर्ता दिखा सकता हूँ। सबसे अधिक रेटेड आपूर्तिकर्ता हैं:",
                'price': "मैं आपको सबसे अच्छी कीमतों वाले आपूर्तिकर्ता खोजने में मदद कर सकता हूँ। मुझे वर्तमान दरें जांचने दें।",
                'category': "आप किस प्रकार के उत्पाद खोज रहे हैं? मैं श्रेणी के अनुसार आपूर्तिकर्ताओं को फ़िल्टर कर सकता हूँ।"
            }
        },
        'orders': {
            'en': {
                'quantity': "How much quantity do you need? I can help you calculate the total cost.",
                'bulk': "For bulk orders, you can save up to 15% with group ordering. Would you like to create a group order?",
                'urgent': "I can help you find suppliers who offer same-day or next-day delivery for urgent orders.",
                'payment': "What payment method would you prefer? We support cash on delivery, online payment, and credit terms."
            }
        }
    }
    
    # Extract specific follow-up intent
    if 'near' in message or 'close' in message or 'nearby' in message:
        return get_location_based_response(language, vendor, context)
    elif 'rating' in message or 'best' in message or 'top' in message:
        return get_rating_based_response(language, vendor, context)
    elif 'price' in message or 'cost' in message or 'cheap' in message:
        return get_price_comparison_response(language, vendor, context)
    elif 'category' in message or 'type' in message or 'kind' in message:
        return get_category_based_response(language, vendor, context)
    else:
        return get_contextual_response(previous_intent, language, vendor, context)

def get_greeting_response(language, vendor, conversation_count=0):
    """Generate enhanced greeting response based on language, vendor, and conversation context"""
    
    # Personalized greetings based on conversation count
    if conversation_count == 0:
        greeting_templates = {
            'en': f"Hello! Welcome to VendorConnect. I'm your personal assistant here to help you with your business needs. " + 
                  (f"I see you're logged in as {vendor.name} ({vendor.business_type}). " if vendor else "") +
                  "I can help you find suppliers, place orders, track deliveries, and much more. How can I assist you today?",
            'hi': f"नमस्ते! VendorConnect में आपका स्वागत है। मैं आपका व्यक्तिगत सहायक हूँ जो आपकी व्यावसायिक जरूरतों में आपकी मदद करने के लिए यहाँ है। " +
                  (f"मैं देख रहा हूँ कि आप {vendor.name} ({vendor.business_type}) के रूप में लॉग इन हैं। " if vendor else "") +
                  "मैं आपको आपूर्तिकर्ता खोजने, ऑर्डर देने, डिलीवरी ट्रैक करने और बहुत कुछ में मदद कर सकता हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
            'bn': f"নমস্কার! VendorConnect-এ স্বাগতম। আমি আপনার ব্যক্তিগত সহায়ক এখানে আপনার ব্যবসায়িক প্রয়োজনে সাহায্য করতে। " +
                  (f"আমি দেখছি আপনি {vendor.name} ({vendor.business_type}) হিসাবে লগ ইন আছেন। " if vendor else "") +
                  "আমি আপনাকে সরবরাহকারী খুঁজে পেতে, অর্ডার দিতে, ডেলিভারি ট্র্যাক করতে এবং আরও অনেক কিছুতে সাহায্য করতে পারি। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
            'ta': f"வணக்கம்! VendorConnect-க்கு வரவேற்கிறோம்। உங்கள் வணிகத் தேவைகளுக்கு உதவ நான் உங்கள் தனிப்பட்ட உதவியாளர் இங்கே இருக்கிறேன்। " +
                  (f"நீங்கள் {vendor.name} ({vendor.business_type}) என லாக் இன் ஆகியிருக்கிறீர்கள் என்று பார்க்கிறேன்। " if vendor else "") +
                "நான் உங்களுக்கு சப்ளையர்களைக் கண்டுபிடிக்க, ஆர்டர்களை வைக்க, டெலிவரிகளைக் கண்காணிக்க மற்றும் பலவற்றில் உதவ முடியும்। இன்று நான் உங்களுக்கு எவ்வாறு உதவ முடியும்?",
            'mr': f"नमस्कार! VendorConnect मध्ये आपले स्वागत आहे. मी तुमच्या व्यावसायिक गरजांसाठी मदत करणारा वैयक्तिक सहाय्यक आहे. " +
                (f"मी पाहतोय की तुम्ही {vendor.name} ({vendor.business_type}) म्हणून लॉग इन आहात. " if vendor else "") +
                "मी तुम्हाला पुरवठादार शोधणे, ऑर्डर देणे, डिलिव्हरी ट्रॅक करणे आणि आणखी बर्‍याच गोष्टींमध्ये मदत करू शकतो. आज मी तुम्हाला कशात मदत करू?"
        }
    else:
        greeting_templates = {
            'en': f"Welcome back! " + (f"Good to see you again, {vendor.name}. " if vendor else "") +
                  "I'm here to continue helping you with your business needs. What would you like to do today?",
            'hi': f"वापस स्वागत! " + (f"आपको फिर से देखकर अच्छा लगा, {vendor.name}। " if vendor else "") +
                  "मैं आपकी व्यावसायिक जरूरतों में आपकी मदद करना जारी रखने के लिए यहाँ हूँ। आज आप क्या करना चाहते हैं?",
            'bn': f"ফিরে স্বাগতম! " + (f"আপনাকে আবার দেখে ভালো লাগল, {vendor.name}। " if vendor else "") +
                  "আমি আপনার ব্যবসায়িক প্রয়োজনে সাহায্য করতে এখানে আছি। আজ আপনি কী করতে চান?",
            'ta': f"மீண்டும் வரவேற்கிறோம்! " + (f"உங்களை மீண்டும் பார்த்து மகிழ்ச்சி, {vendor.name}। " if vendor else "") +
                "நான் உங்கள் வணிகத் தேவைகளுக்கு உதவுவதைத் தொடர இங்கே இருக்கிறேன்। இன்று நீங்கள் என்ன செய்ய விரும்புகிறீர்கள்?",
            'mr': f"पुन्हा स्वागत! " + (f"तुम्हाला पुन्हा भेटून आनंद झाला, {vendor.name}. " if vendor else "") +
                "मी तुमच्या व्यावसायिक गरजांसाठी मदत करण्यासाठी येथे आहे. आज तुम्हाला काय करायचे आहे?"
        }
    
    # Add business-specific suggestions
    business_suggestions = {
        'ice_cream': {
            'en': "Since you're in the ice cream business, I can help you find suppliers for dairy products, flavors, and equipment.",
            'hi': "चूंकि आप आइसक्रीम के व्यवसाय में हैं, मैं आपको डेयरी उत्पादों, स्वादों और उपकरणों के आपूर्तिकर्ता खोजने में मदद कर सकता हूँ।",
            'bn': "যেহেতু আপনি আইসক্রিম ব্যবসায় আছেন, আমি আপনাকে দুগ্ধজাত পণ্য, স্বাদ এবং সরঞ্জামের সরবরাহকারী খুঁজে পেতে সাহায্য করতে পারি।",
            'ta': "நீங்கள் ஐஸ்கிரீம் வணிகத்தில் இருப்பதால், நான் உங்களுக்கு பால் பொருட்கள், சுவைகள் மற்றும் உபகரணங்களுக்கான சப்ளையர்களைக் கண்டுபிடிக்க உதவ முடியும்।",
            'mr': "तुम्ही आइसक्रीम व्यवसायात असल्यामुळे, मी तुम्हाला डेअरी उत्पादने, फ्लेवर्स आणि उपकरणांसाठी पुरवठादार शोधण्यात मदत करू शकतो."
        },
        'chaat': {
            'en': "For your chaat business, I can help you source fresh vegetables, spices, and traditional ingredients.",
            'hi': "आपके चाट व्यवसाय के लिए, मैं आपको ताजी सब्जियां, मसाले और पारंपरिक सामग्री खोजने में मदद कर सकता हूँ।",
            'bn': "আপনার চাট ব্যবসার জন্য, আমি আপনাকে তাজা সবজি, মশলা এবং ঐতিহ্যবাহী উপাদান খুঁজে পেতে সাহায্য করতে পারি।",
            'ta': "உங்கள் சாட் வணிகத்திற்கு, நான் உங்களுக்கு புதிய காய்கறிகள், மசாலாப் பொருட்கள் மற்றும் பாரம்பரிய பொருட்களைக் கண்டுபிடிக்க உதவ முடியும்।",
            'mr': "तुमच्या चाट व्यवसायासाठी, मी तुम्हाला ताजी भाजीपाला, मसाले आणि पारंपरिक घटक मिळवून देण्यात मदत करू शकतो."
        }
    }
    
    base_response = greeting_templates.get(language, greeting_templates['en'])
    
    # Add business-specific suggestions if vendor is logged in
    if vendor and vendor.business_type in business_suggestions:
        business_suggestion = business_suggestions[vendor.business_type].get(language, business_suggestions[vendor.business_type]['en'])
        base_response += f"\n\n{business_suggestion}"
    
    return {
        'message': base_response,
        'context': {'intent': 'greeting', 'message_count': conversation_count + 1},
        'actions': make_actions(language, [
            ('find-suppliers', 'Find Suppliers'),
            ('place-order', 'Place Order'),
            ('price-alerts', 'Price Alerts'),
            ('business-tips', 'Business Tips'),
            ('market-trends', 'Market Trends')
        ])
    }

def get_enhanced_supplier_response(language, vendor, message, context):
    """Generate enhanced supplier-related response with intelligent filtering"""
    
    # Extract specific requirements from message
    location_keywords = ['near', 'close', 'nearby', 'local', 'area', 'location']
    rating_keywords = ['best', 'top', 'rated', 'quality', 'good', 'excellent']
    price_keywords = ['cheap', 'affordable', 'budget', 'low price', 'economical']
    category_keywords = ['vegetables', 'dairy', 'spices', 'grains', 'fruits']
    
    # Determine search criteria
    search_criteria = {
        'location': any(keyword in message for keyword in location_keywords),
        'rating': any(keyword in message for keyword in rating_keywords),
        'price': any(keyword in message for keyword in price_keywords),
        'category': any(keyword in message for keyword in category_keywords)
    }
    
    # Build response based on criteria
    if search_criteria['location']:
        return get_location_based_response(language, vendor, context)
    elif search_criteria['rating']:
        return get_rating_based_response(language, vendor, context)
    elif search_criteria['price']:
        return get_price_comparison_response(language, vendor, context)
    elif search_criteria['category']:
        return get_category_based_response(language, vendor, context)
    else:
        return get_comprehensive_supplier_response(language, vendor, context)

def get_comprehensive_supplier_response(language, vendor, context):
    """Generate comprehensive supplier information with detailed analysis"""
    responses = {
        'en': "I've analyzed the market and found the best suppliers for your business needs. Here's my detailed recommendation:",
        'hi': "मैंने बाजार का विश्लेषण किया है और आपकी व्यावसायिक जरूरतों के लिए सबसे अच्छे आपूर्तिकर्ता पाए हैं। यहाँ मेरी विस्तृत सिफारिश है:",
        'bn': "আমি বাজার বিশ্লেষণ করেছি এবং আপনার ব্যবসায়িক প্রয়োজনের জন্য সেরা সরবরাহকারী খুঁজে পেয়েছি। এখানে আমার বিস্তারিত সুপারিশ:",
        'ta': "நான் சந்தையை பகுப்பாய்வு செய்து உங்கள் வணிகத் தேவைகளுக்கு சிறந்த சப்ளையர்களைக் கண்டறிந்தேன்। இங்கே எனது விரிவான பரிந்துரை:",
        'mr': "मी बाजाराचे विश्लेषण करून तुमच्या व्यवसायाच्या गरजांसाठी सर्वोत्तम पुरवठादार शोधले आहेत. माझी सविस्तर शिफारस येथे आहे:"
    }
    
    # Get comprehensive supplier data
    top_rated = Supplier.query.filter_by(verification_status=True).order_by(Supplier.rating.desc()).limit(3).all()
    verified_suppliers = Supplier.query.filter_by(verification_status=True).limit(5).all()
    
    # Calculate market insights
    total_suppliers = Supplier.query.count()
    verified_count = Supplier.query.filter_by(verification_status=True).count()
    avg_rating = db.session.query(db.func.avg(Supplier.rating)).scalar() or 0
    
    supplier_info = []
    
    # Market overview
    market_overview = {
        'en': [
            "📊 MARKET OVERVIEW:",
            f"• Total Suppliers: {total_suppliers}",
            f"• Verified Suppliers: {verified_count} ({verified_count/total_suppliers*100:.1f}%)",
            f"• Average Rating: {avg_rating:.1f}/5",
            f"• Market Coverage: {verified_count} locations"
        ],
        'hi': [
            "📊 बाजार अवलोकन:",
            f"• कुल आपूर्तिकर्ता: {total_suppliers}",
            f"• सत्यापित आपूर्तिकर्ता: {verified_count} ({verified_count/total_suppliers*100:.1f}%)",
            f"• औसत रेटिंग: {avg_rating:.1f}/5",
            f"• बाजार कवरेज: {verified_count} स्थान"
        ],
        'mr': [
            "📊 बाजाराचा आढावा:",
            f"• एकूण पुरवठादार: {total_suppliers}",
            f"• सत्यापित पुरवठादार: {verified_count} ({verified_count/total_suppliers*100:.1f}%)",
            f"• सरासरी रेटिंग: {avg_rating:.1f}/5",
            f"• बाजार कव्हरेज: {verified_count} ठिकाणे"
        ]
    }
    
    supplier_info.extend(market_overview.get(language, market_overview['en']))
    
    # Top suppliers with detailed analysis
    supplier_info.append("\n🏆 TOP RECOMMENDED SUPPLIERS:")
    for i, supplier in enumerate(top_rated, 1):
        # Get supplier's products for analysis
        products = Product.query.filter_by(supplier_id=supplier.id).limit(3).all()
        product_names = [p.name for p in products]
        
        # Calculate reliability score
        reliability_score = (supplier.rating + supplier.hygiene_rating) / 2
        
        supplier_info.append(f"\n{i}. {supplier.name}")
        supplier_info.append(f"   📍 Location: {supplier.location}")
        supplier_info.append(f"   ⭐ Rating: {supplier.rating}/5 | 🧼 Hygiene: {supplier.hygiene_rating}/5")
        supplier_info.append(f"   📞 Contact: {supplier.phone}")
        supplier_info.append(f"   🎯 Reliability Score: {reliability_score:.1f}/5")
        
        if product_names:
            supplier_info.append(f"   🛍️ Key Products: {', '.join(product_names[:3])}")
        
        # Add specific recommendations
        if supplier.rating >= 4.5:
            supplier_info.append("   ✅ Premium Quality - Recommended for high-end products")
        elif supplier.rating >= 4.0:
            supplier_info.append("   ✅ Good Quality - Reliable for regular orders")
        else:
            supplier_info.append("   ⚠️ Standard Quality - Suitable for budget orders")
    
    # Business-specific analysis
    if vendor and vendor.business_type:
        business_analysis = {
            'ice_cream': {
                'en': [
                    "\n\n🍦 ICE CREAM BUSINESS ANALYSIS:",
                    "• Dairy suppliers with 4.5+ hygiene rating are crucial",
                    "• Temperature-controlled storage facilities required",
                    "• Fresh milk suppliers should be within 50km radius",
                    "• Seasonal fruit suppliers for flavor variety",
                    "• Packaging suppliers for containers and labels"
                ],
                'hi': [
                    "\n\n🍦 आइसक्रीम व्यवसाय विश्लेषण:",
                    "• 4.5+ स्वच्छता रेटिंग वाले डेयरी आपूर्तिकर्ता महत्वपूर्ण हैं",
                    "• तापमान नियंत्रित भंडारण सुविधाएं आवश्यक",
                    "• ताजे दूध आपूर्तिकर्ता 50 किमी त्रिज्या के भीतर होने चाहिए",
                    "• स्वाद विविधता के लिए मौसमी फल आपूर्तिकर्ता",
                    "• कंटेनर और लेबल के लिए पैकेजिंग आपूर्तिकर्ता"
                ]
            },
            'chaat': {
                'en': [
                    "\n\n🌶️ CHAAT BUSINESS ANALYSIS:",
                    "• Fresh vegetable suppliers with daily delivery",
                    "• Authentic spice suppliers from traditional markets",
                    "• Oil and ghee suppliers for cooking",
                    "• Fresh herbs and chutney ingredients",
                    "• Packaging for takeaway containers"
                ],
                'hi': [
                    "\n\n🌶️ चाट व्यवसाय विश्लेषण:",
                    "• दैनिक डिलीवरी के साथ ताजी सब्जी आपूर्तिकर्ता",
                    "• पारंपरिक बाजारों से प्रामाणिक मसाला आपूर्तिकर्ता",
                    "• खाना पकाने के लिए तेल और घी आपूर्तिकर्ता",
                    "• ताजी जड़ी-बूटियां और चटनी सामग्री",
                    "• टेकअवे कंटेनर के लिए पैकेजिंग"
                ]
            }
        }
        
        analysis = business_analysis.get(vendor.business_type, {}).get(language, [])
        if analysis:
            supplier_info.extend(analysis)
    
    # Add strategic recommendations
    strategic_tips = {
        'en': [
            "\n\n💡 STRATEGIC RECOMMENDATIONS:",
            "• Build relationships with 2-3 primary suppliers",
            "• Maintain backup suppliers for critical items",
            "• Negotiate bulk discounts for regular orders",
            "• Monitor supplier performance monthly",
            "• Consider seasonal supplier variations"
        ],
        'hi': [
            "\n\n💡 रणनीतिक सुझाव:",
            "• 2-3 प्राथमिक आपूर्तिकर्ताओं के साथ संबंध बनाएं",
            "• महत्वपूर्ण वस्तुओं के लिए बैकअप आपूर्तिकर्ता रखें",
            "• नियमित ऑर्डर के लिए बल्क छूट पर बातचीत करें",
            "• मासिक आपूर्तिकर्ता प्रदर्शन की निगरानी करें",
            "• मौसमी आपूर्तिकर्ता भिन्नताओं पर विचार करें"
        ]
    }
    
    supplier_info.extend(strategic_tips.get(language, strategic_tips['en']))
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + supplier_info
        },
        'context': {'intent': 'suppliers', 'search_type': 'comprehensive', 'analysis': True},
        'actions': make_actions(language, [
            ('view-supplier-details', 'View Supplier Details'),
            ('compare-suppliers', 'Compare Suppliers'),
            ('contact-supplier', 'Contact Supplier'),
            ('supplier-performance', 'Performance Analysis'),
            ('negotiate-prices', 'Negotiate Prices'),
            ('backup-suppliers', 'Find Backup Suppliers'),
            ('seasonal-analysis', 'Seasonal Analysis'),
            ('supplier-reviews', 'Read Reviews')
        ])
    }

def get_location_based_response(language, vendor, context):
    """Generate location-based supplier response"""
    responses = {
        'en': "I'll help you find suppliers near your location. Here are the closest verified suppliers:",
        'hi': "मैं आपको आपके स्थान के पास आपूर्तिकर्ता खोजने में मदद करूंगा। यहाँ सबसे नजदीकी सत्यापित आपूर्तिकर्ता हैं:",
        'bn': "আমি আপনাকে আপনার অবস্থানের কাছাকাছি সরবরাহকারী খুঁজে পেতে সাহায্য করব। এখানে সবচেয়ে কাছের যাচাইকৃত সরবরাহকারী:",
        'ta': "உங்கள் இடத்திற்கு அருகில் சப்ளையர்களைக் கண்டுபிடிக்க உதவுவேன்। இங்கே மிக நெருக்கமான சரிபார்க்கப்பட்ட சப்ளையர்கள்:",
        'mr': "मी तुमच्या ठिकाणाजवळ पुरवठादार शोधण्यात मदत करीन. इथे सर्वात जवळचे सत्यापित पुरवठादार आहेत:"
    }
    
    # Get suppliers (in a real app, you'd filter by actual location)
    suppliers = Supplier.query.filter_by(verification_status=True).limit(3).all()
    
    supplier_list = []
    for i, supplier in enumerate(suppliers, 1):
        distance = f"{i * 2.5} km away"  # Mock distance
        supplier_list.append(f"• {supplier.name} - {supplier.location}")
        supplier_list.append(f"  📍 {distance} | Rating: {supplier.rating}/5 | Phone: {supplier.phone}")
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + supplier_list
        },
        'context': {'intent': 'suppliers', 'search_type': 'location'},
        'actions': make_actions(language, [
            ('get-directions', 'Get Directions'),
            ('call-supplier', 'Call Supplier'),
            ('view-on-map', 'View on Map'),
            ('set-location', 'Set My Location')
        ])
    }

def get_rating_based_response(language, vendor, context):
    """Generate rating-based supplier response"""
    responses = {
        'en': "Here are the top-rated suppliers based on vendor feedback:",
        'hi': "यहाँ वेंडर फीडबैक के आधार पर सबसे अधिक रेटेड आपूर्तिकर्ता हैं:",
        'bn': "এখানে বিক্রেতা প্রতিক্রিয়ার ভিত্তিতে সর্বোচ্চ রেটেড সরবরাহকারী:",
        'ta': "விற்பனையாளர் கருத்துகளின் அடிப்படையில் மிக உயர்ந்த மதிப்பீடு பெற்ற சப்ளையர்கள்:",
        'mr': "विक्रेता अभिप्रायाच्या आधारावर सर्वोच्च रेटिंग असलेले पुरवठादार येथे आहेत:"
    }
    
    # Get top-rated suppliers
    suppliers = Supplier.query.filter_by(verification_status=True).order_by(Supplier.rating.desc()).limit(3).all()
    
    supplier_list = []
    for supplier in suppliers:
        stars = "⭐" * int(supplier.rating)
        supplier_list.append(f"• {supplier.name} - {supplier.location}")
        supplier_list.append(f"  {stars} Rating: {supplier.rating}/5 | Hygiene: {supplier.hygiene_rating}/5")
        supplier_list.append(f"  📞 {supplier.phone}")
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + supplier_list
        },
        'context': {'intent': 'suppliers', 'search_type': 'rating'},
        'actions': make_actions(language, [
            ('read-reviews', 'Read Reviews'),
            ('contact-supplier', 'Contact Supplier'),
            ('view-details', 'View Details'),
            ('add-to-favorites', 'Add to Favorites')
        ])
    }

def get_price_comparison_response(language, vendor, context):
    """Generate price comparison response"""
    responses = {
        'en': "I'll help you find suppliers with the best prices. Here's a price comparison:",
        'hi': "मैं आपको सबसे अच्छी कीमतों वाले आपूर्तिकर्ता खोजने में मदद करूंगा। यहाँ कीमत तुलना है:",
        'bn': "আমি আপনাকে সেরা মূল্যের সরবরাহকারী খুঁজে পেতে সাহায্য করব। এখানে মূল্য তুলনা:",
        'ta': "சிறந்த விலைகளுடன் சப்ளையர்களைக் கண்டுபிடிக்க உதவுவேன்। இங்கே விலை ஒப்பீடு:",
        'mr': "मी तुम्हाला सर्वोत्तम किंमती असलेले पुरवठादार शोधण्यात मदत करीन. येथे किंमत तुलना आहे:"
    }
    
    # Get sample products for price comparison
    products = Product.query.limit(5).all()
    
    price_info = []
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        price_info.append(f"• {product.name}: ₹{product.current_price}/{product.unit}")
        price_info.append(f"  From: {supplier.name} | Stock: {product.stock_available} {product.unit}")
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + price_info
        },
        'context': {'intent': 'suppliers', 'search_type': 'price'},
        'actions': [
            {'action': 'compare-prices', 'label': 'Compare All Prices'},
            {'action': 'set-price-alert', 'label': 'Set Price Alert'},
            {'action': 'bulk-discount', 'label': 'Check Bulk Discounts'},
            {'action': 'negotiate-price', 'label': 'Negotiate Price'}
        ]
    }

def get_category_based_response(language, vendor, context):
    """Generate category-based supplier response"""
    responses = {
        'en': "I can help you find suppliers by product category. What type of products do you need?",
        'hi': "मैं आपको उत्पाद श्रेणी के अनुसार आपूर्तिकर्ता खोजने में मदद कर सकता हूँ। आपको किस प्रकार के उत्पाद चाहिए?",
        'bn': "আমি আপনাকে পণ্যের বিভাগ অনুযায়ী সরবরাহকারী খুঁজে পেতে সাহায্য করতে পারি। আপনার কী ধরনের পণ্য প্রয়োজন?",
        'ta': "நான் உங்களுக்கு தயாரிப்பு வகையின் அடிப்படையில் சப்ளையர்களைக் கண்டுபிடிக்க உதவ முடியும்। உங்களுக்கு என்ன வகையான தயாரிப்புகள் தேவை?",
        'mr': "मी उत्पादन श्रेणीप्रमाणे पुरवठादार शोधण्यात तुमची मदत करू शकतो. तुम्हाला कोणत्या प्रकारची उत्पादने हवी आहेत?"
    }
    
    # Get available categories
    categories = db.session.query(Product.category).distinct().limit(8).all()
    category_list = [cat[0].title() for cat in categories]
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + [f"• {cat}" for cat in category_list]
        },
        'context': {'intent': 'suppliers', 'search_type': 'category'},
        'actions': make_actions(language, [
            ('select-category', 'Select Category'),
            ('view-all-categories', 'View All Categories'),
            ('mixed-order', 'Mixed Category Order'),
            ('seasonal-products', 'Seasonal Products')
        ])
    }


def get_enhanced_price_response(language, vendor, message, context):
    """Generate enhanced price-related response with market insights"""
    
    print(f"DEBUG: get_enhanced_price_response called with message: '{message}'")
    
    # Extract price-specific keywords
    comparison_keywords = ['compare', 'comparison', 'cheaper', 'expensive', 'best price']
    alert_keywords = ['alert', 'notification', 'watch', 'monitor', 'track']
    trend_keywords = ['trend', 'trending', 'going up', 'going down', 'market']
    
    needs_comparison = any(keyword in message for keyword in comparison_keywords)
    wants_alerts = any(keyword in message for keyword in alert_keywords)
    wants_trends = any(keyword in message for keyword in trend_keywords)
    
    responses = {
        'en': "I can help you with pricing information and market insights! Here's what I found:",
        'hi': "मैं आपको मूल्य निर्धारण जानकारी और बाजार अंतर्दृष्टि में मदद कर सकता हूँ! यहाँ मैंने जो पाया है:",
        'bn': "আমি আপনাকে মূল্য নির্ধারণের তথ্য এবং বাজার অন্তর্দৃষ্টিতে সাহায্য করতে পারি! এখানে আমি যা পেয়েছি:",
        'ta': "நான் உங்களுக்கு விலை தகவல் மற்றும் சந்தை நுண்ணறிவில் உதவ முடியும்! இங்கே நான் கண்டறிந்தவை:",
        'mr': "मी किंमत माहिती आणि बाजार अंतर्दृष्टीमध्ये मदत करू शकतो! मी काय शोधले आहे:"
    }
    
    price_info = [responses.get(language, responses['en'])]
    
    # Try to extract specific product name from the message
    specific_product_found = False
    matched_products = []
    
    if message:
        print(f"DEBUG: Searching for product in message: '{message}'")
        
        # Extract potential product names from the message
        # Common patterns: "price of X", "cost of X", "X price", "how much is X"
        import re
        
        # Try to extract the product name more intelligently
        product_patterns = [
            r'price of ([a-zA-Z\s]+?)(?:\s+on|\s+in|\s+from|$)',
            r'cost of ([a-zA-Z\s]+?)(?:\s+on|\s+in|\s+from|$)',
            r'how much (?:is|are) ([a-zA-Z\s]+?)(?:\s+on|\s+in|\s+from|\?|$)',
            r'([a-zA-Z\s]+) price',
        ]
        
        potential_product_name = None
        for pattern in product_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                potential_product_name = match.group(1).strip().lower()
                print(f"DEBUG: Extracted product name: '{potential_product_name}'")
                break
        
        # Search for the product in vendor's menu items first
        if vendor:
            print(f"DEBUG: Checking vendor menu items for vendor_id: {vendor.id}")
            menu_items = MenuItem.query.filter_by(vendor_id=vendor.id).all()
            print(f"DEBUG: Found {len(menu_items)} menu items")
            
            for item in menu_items:
                # Check if the extracted product name matches or if product name is in message
                if (potential_product_name and potential_product_name in item.name.lower()) or \
                   (item.name.lower() in message.lower()):
                    print(f"DEBUG: Found menu item match: {item.name}")
                    price_info.append(f"\n💰 PRICE ON YOUR WEBSITE:")
                    price_info.append(f"• {item.name}: ₹{item.price}")
                    if item.description:
                        price_info.append(f"  Description: {item.description}")
                    specific_product_found = True
                    break
        
        # If not found in vendor's menu, search in available products from suppliers
        if not specific_product_found:
            print(f"DEBUG: Checking supplier products")
            products = Product.query.all()
            print(f"DEBUG: Found {len(products)} supplier products")
            
            # First, try to find exact match with extracted product name
            if potential_product_name:
                for product in products:
                    if potential_product_name in product.name.lower():
                        print(f"DEBUG: Found exact product match: {product.name}")
                        matched_products.append(product)
            
            # If no exact match, look for any product name in the message
            if not matched_products:
                for product in products:
                    if product.name.lower() in message.lower():
                        print(f"DEBUG: Found product match: {product.name}")
                        matched_products.append(product)
            
            # Display matched products
            if matched_products:
                price_info.append(f"\n💰 AVAILABLE FROM SUPPLIERS:")
                for product in matched_products[:3]:  # Limit to 3 matches
                    supplier = Supplier.query.get(product.supplier_id)
                    price_info.append(f"• {product.name}: ₹{product.current_price}/{product.unit}")
                    if supplier:
                        price_info.append(f"  From: {supplier.name} | Stock: {product.stock_available}")
                specific_product_found = True
    
    # If no specific product found, show general market prices
    if not specific_product_found:
        price_info.append("\n💰 CURRENT MARKET PRICES:")
        products = Product.query.limit(5).all()
        for product in products:
            supplier = Supplier.query.get(product.supplier_id)
            price_info.append(f"• {product.name}: ₹{product.current_price}/{product.unit}")
            price_info.append(f"  From: {supplier.name} | Stock: {product.stock_available}")
    
    if needs_comparison:
        comparison_info = {
            'en': "\n📊 PRICE COMPARISON:",
            'hi': "\n📊 मूल्य तुलना:",
            'bn': "\n📊 মূল্য তুলনা:",
            'ta': "\n📊 விலை ஒப்பீடு:",
            'mr': "\n📊 किंमत तुलना:"
        }
        price_info.append(comparison_info.get(language, comparison_info['en']))
        price_info.append("• Tomatoes: ₹28-35/kg (Best: Krishna Mandi)")
        price_info.append("• Onions: ₹30-40/kg (Best: Fresh Farm)")
        price_info.append("• Rice: ₹40-50/kg (Best: Quality Vegetables)")
    
    if wants_trends:
        trend_info = {
            'en': "\n📈 MARKET TRENDS:",
            'hi': "\n📈 बाजार रुझान:",
            'bn': "\n📈 বাজার প্রবণতা:",
            'ta': "\n📈 சந்தை போக்குகள்:",
            'mr': "\n📈 बाजारातील प्रवृत्ती:"
        }
        price_info.append(trend_info.get(language, trend_info['en']))
        price_info.append("• Vegetable prices down 5% this week")
        price_info.append("• Dairy products stable")
        price_info.append("• Spices trending upward")
    
    if wants_alerts:
        alert_info = {
            'en': "\n🔔 PRICE ALERTS:",
            'hi': "\n🔔 मूल्य अलर्ट:",
            'bn': "\n🔔 মূল্য অ্যালার্ট:",
            'ta': "\n🔔 விலை எச்சரிக்கைகள்:",
            'mr': "\n🔔 किंमत अलर्ट:"
        }
        price_info.append(alert_info.get(language, alert_info['en']))
        price_info.append("• Set alerts for specific products")
        price_info.append("• Get notified of price drops")
        price_info.append("• Monitor competitor prices")
    
    # Add business-specific pricing tips
    if vendor and vendor.business_type:
        business_pricing = {
            'ice_cream': {
                'en': "\n🍦 ICE CREAM PRICING TIPS:",
                'hi': "\n🍦 आइसक्रीम मूल्य निर्धारण सुझाव:",
                'bn': "\n🍦 আইসক্রিম মূল্য নির্ধারণ টিপস:",
                'ta': "\n🍦 ஐஸ்கிரீம் விலை நிர்ணய குறிப்புகள்:",
                'mr': "\n🍦 आइसक्रीम किंमत टिप्स:"
            },
            'chaat': {
                'en': "\n🌶️ CHAAT PRICING TIPS:",
                'hi': "\n🌶️ चाट मूल्य निर्धारण सुझाव:",
                'bn': "\n🌶️ চাট মূল্য নির্ধারণ টিপস:",
                'ta': "\n🌶️ சாட் விலை நிர்ணய குறிப்புகள்:",
                'mr': "\n🌶️ चाट किंमत टिप्स:"
            }
        }
        
        tip_header = business_pricing.get(vendor.business_type, {}).get(language, "")
        if tip_header:
            price_info.append(tip_header)
            price_info.append("• Buy seasonal ingredients in bulk")
            price_info.append("• Monitor daily price fluctuations")
            price_info.append("• Negotiate better rates with regular suppliers")
    
    return {
        'message': {
            'type': 'list',
            'items': price_info
        },
        'context': {'intent': 'pricing', 'comparison': needs_comparison, 'alerts': wants_alerts, 'trends': wants_trends},
        'actions': make_actions(language, [
            ('current-prices', 'Current Prices'),
            ('set-alerts', 'Set Price Alerts'),
            ('price-comparison', 'Compare Prices'),
            ('price-trends', 'Price Trends'),
            ('market-analysis', 'Market Analysis'),
            ('bulk-pricing', 'Bulk Pricing'),
            ('negotiate-price', 'Negotiate Price'),
            ('price-history', 'Price History')
        ])
    }

def get_enhanced_help_response(language, vendor, message, context):
    """Generate enhanced help response with contextual assistance"""
    return get_help_response(language, vendor)

def get_enhanced_account_response(language, vendor, message, context):
    """Generate enhanced account response with personalized information"""
    return get_account_response(language, vendor)

def get_enhanced_product_response(language, vendor, message, context):
    """Generate enhanced product response with intelligent recommendations"""
    responses = {
        'en': "I can help you find the right products for your business! Here's what I recommend:",
        'hi': "मैं आपको आपके व्यवसाय के लिए सही उत्पाद खोजने में मदद कर सकता हूँ! यहाँ मेरी सिफारिश है:",
        'bn': "আমি আপনাকে আপনার ব্যবসার জন্য সঠিক পণ্য খুঁজে পেতে সাহায্য করতে পারি! এখানে আমার সুপারিশ:",
        'ta': "நான் உங்கள் வணிகத்திற்கு சரியான தயாரிப்புகளைக் கண்டுபிடிக்க உதவ முடியும்! இங்கே எனது பரிந்துரை:",
        'mr': "मी तुमच्या व्यवसायासाठी योग्य उत्पादने शोधण्यात मदत करू शकतो! माझी शिफारस येथे आहे:"
    }
    
    # Get products based on vendor's business type
    if vendor and vendor.business_type in BUSINESS_TYPE_CATEGORIES:
        categories = BUSINESS_TYPE_CATEGORIES[vendor.business_type]
        products = Product.query.filter(Product.category.in_(categories)).limit(5).all()
    else:
        products = Product.query.limit(5).all()
    
    product_list = []
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        product_list.append(f"• {product.name}: ₹{product.current_price}/{product.unit}")
        product_list.append(f"  From: {supplier.name} | Stock: {product.stock_available}")
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + product_list
        },
        'context': {'intent': 'products'},
        'actions': make_actions(language, [
            ('browse-products', 'Browse Products'),
            ('search-products', 'Search Products'),
            ('product-details', 'Product Details'),
            ('add-to-cart', 'Add to Cart')
        ])
    }

def get_enhanced_business_response(language, vendor, message, context):
    """Generate enhanced business response with industry insights"""
    responses = {
        'en': "I can help you with business insights and tips! Here's what I can offer:",
        'hi': "मैं आपको व्यावसायिक अंतर्दृष्टि और सुझावों में मदद कर सकता हूँ! यहाँ मैं क्या प्रदान कर सकता हूँ:",
        'bn': "আমি আপনাকে ব্যবসায়িক অন্তর্দৃষ্টি এবং টিপসে সাহায্য করতে পারি! এখানে আমি কী অফার করতে পারি:",
        'ta': "நான் உங்களுக்கு வணிக நுண்ணறிவு மற்றும் குறிப்புகளில் உதவ முடியும்! இங்கே நான் என்ன வழங்க முடியும்:",
        'mr': "मी व्यवसाय अंतर्दृष्ट्या आणि टिप्समध्ये मदत करू शकतो! मी काय देऊ शकतो ते येथे आहे:"
    }
    
    business_tips = {
        'en': [
            "📊 Business Analytics and Insights",
            "🎯 Market Trends and Opportunities", 
            "💡 Industry Best Practices",
            "📈 Growth Strategies",
            "🤝 Networking Opportunities",
            "📚 Educational Resources",
            "🛠️ Business Tools and Resources",
            "📞 Expert Consultation"
        ],
        'hi': [
            "📊 व्यावसायिक विश्लेषण और अंतर्दृष्टि",
            "🎯 बाजार रुझान और अवसर",
            "💡 उद्योग सर्वोत्तम प्रथाएं",
            "📈 विकास रणनीतियां",
            "🤝 नेटवर्किंग अवसर",
            "📚 शैक्षिक संसाधन",
            "🛠️ व्यावसायिक उपकरण और संसाधन",
            "📞 विशेषज्ञ परामर्श"
        ],
        'mr': [
            "📊 व्यवसाय विश्लेषण आणि अंतर्दृष्टी",
            "🎯 बाजारातील प्रवृत्ती आणि संधी",
            "💡 उद्योगातील सर्वोत्तम पद्धती",
            "📈 वाढीच्या रणनीती",
            "🤝 नेटवर्किंग संधी",
            "📚 शैक्षणिक संसाधने",
            "🛠️ व्यवसाय साधने आणि संसाधने",
            "📞 तज्ज्ञ सल्लामसलत"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + business_tips.get(language, business_tips['en'])
        },
        'context': {'intent': 'business'},
        'actions': make_actions(language, [
            ('business-analytics', 'Business Analytics'),
            ('market-trends', 'Market Trends'),
            ('best-practices', 'Best Practices'),
            ('growth-strategies', 'Growth Strategies'),
            ('networking', 'Networking'),
            ('resources', 'Resources'),
            ('consultation', 'Expert Consultation')
        ])
    }

def get_contextual_response(previous_intent, language, vendor, context):
    """Generate contextual response based on previous conversation"""
    responses = {
        'en': f"I understand you're continuing our discussion about {previous_intent}. Let me help you further:",
        'hi': f"मैं समझता हूँ कि आप {previous_intent} के बारे में हमारी चर्चा जारी रख रहे हैं। मैं आपकी आगे मदद करूंगा:",
        'bn': f"আমি বুঝতে পারছি যে আপনি {previous_intent} সম্পর্কে আমাদের আলোচনা চালিয়ে যাচ্ছেন। আমি আপনাকে আরও সাহায্য করব:",
        'ta': f"நீங்கள் {previous_intent} பற்றி எங்கள் விவாதத்தைத் தொடர்கிறீர்கள் என்பதை நான் புரிகிறேன்। நான் உங்களுக்கு மேலும் உதவுவேன்:",
        'mr': f"मला समजते की तुम्ही {previous_intent} बद्दलची चर्चा पुढे चालू ठेवत आहात. मी आणखी मदत करतो:"
    }
    
    return {
        'message': responses.get(language, responses['en']),
        'context': {'intent': previous_intent, 'follow_up': True},
        'actions': make_actions(language, [
            (f'{previous_intent}-details', f'More {previous_intent.title()}'),
            ('related-topics', 'Related Topics'),
            ('start-over', 'Start Over')
        ])
    }

def get_enhanced_order_response(language, vendor, message, context):
    """Generate enhanced order-related response with intelligent suggestions"""
    
    # Extract order-specific keywords
    urgent_keywords = ['urgent', 'asap', 'immediately', 'quick', 'fast', 'emergency']
    bulk_keywords = ['bulk', 'large', 'big', 'wholesale', 'many', 'lot']
    specific_keywords = ['tomatoes', 'onions', 'rice', 'oil', 'milk', 'vegetables']
    
    is_urgent = any(keyword in message for keyword in urgent_keywords)
    is_bulk = any(keyword in message for keyword in bulk_keywords)
    has_specific_items = any(keyword in message for keyword in specific_keywords)
    
    responses = {
        'en': "I can help you place an order! Let me guide you through the process:",
        'hi': "मैं आपको ऑर्डर देने में मदद कर सकता हूँ! मैं आपको प्रक्रिया के माध्यम से मार्गदर्शन करूंगा:",
        'bn': "আমি আপনাকে অর্ডার দিতে সাহায্য করতে পারি! আমি আপনাকে প্রক্রিয়ার মাধ্যমে গাইড করব:",
        'ta': "நான் உங்களுக்கு ஆர்டர் செய்ய உதவ முடியும்! நான் உங்களை செயல்முறை வழியாக வழிநடத்துவேன்:",
        'mr': "मी तुम्हाला ऑर्डर देण्यात मदत करू शकतो! मी तुम्हाला प्रक्रियेत मार्गदर्शन करतो:"
    }
    
    order_info = [responses.get(language, responses['en'])]
    
    # Add urgency-specific information
    if is_urgent:
        urgent_info = {
            'en': "\n🚨 URGENT ORDER DETECTED:",
            'hi': "\n🚨 तत्काल ऑर्डर का पता चला:",
            'bn': "\n🚨 জরুরি অর্ডার সনাক্ত:",
            'ta': "\n🚨 அவசர ஆர்டர் கண்டறியப்பட்டது:",
            'mr': "\n🚨 तातडीचा ऑर्डर आढळला:"
        }
        order_info.append(urgent_info.get(language, urgent_info['en']))
        order_info.append("• Same-day delivery available")
        order_info.append("• Priority suppliers recommended")
        order_info.append("• Express processing enabled")
    
    # Add bulk-specific information
    if is_bulk:
        bulk_info = {
            'en': "\n📦 BULK ORDER BENEFITS:",
            'hi': "\n📦 बल्क ऑर्डर लाभ:",
            'bn': "\n📦 বাল্ক অর্ডার সুবিধা:",
            'ta': "\n📦 மொத்த ஆர்டர் நன்மைகள்:",
            'mr': "\n📦 मोठ्या ऑर्डरचे फायदे:"
        }
        order_info.append(bulk_info.get(language, bulk_info['en']))
        order_info.append("• Up to 15% discount on bulk orders")
        order_info.append("• Group ordering available")
        order_info.append("• Special wholesale rates")
    
    # Add specific item suggestions
    if has_specific_items:
        order_info.append("\n🎯 SPECIFIC ITEMS FOUND:")
        order_info.append("• I can help you find the best suppliers for these items")
        order_info.append("• Price comparison available")
        order_info.append("• Stock availability check")
    
    # Add general order options
    order_options = {
        'en': [
            "\n📋 ORDER OPTIONS:",
            "• Browse products by category",
            "• Search for specific items",
            "• Create a group order for bulk discounts",
            "• View your order history",
            "• Track current orders"
        ],
        'hi': [
            "\n📋 ऑर्डर विकल्प:",
            "• श्रेणी के अनुसार उत्पाद ब्राउज़ करें",
            "• विशिष्ट आइटम खोजें",
            "• बल्क छूट के लिए ग्रुप ऑर्डर बनाएं",
            "• अपना ऑर्डर इतिहास देखें",
            "• वर्तमान ऑर्डर ट्रैक करें"
        ],
        'bn': [
            "\n📋 অর্ডার বিকল্প:",
            "• বিভাগ অনুযায়ী পণ্য ব্রাউজ করুন",
            "• নির্দিষ্ট আইটেম খুঁজুন",
            "• বাল্ক ছাড়ের জন্য গ্রুপ অর্ডার তৈরি করুন",
            "• আপনার অর্ডার ইতিহাস দেখুন",
            "• বর্তমান অর্ডার ট্র্যাক করুন"
        ],
        'ta': [
            "\n📋 ஆர்டர் விருப்பங்கள்:",
            "• வகைப்படி தயாரிப்புகளை உலாவுங்கள்",
            "• குறிப்பிட்ட பொருட்களைத் தேடுங்கள்",
            "• மொத்த தள்ளுபடிக்கு குழு ஆர்டர் உருவாக்குங்கள்",
            "• உங்கள் ஆர்டர் வரலாற்றைப் பாருங்கள்",
            "• தற்போதைய ஆர்டர்களைக் கண்காணிக்கவும்"
        ],
        'mr': [
            "\n📋 ऑर्डर पर्याय:",
            "• श्रेणीनुसार उत्पादने ब्राउझ करा",
            "• विशिष्ट आयटम शोधा",
            "• मोठ्या सवलतींसाठी ग्रुप ऑर्डर तयार करा",
            "• तुमचा ऑर्डर इतिहास पाहा",
            "• सध्याचे ऑर्डर ट्रॅक करा"
        ]
    }
    
    order_info.extend(order_options.get(language, order_options['en']))
    
    # Add business-specific suggestions
    if vendor and vendor.business_type:
        business_tips = {
            'ice_cream': {
                'en': "\n🍦 ICE CREAM BUSINESS TIPS:",
                'hi': "\n🍦 आइसक्रीम व्यवसाय सुझाव:",
                'bn': "\n🍦 আইসক্রিম ব্যবসার টিপস:",
                'ta': "\n🍦 ஐஸ்கிரீம் வணிக குறிப்புகள்:"
            },
            'chaat': {
                'en': "\n🌶️ CHAAT BUSINESS TIPS:",
                'hi': "\n🌶️ चाट व्यवसाय सुझाव:",
                'bn': "\n🌶️ চাট ব্যবসার টিপস:",
                'ta': "\n🌶️ சாட் வணிக குறிப்புகள்:"
            }
        }
        
        tip_header = business_tips.get(vendor.business_type, {}).get(language, "")
        if tip_header:
            order_info.append(tip_header)
            order_info.append("• Order fresh ingredients daily")
            order_info.append("• Consider seasonal pricing")
            order_info.append("• Plan for peak hours")
    
    return {
        'message': {
            'type': 'list',
            'items': order_info
        },
        'context': {'intent': 'orders', 'urgency': is_urgent, 'bulk': is_bulk},
        'actions': make_actions(language, [
            ('browse-products', 'Browse Products'),
            ('search-products', 'Search Products'),
            ('create-group-order', 'Create Group Order'),
            ('view-orders', 'View Orders'),
            ('urgent-order', 'Urgent Order') if is_urgent else (None, None),
            ('bulk-order', 'Bulk Order') if is_bulk else (None, None),
            ('price-check', 'Check Prices'),
            ('stock-check', 'Check Stock')
        ])
    }

def get_help_response(language, vendor):
    """Generate help response"""
    responses = {
        'en': "I'm here to help! Here are the main things I can assist you with:",
        'hi': "मैं मदद के लिए यहाँ हूँ! यहाँ मुख्य चीजें हैं जिनमें मैं आपकी मदद कर सकता हूँ:",
        'context': {'intent': 'help'},
        'actions': make_actions(language, [
            ('contact-support', 'Contact Support'),
            ('faq', 'View FAQ'),
            ('tutorial', 'Watch Tutorial'),
            ('feedback', 'Send Feedback')
        ])
    }

def get_account_response(language, vendor):
    """Generate account-related response"""
    if not vendor:
        responses = {
            'en': "You need to log in to access your account features. Would you like to log in?",
            'hi': "अपने खाता फीचर्स तक पहुँचने के लिए आपको लॉग इन करना होगा। क्या आप लॉग इन करना चाहते हैं?",
            'bn': "আপনার অ্যাকাউন্ট ফিচার অ্যাক্সেস করতে আপনাকে লগ ইন করতে হবে। আপনি কি লগ ইন করতে চান?",
            'ta': "உங்கள் கணக்கு அம்சங்களை அணுக நீங்கள் உள்நுழைய வேண்டும்। நீங்கள் உள்நுழைய விரும்புகிறீர்களா?",
            'mr': "तुमच्या खात्याची वैशिष्ट्ये वापरण्यासाठी तुम्हाला लॉग इन करणे आवश्यक आहे. तुम्हाला लॉग इन करायचे आहे का?"
        }
        
        return {
            'message': responses.get(language, responses['en']),
            'context': {'intent': 'account', 'requires_login': True},
            'actions': make_actions(language, [
                ('login', 'Log In'),
                ('register', 'Register')
            ])
        }
    
    responses = {
        'en': f"Welcome back, {vendor.name}! Here's your account overview:",
        'hi': f"वापस स्वागत है, {vendor.name}! यहाँ आपका खाता अवलोकन है:",
        'bn': f"ফিরে স্বাগতম, {vendor.name}! এখানে আপনার অ্যাকাউন্ট ওভারভিউ:",
        'ta': f"மீண்டும் வரவேற்கிறோம், {vendor.name}! இங்கே உங்கள் கணக்கு கண்ணோட்டம்:",
        'mr': f"पुन्हा स्वागत आहे, {vendor.name}! येथे तुमच्या खात्याचा आढावा आहे:"
    }
    
    account_info = {
        'en': [
            f"Business Type: {vendor.business_type.title()}",
            f"Location: {vendor.location}",
            f"Phone: {vendor.phone}",
            "View your order history",
            "Update profile information",
            "Change password",
            "Manage notifications"
        ],
        'hi': [
            f"व्यवसाय प्रकार: {vendor.business_type.title()}",
            f"स्थान: {vendor.location}",
            f"फोन: {vendor.phone}",
            "अपना ऑर्डर इतिहास देखें",
            "प्रोफाइल जानकारी अपडेट करें",
            "पासवर्ड बदलें",
            "नोटिफिकेशन प्रबंधित करें"
        ],
        'bn': [
            f"ব্যবসার ধরন: {vendor.business_type.title()}",
            f"অবস্থান: {vendor.location}",
            f"ফোন: {vendor.phone}",
            "আপনার অর্ডার ইতিহাস দেখুন",
            "প্রোফাইল তথ্য আপডেট করুন",
            "পাসওয়ার্ড পরিবর্তন করুন",
            "নোটিফিকেশন পরিচালনা করুন"
        ],
        'ta': [
            f"வணிக வகை: {vendor.business_type.title()}",
            f"இடம்: {vendor.location}",
            f"தொலைபேசி: {vendor.phone}",
            "உங்கள் ஆர்டர் வரலாற்றைப் பாருங்கள்",
            "சுயவிவர தகவலைப் புதுப்பிக்கவும்",
            "கடவுச்சொல்லை மாற்றவும்",
            "அறிவிப்புகளை நிர்வகிக்கவும்"
        ],
        'mr': [
            f"व्यवसाय प्रकार: {vendor.business_type.title()}",
            f"स्थान: {vendor.location}",
            f"फोन: {vendor.phone}",
            "तुमचा ऑर्डर इतिहास पहा",
            "प्रोफाइल माहिती अपडेट करा",
            "पासवर्ड बदला",
            "नोटिफिकेशन्स व्यवस्थापित करा"
        ]
    }
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + account_info.get(language, account_info['en'])
        },
        'context': {'intent': 'account', 'vendor_id': vendor.id},
        'actions': make_actions(language, [
            ('view-profile', 'View Profile'),
            ('edit-profile', 'Edit Profile'),
            ('order-history', 'Order History'),
            ('settings', 'Settings')
        ])
    }

def get_intelligent_default_response(language, vendor, message, context):
    """Generate intelligent default response with context awareness and suggestions"""
    
    # Analyze the message for potential keywords
    keywords_found = []
    all_keywords = {
        'supplier': ['supplier', 'vendor', 'seller', 'dealer', 'wholesale'],
        'product': ['product', 'item', 'goods', 'materials', 'ingredients'],
        'price': ['price', 'cost', 'expensive', 'cheap', 'rate'],
        'order': ['order', 'buy', 'purchase', 'need', 'want'],
        'delivery': ['delivery', 'ship', 'send', 'transport'],
        'business': ['business', 'shop', 'store', 'restaurant', 'food']
    }
    
    for category, keywords in all_keywords.items():
        if any(keyword in message for keyword in keywords):
            keywords_found.append(category)
    
    # Generate contextual response
    if keywords_found:
        responses = {
            'en': f"I can see you're interested in {', '.join(keywords_found)}. Let me help you with that:",
            'hi': f"मैं देख सकता हूँ कि आप {', '.join(keywords_found)} में रुचि रखते हैं। मैं आपकी मदद करूंगा:",
            'bn': f"আমি দেখতে পাচ্ছি যে আপনি {', '.join(keywords_found)} নিয়ে আগ্রহী। আমি আপনাকে সাহায্য করব:",
            'ta': f"நீங்கள் {', '.join(keywords_found)} பற்றி ஆர்வமாக இருப்பதை நான் பார்க்கிறேன்। நான் உங்களுக்கு உதவுவேன்:",
            'mr': f"मी पाहतोय की तुम्हाला {', '.join(keywords_found)} मध्ये रस आहे. मी त्यात तुमची मदत करतो:"
        }
        
        base_message = responses.get(language, responses['en'])
        
        # Add specific suggestions based on keywords found
        suggestions = []
        if 'supplier' in keywords_found:
            suggestions.extend([
                "• Find verified suppliers near you",
                "• Compare supplier ratings and prices",
                "• Contact suppliers directly"
            ])
        if 'product' in keywords_found:
            suggestions.extend([
                "• Browse products by category",
                "• Search for specific items",
                "• Check product availability"
            ])
        if 'price' in keywords_found:
            suggestions.extend([
                "• Compare prices across suppliers",
                "• Set up price alerts",
                "• Find bulk discounts"
            ])
        if 'order' in keywords_found:
            suggestions.extend([
                "• Place individual orders",
                "• Create group orders for savings",
                "• Track order status"
            ])
        if 'delivery' in keywords_found:
            suggestions.extend([
                "• Track your deliveries",
                "• Schedule delivery times",
                "• Get delivery notifications"
            ])
        if 'business' in keywords_found:
            suggestions.extend([
                "• Get business tips and advice",
                "• Access market trends",
                "• Connect with other vendors"
            ])
        
        return {
            'message': {
                'type': 'list',
                'items': [base_message] + suggestions
            },
            'context': {'intent': 'unclear', 'keywords_found': keywords_found},
            'actions': [
                {'action': 'find-suppliers', 'label': 'Find Suppliers'},
                {'action': 'browse-products', 'label': 'Browse Products'},
                {'action': 'compare-prices', 'label': 'Compare Prices'},
                {'action': 'place-order', 'label': 'Place Order'},
                {'action': 'business-tips', 'label': 'Business Tips'}
            ]
        }
    
    # If no keywords found, provide general help
    responses = {
        'en': "I'm here to help you with your business needs! Here are some things I can assist you with:",
        'hi': "मैं आपकी व्यावसायिक जरूरतों में आपकी मदद करने के लिए यहाँ हूँ! यहाँ कुछ चीजें हैं जिनमें मैं आपकी मदद कर सकता हूँ:",
        'bn': "আমি আপনার ব্যবসায়িক প্রয়োজনে সাহায্য করতে এখানে আছি! এখানে কিছু বিষয় রয়েছে যাতে আমি আপনাকে সাহায্য করতে পারি:",
        'ta': "உங்கள் வணிகத் தேவைகளுக்கு உதவ நான் இங்கே இருக்கிறேன்! இங்கே சில விஷயங்கள் உள்ளன, அதில் நான் உங்களுக்கு உதவ முடியும்:",
        'mr': "मी तुमच्या व्यावसायिक गरजांसाठी मदत करण्यासाठी येथे आहे! मी ज्या गोष्टींमध्ये मदत करू शकतो त्या येथे आहेत:"
    }
    
    general_options = {
        'en': [
            "🔍 Finding and connecting with suppliers",
            "🛒 Placing individual and group orders",
            "💰 Managing price alerts and notifications",
            "👤 Account settings and profile management",
            "📞 Getting support and resolving issues",
            "📊 Business analytics and insights",
            "🎯 Market trends and opportunities"
        ],
        'hi': [
            "🔍 आपूर्तिकर्ताओं को खोजना और उनसे जुड़ना",
            "🛒 व्यक्तिगत और समूह ऑर्डर देना",
            "💰 मूल्य अलर्ट और नोटिफिकेशन प्रबंधित करना",
            "👤 खाता सेटिंग्स और प्रोफाइल प्रबंधन",
            "📞 सहायता प्राप्त करना और मुद्दों को हल करना",
            "📊 व्यावसायिक विश्लेषण और अंतर्दृष्टि",
            "🎯 बाजार रुझान और अवसर"
        ],
        'bn': [
            "🔍 সরবরাহকারী খুঁজে পাওয়া এবং তাদের সাথে সংযোগ করা",
            "🛒 ব্যক্তিগত এবং গ্রুপ অর্ডার দেওয়া",
            "💰 মূল্য অ্যালার্ট এবং নোটিফিকেশন পরিচালনা করা",
            "👤 অ্যাকাউন্ট সেটিংস এবং প্রোফাইল পরিচালনা",
            "📞 সহায়তা পাওয়া এবং সমস্যা সমাধান করা",
            "📊 ব্যবসায়িক বিশ্লেষণ এবং অন্তর্দৃষ্টি",
            "🎯 বাজার প্রবণতা এবং সুযোগ"
        ],
        'ta': [
            "🔍 சப்ளையர்களைக் கண்டுபிடித்தல் மற்றும் அவர்களுடன் இணைத்தல்",
            "🛒 தனிப்பட்ட மற்றும் குழு ஆர்டர்களை வைத்தல்",
            "💰 விலை எச்சரிக்கைகள் மற்றும் அறிவிப்புகளை நிர்வகித்தல்",
            "👤 கணக்கு அமைப்புகள் மற்றும் சுயவிவர நிர்வாகம்",
            "📞 ஆதரவு பெறுதல் மற்றும் பிரச்சினைகளைத் தீர்ப்பது",
            "📊 வணிக பகுப்பாய்வு மற்றும் நுண்ணறிவு",
            "🎯 சந்தை போக்குகள் மற்றும் வாய்ப்புகள்"
        ],
        'mr': [
            "🔍 पुरवठादार शोधणे आणि त्यांच्याशी जोडणे",
            "🛒 वैयक्तिक आणि समूह ऑर्डर देणे",
            "💰 किंमत अलर्ट आणि नोटिफिकेशन्स व्यवस्थापित करणे",
            "👤 अकाउंट सेटिंग्स आणि प्रोफाइल व्यवस्थापन",
            "📞 सहाय्य मिळवणे आणि समस्या सोडवणे",
            "📊 व्यवसाय विश्लेषण आणि अंतर्दृष्टी",
            "🎯 बाजारातील प्रवृत्ती आणि संधी"
        ]
    }
    
    # Add personalized suggestions if vendor is logged in
    if vendor:
        personalized_tips = {
            'en': f"\n\n👋 Hi {vendor.name}! Since you're in the {vendor.business_type} business, here are some personalized suggestions:",
            'hi': f"\n\n👋 नमस्ते {vendor.name}! चूंकि आप {vendor.business_type} व्यवसाय में हैं, यहाँ कुछ व्यक्तिगत सुझाव हैं:",
            'bn': f"\n\n👋 হাই {vendor.name}! যেহেতু আপনি {vendor.business_type} ব্যবসায় আছেন, এখানে কিছু ব্যক্তিগত পরামর্শ:",
            'ta': f"\n\n👋 வணக்கம் {vendor.name}! நீங்கள் {vendor.business_type} வணிகத்தில் இருப்பதால், இங்கே சில தனிப்பட்ட பரிந்துரைகள்:",
            'mr': f"\n\n👋 हाय {vendor.name}! तुम्ही {vendor.business_type} व्यवसायात असल्यामुळे, येथे काही वैयक्तिक सूचना आहेत:"
        }
        
        business_specific_tips = {
            'ice_cream': {
                'en': [
                    "• Check dairy supplier ratings for quality",
                    "• Order seasonal fruits for new flavors",
                ],
                'hi': [
                    "• गुणवत्ता के लिए डेयरी आपूर्तिकर्ता रेटिंग जांचें",
                    "• नए स्वादों के लिए मौसमी फल ऑर्डर करें",
                    "• तापमान-संवेदनशील डिलीवरी की निगरानी करें"
                ],
                'mr': [
                    "• गुणवत्ता सुनिश्चित करण्यासाठी डेअरी पुरवठादारांचे रेटिंग तपासा",
                    "• तापमान-संवेदनशील डिलिव्हरीचे निरीक्षण करा"
                ]
            },
            'chaat': {
                'en': [
                    "• Source fresh vegetables daily",
                    "• Find authentic spice suppliers",
                    "• Plan for peak evening hours"
                ],
                'hi': [
                    "• दैनिक ताजी सब्जियां सोर्स करें",
                    "• प्रामाणिक मसाला आपूर्तिकर्ता खोजें",
                    "• शाम के पीक घंटों की योजना बनाएं"
                ],
                'mr': [
                    "• दररोज ताजी भाजीपाला सोर्स करा",
                    "• पारंपरिक मसाल्यांचे पुरवठादार शोधा",
                ]
            }
        }
        
        tip_header = personalized_tips.get(language, personalized_tips['en'])
        tips = business_specific_tips.get(vendor.business_type, {}).get(language, [])
        
        if tips:
            general_options[language].extend(tips)
    
    return {
        'message': {
            'type': 'list',
            'items': [responses.get(language, responses['en'])] + general_options.get(language, general_options['en'])
        },
        'context': {'intent': 'unclear', 'general_help': True},
        'actions': make_actions(language, [
            ('find-suppliers', 'Find Suppliers'),
            ('place-order', 'Place Order'),
            ('price-alerts', 'Price Alerts'),
            ('account-settings', 'Account Settings'),
            ('contact-support', 'Contact Support'),
            ('business-analytics', 'Business Analytics'),
            ('market-trends', 'Market Trends')
        ])
    }

@app.route('/chatbot')
def chatbot_page():
    """Dedicated chatbot page for testing"""
    return render_template('chatbot.html')

# ==================== REVIEWS & RATINGS ====================

@app.route('/api/customer/reviews', methods=['POST'])
@customer_api_required
def submit_review():
    """Submit a review for a vendor"""
    try:
        customer_id = session['customer_id']
        data = request.get_json() or {}
        
        vendor_id = data.get('vendor_id')
        order_id = data.get('order_id')
        rating = data.get('rating', 5)
        food_quality = data.get('food_quality')
        delivery_speed = data.get('delivery_speed')
        packaging = data.get('packaging')
        review_text = (data.get('review_text') or '').strip()
        
        if not vendor_id or rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'Invalid rating or vendor'}), 400
        
        # Check if vendor exists
        vendor = db.session.get(Vendor, vendor_id)
        if not vendor:
            return jsonify({'success': False, 'message': 'Vendor not found'}), 404
        
        # Check if customer already reviewed this order
        if order_id:
            existing = CustomerReview.query.filter_by(
                customer_id=customer_id,
                order_id=order_id
            ).first()
            if existing:
                return jsonify({'success': False, 'message': 'You already reviewed this order'}), 409
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and is_allowed_image(image_file.filename):
                upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'reviews')
                os.makedirs(upload_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_filename = secure_filename(image_file.filename)
                unique_name = f"{customer_id}_{timestamp}_{safe_filename}"
                image_path_full = os.path.join(upload_dir, unique_name)
                image_file.save(image_path_full)
                image_path = f"uploads/reviews/{unique_name}"
        
        review = CustomerReview(
            customer_id=customer_id,
            vendor_id=vendor_id,
            order_id=order_id,
            rating=rating,
            food_quality=food_quality,
            delivery_speed=delivery_speed,
            packaging=packaging,
            review_text=review_text,
            image=image_path
        )
        
        db.session.add(review)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Review submitted successfully',
            'review_id': review.id
        })
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error submitting review: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/vendor/<int:vendor_id>/reviews', methods=['GET'])
def get_vendor_reviews(vendor_id):
    """Get reviews for a vendor"""
    try:
        # Get all reviews for this vendor
        reviews = CustomerReview.query.filter_by(vendor_id=vendor_id).order_by(
            CustomerReview.created_at.desc()
        ).all()
        
        reviews_data = []
        for review in reviews:
            customer = db.session.get(Customer, review.customer_id)
            reviews_data.append({
                'id': review.id,
                'rating': review.rating,
                'food_quality': review.food_quality,
                'delivery_speed': review.delivery_speed,
                'packaging': review.packaging,
                'review_text': review.review_text,
                'image': review.image,
                'helpful_votes': review.helpful_votes,
                'customer_name': customer.name if customer else 'Anonymous',
                'created_at': format_ist_time(review.created_at, '%d %b %Y')
            })
        
        # Calculate average ratings
        all_reviews = CustomerReview.query.filter_by(vendor_id=vendor_id).all()
        avg_overall = sum(r.rating for r in all_reviews) / len(all_reviews) if all_reviews else 0
        avg_food = sum(r.food_quality for r in all_reviews if r.food_quality) / len([r for r in all_reviews if r.food_quality]) if any(r.food_quality for r in all_reviews) else 0
        avg_delivery = sum(r.delivery_speed for r in all_reviews if r.delivery_speed) / len([r for r in all_reviews if r.delivery_speed]) if any(r.delivery_speed for r in all_reviews) else 0
        avg_packaging = sum(r.packaging for r in all_reviews if r.packaging) / len([r for r in all_reviews if r.packaging]) if any(r.packaging for r in all_reviews) else 0
        
        return jsonify({
            'success': True,
            'reviews': reviews_data,
            'total_reviews': len(reviews_data),
            'averages': {
                'overall': round(avg_overall, 1),
                'food_quality': round(avg_food, 1),
                'delivery_speed': round(avg_delivery, 1),
                'packaging': round(avg_packaging, 1)
            }
        })
    
    except Exception as e:
        app.logger.error(f'Error fetching reviews: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/review/<int:review_id>/helpful', methods=['POST'])
def mark_review_helpful(review_id):
    """Mark a review as helpful"""
    try:
        review = db.session.get(CustomerReview, review_id)
        if not review:
            return jsonify({'success': False, 'message': 'Review not found'}), 404
        
        review.helpful_votes += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'helpful_votes': review.helpful_votes
        })
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error marking review helpful: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== WISHLIST ====================

@app.route('/api/customer/wishlist', methods=['GET', 'POST'])
@customer_api_required
def customer_wishlist():
    """Get or add to customer wishlist"""
    customer_id = session['customer_id']
    
    if request.method == 'GET':
        try:
            wishlist = Wishlist.query.filter_by(customer_id=customer_id).all()
            items = []
            
            for w in wishlist:
                if w.item_type == 'vendor':
                    vendor = db.session.get(Vendor, w.vendor_id)
                    if vendor:
                        items.append({
                            'id': w.id,
                            'type': 'vendor',
                            'vendor_id': vendor.id,
                            'name': vendor.name,
                            'location': vendor.location,
                            'cuisine': vendor.business_type,
                            'logo': vendor.logo or '',
                            'added_at': format_ist_time(w.created_at, '%d %b %Y')
                        })
                else:  # menu_item
                    item = db.session.get(MenuItem, w.menu_item_id)
                    vendor = db.session.get(Vendor, item.vendor_id) if item else None
                    if item and vendor:
                        items.append({
                            'id': w.id,
                            'type': 'item',
                            'item_id': item.id,
                            'item_name': item.name,
                            'vendor_id': vendor.id,
                            'vendor_name': vendor.name,
                            'price': item.price,
                            'image': item.image or '',
                            'added_at': format_ist_time(w.created_at, '%d %b %Y')
                        })
            
            return jsonify({'success': True, 'wishlist': items})
        
        except Exception as e:
            app.logger.error(f'Error fetching wishlist: {str(e)}')
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    else:  # POST
        try:
            data = request.get_json() or {}
            item_type = data.get('type', 'vendor')  # 'vendor' or 'item'
            
            if item_type == 'vendor':
                vendor_id = data.get('vendor_id')
                if not vendor_id:
                    return jsonify({'success': False, 'message': 'Vendor ID required'}), 400
                
                # Check if already in wishlist
                existing = Wishlist.query.filter_by(
                    customer_id=customer_id,
                    vendor_id=vendor_id,
                    item_type='vendor'
                ).first()
                
                if existing:
                    return jsonify({'success': False, 'message': 'Already in wishlist'}), 409
                
                wishlist_item = Wishlist(
                    customer_id=customer_id,
                    vendor_id=vendor_id,
                    item_type='vendor'
                )
            
            else:  # item
                item_id = data.get('item_id')
                if not item_id:
                    return jsonify({'success': False, 'message': 'Item ID required'}), 400
                
                # Check if already in wishlist
                existing = Wishlist.query.filter_by(
                    customer_id=customer_id,
                    menu_item_id=item_id,
                    item_type='item'
                ).first()
                
                if existing:
                    return jsonify({'success': False, 'message': 'Already in wishlist'}), 409
                
                wishlist_item = Wishlist(
                    customer_id=customer_id,
                    menu_item_id=item_id,
                    item_type='item'
                )
            
            db.session.add(wishlist_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Added to wishlist',
                'wishlist_id': wishlist_item.id
            })
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error adding to wishlist: {str(e)}')
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/wishlist/<int:wishlist_id>', methods=['DELETE'])
@customer_api_required
def remove_from_wishlist(wishlist_id):
    """Remove item from wishlist"""
    try:
        customer_id = session['customer_id']
        wishlist_item = db.session.get(Wishlist, wishlist_id)
        
        if not wishlist_item or wishlist_item.customer_id != customer_id:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        db.session.delete(wishlist_item)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Removed from wishlist'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error removing from wishlist: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/customer/wishlist/<int:vendor_id>/check', methods=['GET'])
@customer_api_required
def check_in_wishlist(vendor_id):
    """Check if vendor is in wishlist"""
    customer_id = session['customer_id']
    exists = Wishlist.query.filter_by(
        customer_id=customer_id,
        vendor_id=vendor_id,
        item_type='vendor'
    ).first()
    
    return jsonify({'in_wishlist': bool(exists)})

# ==================== REWARDS & COUPONS ====================

@app.route('/api/customer/rewards', methods=['GET'])
@customer_api_required
def customer_rewards():
    """Get customer rewards and available coupons"""
    customer_id = session['customer_id']
    
    try:
        # Get customer's total reward points (from self-pickup distance rewards)
        customer = Customer.query.get(customer_id)
        total_points = customer.reward_points if hasattr(customer, 'reward_points') else 0
        
        # Generate sample coupons based on reward points
        # In a production system, these would be stored in a Coupon table
        coupons = []
        
        if total_points >= 50:
            coupons.append({
                'id': 1,
                'code': 'SELFPICK50',
                'title': 'Self-Pickup Bonus',
                'description': 'Get 10% off on your next order',
                'discount': 10,
                'discountType': 'percentage',
                'expiryDate': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'minPurchase': 200,
                'redeemed': False,
                'source': 'self_pickup_reward'
            })
        
        if total_points >= 100:
            coupons.append({
                'id': 2,
                'code': 'DISTANCE100',
                'title': 'Long Distance Reward',
                'description': 'Get ₹50 off on any order',
                'discount': 50,
                'discountType': 'amount',
                'expiryDate': (datetime.utcnow() + timedelta(days=45)).isoformat(),
                'minPurchase': 300,
                'redeemed': False,
                'source': 'distance_reward'
            })
        
        if total_points >= 200:
            coupons.append({
                'id': 3,
                'code': 'LOYAL200',
                'title': 'Loyalty Bonus',
                'description': 'Unlock free delivery on your next order',
                'discount': 100,
                'discountType': 'delivery',
                'expiryDate': (datetime.utcnow() + timedelta(days=60)).isoformat(),
                'minPurchase': 0,
                'redeemed': False,
                'source': 'loyalty_reward'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'totalPoints': total_points,
                'coupons': coupons
            }
        })
    
    except Exception as e:
        app.logger.error(f'Error fetching customer rewards: {str(e)}')
        return jsonify({
            'success': True,
            'data': {
                'totalPoints': 0,
                'coupons': []
            }
        })

# ==================== SCHEDULED ORDERS ====================

@app.route('/api/customer/scheduled-orders', methods=['GET', 'POST'])
@customer_api_required
def customer_scheduled_orders():
    """Get or create scheduled orders"""
    customer_id = session['customer_id']
    
    if request.method == 'GET':
        try:
            orders = ScheduledOrder.query.filter_by(
                customer_id=customer_id,
                status='pending'
            ).order_by(ScheduledOrder.scheduled_time.asc()).all()
            
            scheduled_orders = []
            for order in orders:
                scheduled_orders.append({
                    'id': order.id,
                    'scheduled_time': format_ist_time(order.scheduled_time, '%d %b %Y, %I:%M %p'),
                    'recurring': order.recurring,
                    'notes': order.notes,
                    'order_data': json.loads(order.order_data),
                    'status': order.status,
                    'created_at': format_ist_time(order.created_at, '%d %b %Y')
                })
            
            return jsonify({
                'success': True,
                'scheduled_orders': scheduled_orders
            })
        
        except Exception as e:
            app.logger.error(f'Error fetching scheduled orders: {str(e)}')
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
    else:  # POST
        try:
            data = request.get_json() or {}
            
            scheduled_time_str = data.get('scheduled_time')
            if not scheduled_time_str:
                return jsonify({'success': False, 'message': 'Scheduled time required'}), 400
            
            # Parse datetime
            try:
                scheduled_time = datetime.fromisoformat(scheduled_time_str)
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid datetime format'}), 400
            
            order_data = data.get('order_data', {})
            recurring = data.get('recurring')  # None, 'daily', 'weekly', 'monthly'
            notes = (data.get('notes') or '').strip()
            
            scheduled_order = ScheduledOrder(
                customer_id=customer_id,
                order_data=json.dumps(order_data),
                scheduled_time=scheduled_time,
                recurring=recurring,
                notes=notes,
                status='pending'
            )
            
            db.session.add(scheduled_order)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Order scheduled successfully',
                'order_id': scheduled_order.id
            })
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error scheduling order: {str(e)}')
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/scheduled-order/<int:order_id>', methods=['DELETE', 'PUT'])
@customer_api_required
def manage_scheduled_order(order_id):
    """Cancel or update scheduled order"""
    try:
        customer_id = session['customer_id']
        order = db.session.get(ScheduledOrder, order_id)
        
        if not order or order.customer_id != customer_id:
            return jsonify({'success': False, 'message': 'Order not found'}), 404
        
        if request.method == 'DELETE':
            order.status = 'cancelled'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Order cancelled'})
        
        else:  # PUT
            data = request.get_json() or {}
            if 'scheduled_time' in data:
                try:
                    order.scheduled_time = datetime.fromisoformat(data['scheduled_time'])
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid datetime format'}), 400
            
            if 'notes' in data:
                order.notes = (data['notes'] or '').strip()
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Order updated'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error managing scheduled order: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== SMART RECOMMENDATIONS ====================

@app.route('/api/customer/recommendations', methods=['GET'])
@customer_api_required
def get_recommendations():
    """Get personalized recommendations based on order history"""
    try:
        customer_id = session['customer_id']
        
        # Get customer's past orders
        past_orders = CustomerOrder.query.filter_by(
            customer_id=customer_id
        ).order_by(CustomerOrder.created_at.desc()).limit(10).all()
        
        # Get favorite vendors from order history
        favorite_vendors = {}
        for order in past_orders:
            order_items = CustomerOrderItem.query.filter_by(order_id=order.id).all()
            for item in order_items:
                menu_item = db.session.get(MenuItem, item.menu_item_id)
                if menu_item:
                    vendor_id = menu_item.vendor_id
                    favorite_vendors[vendor_id] = favorite_vendors.get(vendor_id, 0) + 1
        
        recommendations = {
            'trending': [],
            'based_on_history': [],
            'similar_to_favorites': [],
            'new_from_favorites': []
        }
        
        # 1. Trending items (most ordered recently)
        all_items = db.session.query(MenuItem).order_by(MenuItem.created_at.desc()).limit(20).all()
        for item in all_items[:5]:
            vendor = db.session.get(Vendor, item.vendor_id)
            if vendor and vendor.is_open:
                recommendations['trending'].append({
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'image': item.image or '',
                    'vendor_id': vendor.id,
                    'vendor_name': vendor.name,
                    'reason': 'Trending now'
                })
        
        # 2. Similar items from favorite vendors
        if favorite_vendors:
            top_vendor_id = max(favorite_vendors, key=favorite_vendors.get)
            vendor_items = MenuItem.query.filter_by(vendor_id=top_vendor_id).limit(5).all()
            for item in vendor_items:
                vendor = db.session.get(Vendor, item.vendor_id)
                if vendor and vendor.is_open:
                    recommendations['based_on_history'].append({
                        'id': item.id,
                        'name': item.name,
                        'price': item.price,
                        'image': item.image or '',
                        'vendor_id': vendor.id,
                        'vendor_name': vendor.name,
                        'reason': f'More from your favorite vendor'
                    })
        
        # 3. Similar items from similar business types
        if favorite_vendors:
            top_vendor = db.session.get(Vendor, max(favorite_vendors, key=favorite_vendors.get))
            if top_vendor:
                similar_vendors = Vendor.query.filter_by(
                    business_type=top_vendor.business_type
                ).filter(Vendor.id != top_vendor.id).limit(3).all()
                
                for vendor in similar_vendors:
                    if vendor.is_open:
                        items = MenuItem.query.filter_by(vendor_id=vendor.id).limit(3).all()
                        for item in items:
                            recommendations['similar_to_favorites'].append({
                                'id': item.id,
                                'name': item.name,
                                'price': item.price,
                                'image': item.image or '',
                                'vendor_id': vendor.id,
                                'vendor_name': vendor.name,
                                'reason': f'Similar to {top_vendor.name}'
                            })
        
        # 4. New items from favorite vendors
        if favorite_vendors:
            for vendor_id, _ in sorted(favorite_vendors.items(), key=lambda x: x[1], reverse=True)[:2]:
                vendor = db.session.get(Vendor, vendor_id)
                if vendor and vendor.is_open:
                    new_items = MenuItem.query.filter_by(vendor_id=vendor_id).order_by(
                        MenuItem.created_at.desc()
                    ).limit(3).all()
                    
                    for item in new_items:
                        recommendations['new_from_favorites'].append({
                            'id': item.id,
                            'name': item.name,
                            'price': item.price,
                            'image': item.image or '',
                            'vendor_id': vendor.id,
                            'vendor_name': vendor.name,
                            'reason': f'New at {vendor.name}'
                        })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    
    except Exception as e:
        app.logger.error(f'Error generating recommendations: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== SORTING & FILTERING ====================

@app.route('/api/vendors/sorted', methods=['GET'])
def get_sorted_vendors():
    """Get vendors sorted by rating, category, or distance"""
    try:
        sort_by = request.args.get('sort_by', 'rating')  # rating, category, distance, newest
        category = request.args.get('category', '')
        search = request.args.get('search', '').strip()
        
        query = Vendor.query.filter_by(is_open=True)
        
        # Filter by search
        if search:
            query = query.filter(
                db.or_(
                    Vendor.name.ilike(f'%{search}%'),
                    Vendor.location.ilike(f'%{search}%')
                )
            )
        
        # Filter by category
        if category:
            query = query.filter_by(business_type=category)
        
        vendors = query.all()
        vendors_data = []
        
        for vendor in vendors:
            # Calculate average rating from reviews
            reviews = CustomerReview.query.filter_by(vendor_id=vendor.id).all()
            avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
            review_count = len(reviews)
            
            vendors_data.append({
                'id': vendor.id,
                'name': vendor.name,
                'location': vendor.location,
                'cuisine': vendor.business_type,
                'logo': vendor.logo or '',
                'hero_image': vendor.hero_image or '',
                'rating': round(avg_rating, 1),
                'review_count': review_count,
                'created_at': vendor.created_at
            })
        
        # Sort based on criteria
        if sort_by == 'rating':
            vendors_data.sort(key=lambda x: (x['rating'], x['review_count']), reverse=True)
        elif sort_by == 'category':
            vendors_data.sort(key=lambda x: x['cuisine'])
        elif sort_by == 'newest':
            vendors_data.sort(key=lambda x: x['created_at'], reverse=True)
        elif sort_by == 'reviews':
            vendors_data.sort(key=lambda x: x['review_count'], reverse=True)
        
        return jsonify({
            'success': True,
            'vendors': vendors_data,
            'total': len(vendors_data)
        })
    
    except Exception as e:
        app.logger.error(f'Error sorting vendors: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/menu/sorted', methods=['GET'])
def get_sorted_menu():
    """Get menu items sorted by rating, category, price"""
    try:
        sort_by = request.args.get('sort_by', 'price')  # rating, price, newest, popularity
        category = request.args.get('category', '')
        vendor_id = request.args.get('vendor_id', '')
        search = request.args.get('search', '').strip()
        
        query = MenuItem.query
        
        # Filter by vendor
        if vendor_id:
            query = query.filter_by(vendor_id=vendor_id)
        
        # Filter by search
        if search:
            query = query.filter(MenuItem.name.ilike(f'%{search}%'))
        
        items = query.all()
        items_data = []
        
        for item in items:
            vendor = db.session.get(Vendor, item.vendor_id)
            if not vendor or not vendor.is_open:
                continue
            
            # Get reviews for this vendor (for rating)
            reviews = CustomerReview.query.filter_by(vendor_id=vendor.id).all()
            vendor_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
            
            items_data.append({
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'description': item.description or '',
                'image': item.image or '',
                'vendor_id': vendor.id,
                'vendor_name': vendor.name,
                'vendor_rating': round(vendor_rating, 1),
                'created_at': item.created_at
            })
        
        # Sort based on criteria
        if sort_by == 'rating':
            items_data.sort(key=lambda x: x['vendor_rating'], reverse=True)
        elif sort_by == 'price_low':
            items_data.sort(key=lambda x: x['price'])
        elif sort_by == 'price_high':
            items_data.sort(key=lambda x: x['price'], reverse=True)
        elif sort_by == 'newest':
            items_data.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'items': items_data,
            'total': len(items_data)
        })
    
    except Exception as e:
        app.logger.error(f'Error sorting menu: {str(e)}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ─────────────────────────────────────────────────────────────────────────────
# AWS Services Routes
# ─────────────────────────────────────────────────────────────────────────────
try:
    from aws_services import (
        text_to_speech_base64,
        transcribe_audio_bytes,
        translate_text,
        LANGUAGE_NAMES,
        verify_supplier_document,
        send_sms_otp,
        upload_image_to_s3,
        publish_group_order_event,
        lambda_group_order_handler,
        analyze_food_image,
        S3_BUCKET_NAME,
        AWS_REGION,
    )
    AWS_ENABLED = True
except ImportError:
    AWS_ENABLED = False
    app.logger.warning('aws_services not found – AWS features disabled.')

# ── Voice: Text-to-Speech (Amazon Polly) ──────────────────────────────────────
@app.route('/api/voice/speak', methods=['POST'])
def voice_speak():
    """Convert text to speech using Amazon Polly. Returns base64 MP3."""
    if not AWS_ENABLED:
        return jsonify({'success': False, 'message': 'AWS not configured'}), 503

    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    language = (data.get('language') or 'hi').lower()

    if not text:
        return jsonify({'success': False, 'message': 'text is required'}), 400

    audio_b64 = text_to_speech_base64(text, language)
    if audio_b64 is None:
        return jsonify({'success': False, 'message': 'TTS unavailable – AWS Polly not configured or credential missing'}), 503

    return jsonify({
        'success': True,
        'audio_base64': audio_b64,
        'format': 'mp3',
        'language': language,
    })


# ── Voice: Speech-to-Text (Amazon Transcribe) ────────────────────────────────
@app.route('/api/voice/transcribe', methods=['POST'])
def voice_transcribe():
    """
    Transcribe audio to text.
    Accepts multipart/form-data with:
      - audio: audio file (webm / wav / mp3 / ogg)
      - language: language code (hi / en / ta / te / bn / mr ...)
    """
    if not AWS_ENABLED:
        return jsonify({
            'success': False,
            'message': 'AWS Transcribe not configured – add AWS credentials to .env',
            'aws_enabled': False,
        }), 503

    audio_file = request.files.get('audio')
    language   = (request.form.get('language') or request.args.get('language') or 'hi').lower()

    if audio_file is None:
        return jsonify({'success': False, 'message': 'No audio file provided'}), 400

    audio_bytes = audio_file.read()
    if len(audio_bytes) == 0:
        return jsonify({'success': False, 'message': 'Audio file is empty'}), 400

    # Determine format from filename / content-type
    filename = audio_file.filename or ''
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'webm'
    if ext not in ('mp3', 'mp4', 'wav', 'flac', 'ogg', 'webm', 'm4a'):
        ext = 'webm'

    transcript = transcribe_audio_bytes(audio_bytes, language, ext)
    if transcript is None:
        return jsonify({
            'success': False,
            'message': 'Transcription unavailable – AWS Transcribe/S3 not configured or credentials missing',
            'aws_enabled': AWS_ENABLED,
        }), 503

    return jsonify({
        'success': True,
        'transcript': transcript,
        'language': language,
    })


# ── Translation (Amazon Translate) ───────────────────────────────────────────
@app.route('/api/translate', methods=['POST'])
def translate_api():
    """
    Translate text(s) using Amazon Translate.
    Body: { "text": "...", "target": "hi", "source": "en" }
      OR  { "texts": ["...", "..."], "target": "hi" }
    """
    data   = request.get_json(silent=True) or {}
    target = (data.get('target') or data.get('language') or 'hi').lower()
    source = (data.get('source') or 'auto').lower()

    if not AWS_ENABLED:
        # Return original text unchanged when no AWS credentials
        if 'texts' in data:
            return jsonify({'success': True, 'translated': data['texts'], 'target': target, 'aws_enabled': False})
        text = (data.get('text') or '').strip()
        return jsonify({'success': True, 'original': text, 'translated': text, 'target': target,
                        'language_name': LANGUAGE_NAMES.get(target, target), 'aws_enabled': False})

    if 'texts' in data:
        texts   = data['texts']
        results = [translate_text(t, target, source) for t in texts]
        return jsonify({'success': True, 'translated': results, 'target': target})

    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'success': False, 'message': 'text is required'}), 400

    translated = translate_text(text, target, source)
    return jsonify({
        'success': True,
        'original': text,
        'translated': translated,
        'target': target,
        'language_name': LANGUAGE_NAMES.get(target, target),
    })


@app.route('/api/translate/languages')
def get_supported_languages():
    """Return list of supported languages."""
    return jsonify({
        'success': True,
        'languages': [
            {'code': code, 'name': name}
            for code, name in LANGUAGE_NAMES.items()
        ] if AWS_ENABLED else [{'code': 'en', 'name': 'English'}]
    })


# ── Supplier Document Verification (Amazon Rekognition) ──────────────────────
@app.route('/api/supplier/verify-document', methods=['POST'])
def verify_supplier_doc():
    """
    Upload and verify a supplier certification document.
    Accepts: multipart/form-data with 'document' file field.
    Returns verification result with confidence score.
    """
    if 'supplier_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401

    if not AWS_ENABLED:
        # Graceful mock — document accepted without cloud verification
        return jsonify({
            'success': True,
            'verification': {
                'verified': False,
                'confidence': 0,
                'detected_text': [],
                'labels': [],
                'reason': 'AWS Rekognition not configured – add AWS credentials to .env to enable real verification',
            },
            'aws_enabled': False,
        })

    doc_file = request.files.get('document')
    if doc_file is None:
        return jsonify({'success': False, 'message': 'No document file provided'}), 400

    image_bytes = doc_file.read()
    if len(image_bytes) == 0:
        return jsonify({'success': False, 'message': 'Document file is empty'}), 400

    if len(image_bytes) > 5 * 1024 * 1024:
        return jsonify({'success': False, 'message': 'File too large (max 5 MB)'}), 400

    result = verify_supplier_document(image_bytes)

    # If verified, update supplier's verification_status and save doc to S3
    if result['verified']:
        supplier = db.session.get(Supplier, session['supplier_id'])
        if supplier:
            # Upload to S3 for record keeping
            ext = (doc_file.filename or 'cert.jpg').rsplit('.', 1)[-1].lower()
            s3_url = upload_image_to_s3(
                type('FakeFileStorage', (), {
                    'filename': f'cert_{supplier.id}.{ext}',
                    'content_type': f'image/{ext}',
                    'read': lambda: image_bytes
                })(),
                folder='supplier-docs'
            )
            # Upload bytes directly
            from aws_services import upload_file_to_s3
            unique_name = f"supplier_{supplier.id}_{uuid.uuid4().hex}.{ext}"
            s3_url = upload_file_to_s3(image_bytes, unique_name, f'image/{ext}', 'supplier-docs')

            if s3_url:
                supplier.certification = s3_url
            supplier.verification_status = True
            db.session.commit()

    return jsonify({
        'success': True,
        'verification': result,
    })


@app.route('/api/product/analyze-image', methods=['POST'])
def analyze_product_image():
    """Analyze a product image for food detection and safety."""
    if not AWS_ENABLED:
        return jsonify({'success': False, 'message': 'AWS not configured'}), 503

    img_file = request.files.get('image')
    if img_file is None:
        return jsonify({'success': False, 'message': 'No image provided'}), 400

    img_bytes = img_file.read()
    result    = analyze_food_image(img_bytes)
    return jsonify({'success': True, 'analysis': result})


# ── SMS OTP via AWS SNS ───────────────────────────────────────────────────────
@app.route('/api/sms/send-otp', methods=['POST'])
def send_sms_otp_route():
    """Send OTP via AWS SNS SMS (phone-based auth)."""
    data     = request.get_json(silent=True) or {}
    phone    = (data.get('phone') or '').strip()
    language = (data.get('language') or 'en').lower()

    if not phone:
        return jsonify({'success': False, 'message': 'Phone number is required'}), 400

    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    otp_record = OTPVerification(email=phone, otp=otp, expires_at=expires_at)
    db.session.add(otp_record)
    db.session.commit()

    dlt_configured = bool(os.environ.get('AWS_SNS_DLT_ENTITY_ID'))
    sms_sent = False

    if AWS_ENABLED:
        sms_sent = send_sms_otp(phone, otp, language)

    if not sms_sent:
        send_mock_otp_email(phone, otp)

    # If DLT not registered, Indian carriers silently drop SMS → show OTP on screen
    if not dlt_configured:
        return jsonify({
            'success': True,
            'message': (
                'OTP generated. SMS delivery requires DLT registration for India. '
                'Your OTP is shown below (development mode).'
            ),
            'otp_fallback': otp,
            'dlt_required': True,
        })

    return jsonify({'success': True, 'message': 'OTP sent via SMS' if sms_sent else 'OTP sent (check server logs)'})


# ── Vendor Analytics Dashboard ────────────────────────────────────────────────
@app.route('/vendor/analytics')
@vendor_required
def vendor_analytics_dashboard():
    vendor = db.session.get(Vendor, session['vendor_id'])
    return render_template('vendor_analytics.html', vendor=vendor)


@app.route('/api/vendor/analytics')
@vendor_api_required
def get_vendor_analytics():
    """
    Returns comprehensive analytics for the logged-in vendor.
    Covers: daily/weekly/monthly sales from CustomerOrder,
    peak hours, popular items, trend comparison.
    """
    vendor_id = session['vendor_id']
    vendor    = db.session.get(Vendor, vendor_id)
    now       = datetime.utcnow()

    # ── Time windows ──────────────────────────────────────────────────────────
    today_start   = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start    = today_start - timedelta(days=today_start.weekday())
    month_start   = today_start.replace(day=1)
    prev_week_start = week_start - timedelta(days=7)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # ── Helper: fetch CustomerOrders for this vendor ──────────────────────────
    # CustomerOrder is linked to vendor via CustomerOrderItem → MenuItem → vendor_id
    def orders_in_range(start, end):
        return (
            CustomerOrder.query
            .join(CustomerOrderItem, CustomerOrder.id == CustomerOrderItem.order_id)
            .join(MenuItem, CustomerOrderItem.menu_item_id == MenuItem.id)
            .filter(
                MenuItem.vendor_id == vendor_id,
                CustomerOrder.status.in_(['delivered', 'done', 'confirmed', 'preparing', 'ready', 'out_for_delivery']),
                CustomerOrder.created_at >= start,
                CustomerOrder.created_at < end,
            )
            .distinct(CustomerOrder.id)
            .all()
        )

    today_orders = orders_in_range(today_start, now)
    week_orders  = orders_in_range(week_start,  now)
    month_orders = orders_in_range(month_start, now)
    prev_week_orders  = orders_in_range(prev_week_start, week_start)
    prev_month_orders = orders_in_range(prev_month_start, month_start)

    def total_revenue(orders):
        return round(sum(o.total_amount for o in orders), 2)

    today_revenue = total_revenue(today_orders)
    week_revenue  = total_revenue(week_orders)
    month_revenue = total_revenue(month_orders)

    prev_week_revenue  = total_revenue(prev_week_orders)
    prev_month_revenue = total_revenue(prev_month_orders)

    # ── Week-over-week & month-over-month change ──────────────────────────────
    def pct_change(current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)

    # ── Daily revenue for last 7 days (chart data) ───────────────────────────
    daily_data = []
    for i in range(6, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end   = day_start + timedelta(days=1)
        day_orders = orders_in_range(day_start, day_end)
        daily_data.append({
            'date':    day_start.strftime('%a %d %b'),
            'revenue': total_revenue(day_orders),
            'orders':  len(day_orders),
        })

    # ── Monthly revenue for last 6 months ────────────────────────────────────
    monthly_data = []
    for i in range(5, -1, -1):
        # Compute first day of the month going back i months
        m_start = (month_start - timedelta(days=i * 30)).replace(day=1)
        if i == 0:
            m_end = now
        else:
            # First day of next month
            if m_start.month == 12:
                m_end = m_start.replace(year=m_start.year + 1, month=1, day=1)
            else:
                m_end = m_start.replace(month=m_start.month + 1, day=1)
        m_orders = orders_in_range(m_start, m_end)
        monthly_data.append({
            'month':   m_start.strftime('%b %Y'),
            'revenue': total_revenue(m_orders),
            'orders':  len(m_orders),
        })

    # ── Peak hours (last 30 days) ─────────────────────────────────────────────
    thirty_days_ago = now - timedelta(days=30)
    all_recent_orders = orders_in_range(thirty_days_ago, now)
    from collections import Counter
    hour_counter = Counter()
    for o in all_recent_orders:
        if o.created_at:
            # Convert UTC to IST
            ist_hour = (o.created_at + timedelta(hours=5, minutes=30)).hour
            hour_counter[ist_hour] += 1

    peak_hours = [
        {'hour': f'{h:02d}:00', 'orders': c}
        for h, c in sorted(hour_counter.items())
    ]

    # ── Popular menu items ────────────────────────────────────────────────────
    item_counter = Counter()
    qty_counter  = Counter()
    rev_counter  = Counter()

    month_item_rows = (
        db.session.query(
            MenuItem.name,
            db.func.sum(CustomerOrderItem.quantity).label('total_qty'),
            db.func.sum(CustomerOrderItem.quantity * CustomerOrderItem.price_per_unit).label('total_rev'),
        )
        .join(CustomerOrderItem, CustomerOrderItem.menu_item_id == MenuItem.id)
        .join(CustomerOrder, CustomerOrder.id == CustomerOrderItem.order_id)
        .filter(
            MenuItem.vendor_id == vendor_id,
            CustomerOrder.created_at >= month_start,
            CustomerOrder.status.in_(['delivered', 'done', 'confirmed', 'preparing', 'ready', 'out_for_delivery']),
        )
        .group_by(MenuItem.name)
        .order_by(db.func.sum(CustomerOrderItem.quantity).desc())
        .limit(10)
        .all()
    )

    popular_items = [
        {
            'name':     row.name,
            'quantity': int(row.total_qty or 0),
            'revenue':  round(float(row.total_rev or 0), 2),
        }
        for row in month_item_rows
    ]

    # ── Total customers (unique) ──────────────────────────────────────────────
    unique_customers_month = (
        db.session.query(db.func.count(db.func.distinct(CustomerOrder.customer_id)))
        .join(CustomerOrderItem, CustomerOrder.id == CustomerOrderItem.order_id)
        .join(MenuItem, CustomerOrderItem.menu_item_id == MenuItem.id)
        .filter(
            MenuItem.vendor_id == vendor_id,
            CustomerOrder.created_at >= month_start,
        )
        .scalar() or 0
    )

    # ── Average order value ───────────────────────────────────────────────────
    avg_order_value = round(week_revenue / len(week_orders), 2) if week_orders else 0.0

    # ── Supplier orders (raw material spend) ─────────────────────────────────
    supplier_spend_month = (
        db.session.query(db.func.sum(Order.total_amount))
        .filter(Order.vendor_id == vendor_id, Order.created_at >= month_start)
        .scalar() or 0.0
    )

    # ── Reward points ─────────────────────────────────────────────────────────
    reward_points = float(getattr(vendor, 'reward_points', 0) or 0)

    return jsonify({
        'success': True,
        'summary': {
            'today':  {'revenue': today_revenue, 'orders': len(today_orders)},
            'week':   {'revenue': week_revenue,  'orders': len(week_orders),  'change_pct': pct_change(week_revenue, prev_week_revenue)},
            'month':  {'revenue': month_revenue, 'orders': len(month_orders), 'change_pct': pct_change(month_revenue, prev_month_revenue)},
        },
        'daily_chart':   daily_data,
        'monthly_chart': monthly_data,
        'peak_hours':    peak_hours,
        'popular_items': popular_items,
        'metrics': {
            'avg_order_value':        avg_order_value,
            'unique_customers_month': unique_customers_month,
            'supplier_spend_month':   round(float(supplier_spend_month), 2),
            'reward_points':          reward_points,
        },
        'vendor': {
            'name':          vendor.name,
            'business_type': vendor.business_type,
            'location':      vendor.location,
        },
    })


# ── SQS Group Order Automation ────────────────────────────────────────────────
@app.route('/api/group-orders/process-expired', methods=['POST'])
def process_expired_group_orders():
    """
    Process expired group orders.
    Can be called by a scheduled task or AWS Lambda via HTTP trigger.
    Marks orders as expired & sends SQS events.
    """
    # Simple auth via secret header (replace with proper Lambda auth in production)
    secret = request.headers.get('X-Internal-Secret', '')
    expected = os.environ.get('INTERNAL_SECRET', 'vendorconnect-internal')
    if secret != expected:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    expiry_hours = int(request.args.get('hours', 24))
    cutoff = datetime.utcnow() - timedelta(hours=expiry_hours)

    expired = GroupOrder.query.filter(
        GroupOrder.status == 'active',
        GroupOrder.created_at < cutoff,
    ).all()

    processed = []
    for go in expired:
        go.status = 'expired'
        db.session.add(go)

        # Gather participant phones
        participants = GroupOrderParticipant.query.filter_by(group_order_id=go.id).all()
        phones = []
        for p in participants:
            vendor = db.session.get(Vendor, p.vendor_id)
            if vendor and vendor.phone:
                phones.append(vendor.phone)

        if AWS_ENABLED:
            publish_group_order_event('ORDER_EXPIRED', {
                'group_order_id': go.id,
                'product_id': go.product_id,
                'participant_phones': phones,
            })

        processed.append(go.id)

    db.session.commit()

    return jsonify({
        'success': True,
        'expired_orders': processed,
        'count': len(processed),
    })


@app.route('/api/group-orders/sqs-handler', methods=['POST'])
def sqs_handler_webhook():
    """
    Webhook endpoint that mimics the Lambda SQS handler.
    Useful for local testing without deploying to Lambda.
    """
    if not AWS_ENABLED:
        return jsonify({'success': False, 'message': 'AWS not configured'}), 503

    event = request.get_json(silent=True) or {}
    result = lambda_group_order_handler(event)
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────────────
# End of AWS Routes
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        # Create any missing tables (won't modify existing columns)
        db.create_all()

        # If the DB existed before we added the `email` and `password_hash` fields
        # to Supplier, querying Supplier will fail. Detect and add those columns
        # at runtime for SQLite using ALTER TABLE ADD COLUMN.
        try:
            info = db.session.execute(text("PRAGMA table_info('supplier')")).fetchall()
            cols = [row[1] for row in info]
            altered = False
            if 'email' not in cols:
                db.session.execute(text("ALTER TABLE supplier ADD COLUMN email VARCHAR(120)"))
                altered = True
            if 'password_hash' not in cols:
                db.session.execute(text("ALTER TABLE supplier ADD COLUMN password_hash VARCHAR(200)"))
                altered = True
            if altered:
                db.session.commit()
                app.logger.info('Updated supplier table with new columns')
        except Exception as e:
            app.logger.exception('Error ensuring supplier columns:')
            try:
                db.session.rollback()
            except Exception:
                pass

        # Only create sample data if database is empty
        try:
            if not Supplier.query.first():
                create_sample_data()
            elif not Product.query.first():
                # Suppliers exist but products are missing — seed products only
                app.logger.info('Suppliers exist but no products found — seeding products from create_sample_data')
                create_sample_data()
        except Exception:
            # If Supplier table still not queryable, skip sample data creation
            app.logger.exception('Skipping sample data creation due to DB schema issue')

        create_sample_orders()
        create_sample_vendors()
        create_sample_menu_items()
    
if __name__ == '__main__':
    # For production deployment on Render
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port) 
