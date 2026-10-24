from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from deep_translator import GoogleTranslator
from sqlalchemy import text, inspect as sa_inspect
from PIL import Image
import imagehash
import os, uuid, requests

# Local logic module
import logic

app = Flask(__name__)
app.secret_key = 'streetsignal-hackathon-secure-key-2026'
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///streetsignal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER']                  = os.path.join(app.root_path, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH']             = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

TEXT_DUPLICATE_THRESHOLD = 0.65
TEXT_GROUP_THRESHOLD     = 0.30
PHOTO_HASH_MAX_DISTANCE  = 10

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

# ── Categories ────────────────────────────────────────────────────────────────
CATEGORIES = {
    'water':       {'label': 'Water Department',  'icon': '💧', 'color': 'blue',   'dept': 'Water Department'},
    'roads':       {'label': 'Roads & Transport',  'icon': '🚧', 'color': 'yellow', 'dept': 'Roads & Transport'},
    'sanitation':  {'label': 'Sanitation',         'icon': '🗑️', 'color': 'green',  'dept': 'Sanitation'},
    'parks':       {'label': 'Parks & Recreation', 'icon': '🌳', 'color': 'emerald','dept': 'Parks & Recreation'},
    'electricity': {'label': 'Electricity/Power',  'icon': '⚡', 'color': 'pink',   'dept': 'Electricity/Power'},
    'general':     {'label': 'General Services',   'icon': '📋', 'color': 'slate',  'dept': 'General Services'},
}

# ── Priority levels ───────────────────────────────────────────────────────────
PRIORITIES = [
    ('critical', '🚨 Critical',  'Life-threatening or immediate danger'),
    ('urgent',   '⚡ Urgent',    'Needs attention within 24 hours'),
    ('normal',   '🔶 Normal',    'Standard complaint, within a week'),
    ('low',      '🔵 Low',       'Minor issue, no rush'),
]

PRIORITY_META = {
    'critical': {'icon': '🚨', 'label': 'Critical', 'badge': 'bg-red-100 text-red-700 border-red-300',    'bar': 'bg-red-500'},
    'urgent':   {'icon': '⚡', 'label': 'Urgent',   'badge': 'bg-orange-100 text-orange-700 border-orange-300', 'bar': 'bg-orange-500'},
    'normal':   {'icon': '🔶', 'label': 'Normal',   'badge': 'bg-yellow-100 text-yellow-700 border-yellow-300', 'bar': 'bg-yellow-500'},
    'low':      {'icon': '🔵', 'label': 'Low',      'badge': 'bg-blue-100 text-blue-700 border-blue-300',   'bar': 'bg-blue-400'},
}

PRIORITY_ORDER = {'critical': 0, 'urgent': 1, 'normal': 2, 'low': 3}

# ── Supported languages ───────────────────────────────────────────────────────
LANGUAGES = [
    ('en',   '🇺🇸 English'),     ('hi',   '🇮🇳 Hindi (हिन्दी)'),
    ('ta',   '🇮🇳 Tamil (தமிழ்)'),       ('te',   '🇮🇳 Telugu (తెలుగు)'),
    ('bn',   '🇧🇩 Bengali (বাংলা)'),     ('mr',   '🇮🇳 Marathi (मराठी)'),
    ('gu',   '🇮🇳 Gujarati (ગુજરાતી)'),    ('pa',   '🇮🇳 Punjabi (ਪੰਜਾਬੀ)'),
    ('ur',   '🇵🇰 Urdu (اردو)'),        ('es',   '🇪🇸 Spanish (Español)'),
    ('fr',   '🇫🇷 French (Français)'),      ('ar',   '🇸🇦 Arabic (العربية)'),
    ('de',   '🇩🇪 German (Deutsch)'),      ('zh-CN','🇨🇳 Chinese (中文)'),
    ('ja',   '🇯🇵 Japanese (日本語)'),    ('ru',   '🇷🇺 Russian (Русский)'),
    ('pt',   '🇧🇷 Portuguese'),  ('ko',   '🇰🇷 Korean (한국어)'),
]

# ── Models ────────────────────────────────────────────────────────────────────
class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    phone      = db.Column(db.String(20), nullable=True)
    password   = db.Column(db.String(200), nullable=False)
    role       = db.Column(db.String(20), default='citizen')  # 'citizen' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active  = db.Column(db.Boolean, default=True)


class Complaint(db.Model):
    id                   = db.Column(db.Integer, primary_key=True)
    user_id              = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user_name            = db.Column(db.String(100), nullable=True)
    user_email           = db.Column(db.String(150), nullable=True)
    text                 = db.Column(db.String(500), nullable=False)
    original_text        = db.Column(db.String(500), nullable=True)
    original_lang        = db.Column(db.String(20),  nullable=True)
    original_lang_name   = db.Column(db.String(50),  nullable=True)
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)
    group_id             = db.Column(db.Integer, nullable=True)
    department           = db.Column(db.String(100), nullable=True)
    priority             = db.Column(db.String(20), default='normal', nullable=False)
    is_overdue_escalated = db.Column(db.Boolean, default=False, nullable=False)
    resolved             = db.Column(db.Boolean, default=False, nullable=False)
    resolved_at          = db.Column(db.DateTime, nullable=True)
    photo_filename       = db.Column(db.String(200), nullable=True)
    photo_hash           = db.Column(db.String(100), nullable=True)
    location_lat         = db.Column(db.Float, nullable=True)
    location_lng         = db.Column(db.Float, nullable=True)
    location_address     = db.Column(db.String(300), nullable=True)


def migrate_db():
    new_cols = {
        'user_id':              'ALTER TABLE complaint ADD COLUMN user_id INTEGER',
        'user_name':            'ALTER TABLE complaint ADD COLUMN user_name VARCHAR(100)',
        'user_email':           'ALTER TABLE complaint ADD COLUMN user_email VARCHAR(150)',
        'original_text':        'ALTER TABLE complaint ADD COLUMN original_text VARCHAR(500)',
        'original_lang':        'ALTER TABLE complaint ADD COLUMN original_lang VARCHAR(20)',
        'original_lang_name':   'ALTER TABLE complaint ADD COLUMN original_lang_name VARCHAR(50)',
        'priority':             "ALTER TABLE complaint ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'normal'",
        'is_overdue_escalated': 'ALTER TABLE complaint ADD COLUMN is_overdue_escalated BOOLEAN NOT NULL DEFAULT 0',
        'resolved':             'ALTER TABLE complaint ADD COLUMN resolved BOOLEAN NOT NULL DEFAULT 0',
        'resolved_at':          'ALTER TABLE complaint ADD COLUMN resolved_at DATETIME',
        'photo_filename':       'ALTER TABLE complaint ADD COLUMN photo_filename VARCHAR(200)',
        'photo_hash':           'ALTER TABLE complaint ADD COLUMN photo_hash VARCHAR(100)',
        'location_lat':         'ALTER TABLE complaint ADD COLUMN location_lat FLOAT',
        'location_lng':         'ALTER TABLE complaint ADD COLUMN location_lng FLOAT',
        'location_address':     'ALTER TABLE complaint ADD COLUMN location_address VARCHAR(300)',
    }
    with db.engine.connect() as conn:
        existing = [c['name'] for c in sa_inspect(db.engine).get_columns('complaint')]
        for col, sql in new_cols.items():
            if col not in existing:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                except Exception as e:
                    print(f"Migration note for {col}: {e}")


with app.app_context():
    db.create_all()
    migrate_db()
    # Seed default municipal admin if doesn't exist
    admin_user = User.query.filter_by(email='admin@streetsignal.com').first()
    if not admin_user:
        admin_user = User(
            name='Municipal Authority',
            email='admin@streetsignal.com',
            phone='+1 800-CITY-GOV',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Default admin created: admin@streetsignal.com / admin123")


# ── Auth Helpers ──────────────────────────────────────────────────────────────
def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return db.session.get(User, user_id)
    return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user():
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect('/login?error=admin_required')
        if user.role != 'admin':
            return redirect('/citizen?error=unauthorized')
        return f(*args, **kwargs)
    return decorated

def citizen_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect('/login')
        if user.role == 'admin':
            return redirect('/admin')
        return f(*args, **kwargs)
    return decorated


# ── 72 Hours Auto-Escalation Engine ───────────────────────────────────────────
def check_and_escalate_overdue():
    cutoff = datetime.utcnow() - timedelta(hours=72)
    overdue_complaints = Complaint.query.filter(
        Complaint.resolved == False,
        Complaint.created_at <= cutoff
    ).all()

    escalated_count = 0
    for c in overdue_complaints:
        if c.priority != 'critical' or not c.is_overdue_escalated:
            c.priority = 'critical'
            c.is_overdue_escalated = True
            escalated_count += 1

    if escalated_count > 0:
        db.session.commit()

    return len(overdue_complaints)


# ── Logic & Media Helpers ─────────────────────────────────────────────────────
def allowed_file(f): 
    return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compute_photo_hash(path):
    try:
        return str(imagehash.phash(Image.open(path).convert('RGB')))
    except: 
        return None

def is_duplicate_photo(new_hash, complaints):
    if not new_hash: return False, None
    try:
        h1 = imagehash.hex_to_hash(new_hash)
        for c in complaints:
            if c.photo_hash:
                if (h1 - imagehash.hex_to_hash(c.photo_hash)) <= PHOTO_HASH_MAX_DISTANCE:
                    return True, c.group_id
    except: 
        pass
    return False, None

def is_duplicate_text(new_text, complaints):
    if not complaints: return False, None
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import re
        def clean(t): return re.sub(r'[^\w\s]', '', t.lower()).strip()
        data   = [{'id': c.id, 'text': c.text} for c in complaints]
        corpus = [clean(new_text)] + [clean(d['text']) for d in data]
        vecs   = TfidfVectorizer(stop_words='english').fit_transform(corpus).toarray()
        scores = cosine_similarity(vecs[0:1], vecs[1:])[0]
        idx, score = scores.argmax(), scores.max()
        if score >= TEXT_DUPLICATE_THRESHOLD:
            c = Complaint.query.get(data[idx]['id'])
            return True, c.group_id if c else None
    except: 
        pass
    return False, None

def translate_to_english(text, src):
    if src == 'en' or not text.strip(): return text, True
    try:
        t = GoogleTranslator(source=src, target='en').translate(text)
        return t or text, True
    except: 
        return text, False

def reverse_geocode(lat, lng):
    try:
        r = requests.get('https://nominatim.openstreetmap.org/reverse',
                         params={'lat': lat, 'lon': lng, 'format': 'json'},
                         headers={'User-Agent': 'StreetSignal/1.0'}, timeout=5)
        if r.status_code == 200:
            return r.json().get('display_name', f'{lat:.4f}, {lng:.4f}')
    except: 
        pass
    return f'{lat:.4f}, {lng:.4f}'

def dept_to_slug(dept):
    for slug, meta in CATEGORIES.items():
        if meta['dept'] == dept:
            return slug
    return 'general'


def build_groups(complaints):
    now = datetime.utcnow()
    grouped = {}
    for c in complaints:
        gid = c.group_id
        if gid not in grouped:
            grouped[gid] = {
                'group_id':             gid,
                'main_text':            c.text,
                'department':           c.department,
                'dept_slug':            dept_to_slug(c.department),
                'priority':             c.priority or 'normal',
                'priority_meta':        PRIORITY_META.get(c.priority or 'normal', PRIORITY_META['normal']),
                'count':                0,
                'reports':              [],
                'created_at_dt':        c.created_at,
                'created_at':           c.created_at.strftime('%b %d, %Y %I:%M %p'),
                'resolved':             c.resolved,
                'resolved_at':          c.resolved_at.strftime('%b %d, %Y %I:%M %p') if c.resolved_at else None,
                'photo_filename':       c.photo_filename,
                'location_address':     c.location_address,
                'location_lat':         c.location_lat,
                'location_lng':         c.location_lng,
                'primary_reporter':     c.user_name or 'Citizen',
                'primary_reporter_email': c.user_email or 'Anonymous',
                'is_overdue':           False,
                'hours_pending':        0,
            }
        g = grouped[gid]
        g['count'] += 1
        g['reports'].append({
            'text':          c.text,
            'original_text': c.original_text,
            'lang_name':     c.original_lang_name,
            'photo':         c.photo_filename,
            'address':       c.location_address,
            'reporter':      c.user_name or 'Citizen',
            'reporter_email': c.user_email or 'Anonymous',
            'created_at':    c.created_at.strftime('%b %d, %I:%M %p'),
        })

        if c.created_at < g['created_at_dt']:
            g['created_at_dt'] = c.created_at
            g['created_at']    = c.created_at.strftime('%b %d, %Y %I:%M %p')

        if PRIORITY_ORDER.get(c.priority, 2) < PRIORITY_ORDER.get(g['priority'], 2):
            g['priority']      = c.priority
            g['priority_meta'] = PRIORITY_META.get(c.priority, PRIORITY_META['normal'])

        if c.resolved:
            g['resolved'] = True
            if c.resolved_at:
                g['resolved_at'] = c.resolved_at.strftime('%b %d, %Y %I:%M %p')

        if c.photo_filename and not g['photo_filename']:
            g['photo_filename'] = c.photo_filename

    for g in grouped.values():
        age_hours = int((now - g['created_at_dt']).total_seconds() // 3600)
        g['hours_pending'] = age_hours
        if not g['resolved'] and age_hours >= 72:
            g['is_overdue'] = True
            g['priority']   = 'critical'
            g['priority_meta'] = PRIORITY_META['critical']

    def sort_order(x):
        if x['resolved']:
            return (10, -x['count'])
        if x['is_overdue']:
            return (0, -x['hours_pending'], -x['count'])
        prio_rank = PRIORITY_ORDER.get(x['priority'], 2) + 1
        return (prio_rank, -x['count'])

    return sorted(grouped.values(), key=sort_order)


def admin_global_stats():
    all_c = Complaint.query.all()
    groups = build_groups(all_c)
    resolved = sum(1 for g in groups if g['resolved'])
    overdue  = sum(1 for g in groups if not g['resolved'] and g.get('is_overdue'))
    critical = sum(1 for g in groups if not g['resolved'] and g['priority'] == 'critical')
    return {
        'total_groups': len(groups),
        'open':         len(groups) - resolved,
        'resolved':     resolved,
        'overdue_72h':  overdue,
        'critical':     critical,
        'total_reports': len(all_c),
    }


def admin_category_stats():
    stats = {}
    for slug, meta in CATEGORIES.items():
        complaints = Complaint.query.filter_by(department=meta['dept']).all()
        groups     = build_groups(complaints)
        resolved   = sum(1 for g in groups if g['resolved'])
        overdue    = sum(1 for g in groups if not g['resolved'] and g.get('is_overdue'))
        critical   = sum(1 for g in groups if not g['resolved'] and g['priority'] == 'critical')
        urgent     = sum(1 for g in groups if not g['resolved'] and g['priority'] == 'urgent')
        stats[slug] = {
            **meta,
            'slug':        slug,
            'groups':      len(groups),
            'open':        len(groups) - resolved,
            'resolved':    resolved,
            'overdue_72h': overdue,
            'reports':     len(complaints),
            'critical':    critical,
            'urgent':      urgent,
        }
    return stats


# ── Routes: Auth ──────────────────────────────────────────────────────────────
@app.route('/')
def home():
    user = get_current_user()
    if not user:
        return redirect('/login')
    if user.role == 'admin':
        return redirect('/admin')
    return redirect('/citizen')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            if user.role == 'admin':
                return redirect('/admin')
            return redirect('/citizen')

        return render_template('login.html', error='Invalid email or password. Please try again.')

    error = request.args.get('error')
    error_msg = None
    if error == 'admin_required':
        error_msg = 'Municipal administrative credentials required for portal access.'
    elif error == 'unauthorized':
        error_msg = 'Access restricted to authorized personnel.'

    return render_template('login.html', error=error_msg)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        phone    = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        confirm  = request.form.get('confirm_password', '').strip()

        if not name or not email or not password:
            return render_template('register.html', error='Please fill out all required fields.')

        if password != confirm:
            return render_template('register.html', error='Passwords do not match.')

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='An account with this email already exists. Please log in.')

        new_user = User(
            name=name,
            email=email,
            phone=phone,
            password=generate_password_hash(password),
            role='citizen'
        )
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        return redirect('/citizen')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ── Routes: Citizen Portal ────────────────────────────────────────────────────
@app.route('/citizen')
@citizen_required
def citizen_dashboard():
    user = get_current_user()
    duplicate_type = request.args.get('duplicate')
    error          = request.args.get('error')

    my_complaints = Complaint.query.filter_by(user_id=user.id)\
                                   .order_by(Complaint.created_at.desc()).all()

    my_group_ids = list(set([c.group_id for c in my_complaints if c.group_id]))

    all_group_complaints = []
    if my_group_ids:
        all_group_complaints = Complaint.query.filter(Complaint.group_id.in_(my_group_ids)).all()

    my_groups = build_groups(all_group_complaints)

    total_filed = len(my_complaints)
    resolved_count = sum(1 for g in my_groups if g['resolved'])
    open_count     = len(my_groups) - resolved_count
    overdue_count  = sum(1 for g in my_groups if not g['resolved'] and g.get('is_overdue'))

    return render_template('citizen/dashboard.html',
                           user=user,
                           groups=my_groups,
                           total_filed=total_filed,
                           open_count=open_count,
                           resolved_count=resolved_count,
                           overdue_count=overdue_count,
                           languages=LANGUAGES,
                           priorities=PRIORITIES,
                           categories=CATEGORIES,
                           duplicate_type=duplicate_type,
                           error=error)


@app.route('/citizen/submit', methods=['POST'])
@citizen_required
def citizen_submit():
    user = get_current_user()

    raw_text   = request.form.get('complaint', '').strip()
    src_lang   = request.form.get('language', 'en')
    lat        = request.form.get('lat', '').strip()
    lng        = request.form.get('lng', '').strip()
    priority   = request.form.get('priority', 'normal')
    file       = request.files.get('photo')

    has_photo    = bool(file and file.filename and allowed_file(file.filename))
    has_location = bool(lat and lng)

    if not has_photo and not has_location:
        return redirect('/citizen?error=no_both')
    if not has_photo:
        return redirect('/citizen?error=no_photo')
    if not has_location:
        return redirect('/citizen?error=no_location')
    if not raw_text:
        return redirect('/citizen')

    # Save photo
    ext       = file.filename.rsplit('.', 1)[1].lower()
    safe      = f'{uuid.uuid4().hex}.{ext}'
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe)
    file.save(save_path)
    new_hash  = compute_photo_hash(save_path)

    # Translation
    lang_name = dict([(k, v.split(' ', 1)[1]) for k, v in LANGUAGES]).get(src_lang, src_lang)
    if src_lang == 'en':
        english_text  = raw_text
        original_text = None
        lang_name     = None
        src_lang      = None
    else:
        english_text, _ = translate_to_english(raw_text, src_lang)
        original_text   = raw_text

    all_existing = Complaint.query.all()

    # Check duplicate photo
    photo_dupe, _ = is_duplicate_photo(new_hash, all_existing)
    if photo_dupe:
        os.remove(save_path)
        return redirect('/citizen?duplicate=photo')

    # Check duplicate text
    text_dupe, _ = is_duplicate_text(english_text, all_existing)
    if text_dupe:
        os.remove(save_path)
        return redirect('/citizen?duplicate=text')

    # Reverse Geocode
    location_lat = location_lng = location_address = None
    try:
        location_lat     = float(lat)
        location_lng     = float(lng)
        location_address = reverse_geocode(location_lat, location_lng)
    except: 
        pass

    # AI Grouping & Department Routing
    existing_data = [{'id': c.id, 'text': c.text} for c in all_existing]
    matched_id    = logic.group_complaints(english_text, existing_data)
    dept          = logic.suggest_department(english_text)

    group_id = None
    if matched_id:
        orig = db.session.get(Complaint, matched_id)
        if orig: 
            group_id = orig.group_id

    new_c = Complaint(
        user_id=user.id,
        user_name=user.name,
        user_email=user.email,
        text=english_text,
        original_text=original_text,
        original_lang=src_lang,
        original_lang_name=lang_name,
        group_id=group_id,
        department=dept,
        priority=priority,
        photo_filename=safe,
        photo_hash=new_hash,
        location_lat=location_lat,
        location_lng=location_lng,
        location_address=location_address,
    )
    db.session.add(new_c)
    db.session.commit()

    if group_id is None:
        new_c.group_id = new_c.id
        db.session.commit()

    return redirect('/citizen?success=1')


# ── Routes: Municipal Admin Portal ────────────────────────────────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    user = get_current_user()
    overdue_count = check_and_escalate_overdue()

    gs   = admin_global_stats()
    cats = admin_category_stats()

    all_complaints = Complaint.query.all()
    all_groups = build_groups(all_complaints)
    overdue_and_critical = [g for g in all_groups if not g['resolved'] and (g.get('is_overdue') or g['priority'] == 'critical')][:8]

    return render_template('admin/dashboard.html',
                           user=user,
                           gs=gs,
                           cats=cats,
                           overdue_count=overdue_count,
                           urgent_groups=overdue_and_critical,
                           categories=CATEGORIES)


@app.route('/admin/category/<slug>')
@admin_required
def admin_category(slug):
    user = get_current_user()
    if slug not in CATEGORIES:
        return redirect('/admin')

    check_and_escalate_overdue()
    meta          = CATEGORIES[slug]
    show_resolved = request.args.get('show_resolved', 'false') == 'true'
    filter_prio   = request.args.get('priority', 'all')

    complaints = Complaint.query.filter_by(department=meta['dept'])\
                                .order_by(Complaint.created_at.desc()).all()
    all_groups = build_groups(complaints)

    if not show_resolved:
        groups = [g for g in all_groups if not g['resolved']]
    else:
        groups = all_groups

    if filter_prio != 'all':
        groups = [g for g in groups if g['priority'] == filter_prio]

    resolved_count = sum(1 for g in all_groups if g['resolved'])
    open_count     = len(all_groups) - resolved_count
    overdue_count  = sum(1 for g in all_groups if not g['resolved'] and g.get('is_overdue'))

    return render_template('admin/category.html',
                           user=user,
                           slug=slug,
                           meta=meta,
                           groups=groups,
                           open_count=open_count,
                           resolved_count=resolved_count,
                           overdue_count=overdue_count,
                           show_resolved=show_resolved,
                           filter_prio=filter_prio,
                           priority_meta=PRIORITY_META,
                           categories=CATEGORIES)


@app.route('/admin/logs')
@admin_required
def admin_logs():
    user = get_current_user()
    check_and_escalate_overdue()

    dept_filter   = request.args.get('dept', 'all')
    status_filter = request.args.get('status', 'all')
    search_query  = request.args.get('q', '').strip().lower()

    query = Complaint.query

    if dept_filter != 'all':
        dept_name = CATEGORIES.get(dept_filter, {}).get('dept')
        if dept_name:
            query = query.filter_by(department=dept_name)

    if status_filter == 'open':
        query = query.filter_by(resolved=False)
    elif status_filter == 'resolved':
        query = query.filter_by(resolved=True)

    complaints = query.order_by(Complaint.created_at.desc()).all()

    if search_query:
        complaints = [c for c in complaints if search_query in c.text.lower() 
                      or (c.user_name and search_query in c.user_name.lower())
                      or (c.location_address and search_query in c.location_address.lower())]

    now = datetime.utcnow()
    logs_data = []
    for c in complaints:
        age_hours = int((now - c.created_at).total_seconds() // 3600)
        is_overdue = (not c.resolved) and (age_hours >= 72)
        logs_data.append({
            'complaint': c,
            'age_hours': age_hours,
            'is_overdue': is_overdue,
            'dept_slug': dept_to_slug(c.department),
            'priority_meta': PRIORITY_META.get(c.priority, PRIORITY_META['normal']),
        })

    return render_template('admin/logs.html',
                           user=user,
                           logs=logs_data,
                           total_count=len(logs_data),
                           categories=CATEGORIES,
                           dept_filter=dept_filter,
                           status_filter=status_filter,
                           search_query=search_query)


@app.route('/admin/resolve/<int:group_id>', methods=['POST'])
@admin_required
def admin_resolve(group_id):
    now = datetime.utcnow()
    for c in Complaint.query.filter_by(group_id=group_id).all():
        c.resolved = True
        c.resolved_at = now
    db.session.commit()
    return redirect(request.referrer or '/admin')


@app.route('/admin/reopen/<int:group_id>', methods=['POST'])
@admin_required
def admin_reopen(group_id):
    for c in Complaint.query.filter_by(group_id=group_id).all():
        c.resolved = False
        c.resolved_at = None
    db.session.commit()
    return redirect(request.referrer or '/admin')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=True, port=port)
