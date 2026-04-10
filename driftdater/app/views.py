"""
app/views.py
------------
DriftDater REST API — all routes defined on a Flask Blueprint.

Authentication
--------------
All protected endpoints use JWT (JSON Web Tokens) rather than server-side
sessions.  This allows each browser tab to hold a completely independent
identity by storing its token in `sessionStorage` (tab-isolated), solving
the problem of multiple accounts in the same browser overwriting each other.

Token Flow
----------
1. Client calls POST /api/v1/login or /api/v1/register.
2. Server returns a signed JWT valid for 30 days.
3. Client stores the token in sessionStorage (NOT localStorage — tab-isolated).
4. Every subsequent request includes:  Authorization: Bearer <token>
5. The @token_required decorator validates the token and injects the user into
   Flask's request-scoped `g` object via get_current_user().

Blueprint
---------
All routes are registered on the `api` Blueprint which is imported and
registered against the Flask app in app/__init__.py.  This avoids the circular
import that would occur if routes imported the `app` object directly.

Matching Algorithm  (compute_match_score)
-----------------------------------------
Returns a 0–100 score for a candidate relative to the current user:
  - Shared interests  : up to 50 pts  (Jaccard similarity of interest sets)
  - Age fit           : up to 20 pts  (candidate age within user's preference range)
  - Location proximity: up to 30 pts  (Haversine distance, scaled by max_distance)

Block Enforcement
-----------------
is_blocked_between() is called before any messaging endpoint.  A block
prevents both users from sending or loading messages for as long as it is
active.  Blocked users are also excluded from Discover, Matches, Search, and
the Conversations list.
"""

from flask import Blueprint, request, jsonify, send_from_directory
from flask_login import logout_user
from werkzeug.utils import secure_filename
from datetime import datetime, timezone, timedelta
import os
import math
import jwt
from functools import wraps

from app import db
from app.models import User, Interest, Swipe, Message, Favorite, Report

# All routes are attached to this blueprint, registered in create_app()
api = Blueprint('api', __name__)

# Permitted image extensions for profile photo uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


# ─── JWT HELPERS ──────────────────────────────────────────────────────────────

def make_token(user_id):
    """
    Create a signed JWT for the given user, valid for 30 days.

    Parameters
    ----------
    user_id : int
        The primary key of the user to encode.

    Returns
    -------
    str : Encoded JWT string.
    """
    from flask import current_app
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=30),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def token_required(f):
    """
    Route decorator that validates the JWT in the Authorization header.

    Reads the `Authorization: Bearer <token>` header, decodes the JWT, looks
    up the user, and stores the user object in Flask's request-scoped `g` so
    it can be retrieved by get_current_user() inside the view.

    Returns HTTP 401 if the token is missing, expired, or invalid.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app, g
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
        if not token:
            return jsonify(error='Authentication required'), 401
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify(error='User not found'), 401
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify(error='Token expired, please log in again'), 401
        except jwt.InvalidTokenError:
            return jsonify(error='Invalid token'), 401
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """
    Retrieve the authenticated user stored by @token_required.

    Returns
    -------
    User : The authenticated User ORM object for the current request.
    """
    from flask import g
    return g.get('current_user')


# ─── UTILITY FUNCTIONS ────────────────────────────────────────────────────────

def allowed_file(filename):
    """Return True if the filename has a permitted image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth.

    Uses the Haversine formula with Earth radius 6371 km.

    Parameters
    ----------
    lat1, lon1 : float  Coordinates of point A in decimal degrees.
    lat2, lon2 : float  Coordinates of point B in decimal degrees.

    Returns
    -------
    float : Distance in kilometres.
    """
    R    = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a    = (math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_match_score(user, candidate):
    """
    Compute a 0–100 compatibility score between two users.

    Scoring Breakdown
    -----------------
    Shared interests  : up to 50 pts
        Jaccard similarity: |intersection| / |union| * 50
    Age preference fit: up to 20 pts
        Full 20 pts if the candidate's age falls within the user's stated range.
    Location proximity: up to 30 pts
        Linearly decays from 30 pts (same location) to 0 pts (at max_distance).
        Zero if either user has no coordinates stored.

    Parameters
    ----------
    user      : User  The logged-in user (whose preferences apply).
    candidate : User  The profile being evaluated.

    Returns
    -------
    float : Rounded score in the range [0, 100].
    """
    score = 0

    # Shared interests (Jaccard similarity × 50)
    u_interests = set(i.name for i in user.interests)
    c_interests = set(i.name for i in candidate.interests)
    shared      = u_interests & c_interests
    if u_interests or c_interests:
        score += (len(shared) / max(len(u_interests | c_interests), 1)) * 50

    # Age preference fit
    if candidate.age:
        if user.age_min_pref <= candidate.age <= user.age_max_pref:
            score += 20

    # Location proximity
    if all([user.latitude, user.longitude, candidate.latitude, candidate.longitude]):
        dist = haversine(user.latitude, user.longitude, candidate.latitude, candidate.longitude)
        if dist <= user.max_distance:
            score += 30 * (1 - dist / user.max_distance)

    return round(score, 1)


def get_blocked_ids(user_id):
    """
    Return the set of user IDs that have a block relationship with user_id.

    Blocks are bidirectional: if user A blocks user B, both A and B should be
    invisible to each other.  This function returns all IDs involved in any
    active block record where user_id is either the reporter or the reported.

    Parameters
    ----------
    user_id : int

    Returns
    -------
    set[int] : IDs to exclude from feeds, matches, and conversations.
    """
    blocked = Report.query.filter(
        ((Report.reporter_id == user_id) | (Report.reported_id == user_id)),
        Report.is_block == True
    ).all()
    ids = set()
    for r in blocked:
        ids.add(r.reporter_id)
        ids.add(r.reported_id)
    ids.discard(user_id)   # Never exclude the user from their own results
    return ids


def is_mutual_match(id_a, id_b):
    """
    Return True if both users have an active 'like' swipe toward each other.

    Parameters
    ----------
    id_a, id_b : int  User primary keys.

    Returns
    -------
    bool
    """
    a_likes_b = Swipe.query.filter_by(swiper_id=id_a, swiped_id=id_b, action='like').first()
    b_likes_a = Swipe.query.filter_by(swiper_id=id_b, swiped_id=id_a, action='like').first()
    return bool(a_likes_b and b_likes_a)


def is_blocked_between(id_a, id_b):
    """
    Return True if an active block exists between the two users in either direction.

    Used by messaging endpoints to prevent communication while a block is active.

    Parameters
    ----------
    id_a, id_b : int  User primary keys.

    Returns
    -------
    bool
    """
    return bool(Report.query.filter(
        ((Report.reporter_id == id_a) & (Report.reported_id == id_b)) |
        ((Report.reporter_id == id_b) & (Report.reported_id == id_a)),
        Report.is_block == True
    ).first())


# ─── AUTH ENDPOINTS ───────────────────────────────────────────────────────────

@api.route('/api/v1/register', methods=['POST'])
def register():
    """
    Register a new user account.

    Request Body (JSON)
    -------------------
    email        : str  (required, must be unique)
    username     : str  (required, must be unique)
    password     : str  (required, min 6 chars recommended)
    first_name   : str  (required)
    last_name    : str  (required)
    date_of_birth: str  (optional, YYYY-MM-DD)
    gender       : str  (optional)
    looking_for  : str  (optional, defaults to 'any')

    Responses
    ---------
    201 : { token, user }  — Account created, JWT returned.
    400 : Required field missing or invalid date format.
    409 : Email or username already taken.
    """
    data = request.get_json()
    if not data:
        return jsonify(error='No data provided'), 400
    for field in ['email', 'username', 'password', 'first_name', 'last_name']:
        if not data.get(field):
            return jsonify(error=f'{field} is required'), 400
    if User.query.filter_by(email=data['email'].lower().strip()).first():
        return jsonify(error='Email already registered'), 409
    if User.query.filter_by(username=data['username'].strip()).first():
        return jsonify(error='Username already taken'), 409
    dob = None
    if data.get('date_of_birth'):
        try:
            dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify(error='Invalid date format, use YYYY-MM-DD'), 400
    user = User(
        email=data['email'].lower().strip(),
        username=data['username'].strip(),
        first_name=data['first_name'].strip(),
        last_name=data['last_name'].strip(),
        date_of_birth=dob,
        gender=data.get('gender'),
        looking_for=data.get('looking_for', 'any'),
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    token = make_token(user.id)
    return jsonify(message='Registration successful', token=token,
                   user=user.to_dict(include_private=True)), 201


@api.route('/api/v1/login', methods=['POST'])
def login():
    """
    Authenticate a user and return a JWT.

    Request Body (JSON)
    -------------------
    email    : str
    password : str

    Responses
    ---------
    200 : { token, user }
    400 : Missing fields.
    401 : Invalid credentials.
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify(error='Email and password required'), 400
    user = User.query.filter_by(email=data['email'].lower().strip()).first()
    if not user or not user.check_password(data['password']):
        return jsonify(error='Invalid email or password'), 401
    token = make_token(user.id)
    return jsonify(message='Login successful', token=token,
                   user=user.to_dict(include_private=True)), 200


@api.route('/api/v1/logout', methods=['POST'])
def logout():
    """
    Logout endpoint (stateless).

    JWT tokens are stateless — the server has no session to destroy.
    The client is responsible for deleting the token from sessionStorage.
    This endpoint exists as a conventional hook for any future token
    blacklisting or audit logging.

    Responses
    ---------
    200 : { message }
    """
    return jsonify(message='Logged out successfully'), 200


@api.route('/api/v1/auth/status', methods=['GET'])
@token_required
def auth_status():
    """
    Verify the current JWT and return the authenticated user's profile.

    Called on every page load by the Vue auth store to restore session state.

    Responses
    ---------
    200 : { authenticated: true, user }
    401 : Token missing, expired, or invalid (handled by @token_required).
    """
    cu = get_current_user()
    return jsonify(authenticated=True, user=cu.to_dict(include_private=True)), 200


# ─── PROFILE ENDPOINTS ────────────────────────────────────────────────────────

@api.route('/api/v1/profiles/<int:user_id>', methods=['GET'])
@token_required
def get_profile(user_id):
    """
    Retrieve a user's profile.

    Private fields (email, preferences, coordinates) are included only when
    the requesting user is viewing their own profile.

    Responses
    ---------
    200 : { user }
    401 : Not authenticated.
    404 : User not found.
    """
    cu   = get_current_user()
    user = User.query.get_or_404(user_id)
    return jsonify(user=user.to_dict(include_private=(user.id == cu.id))), 200


@api.route('/api/v1/profiles/<int:user_id>', methods=['PUT'])
@token_required
def update_profile(user_id):
    """
    Update the current user's profile.

    Only the owner may update their own profile (403 if user_id != token user).
    All updatable fields are optional — only provided fields are changed.
    Interests are replaced wholesale when supplied.

    Request Body (JSON)  — all fields optional
    -------------------------------------------
    first_name, last_name, bio, location, latitude, longitude,
    occupation, education, is_public, age_min_pref, age_max_pref,
    max_distance, looking_for, gender, date_of_birth,
    interests : list[str]

    Responses
    ---------
    200 : { user }  Updated profile with private fields.
    400 : Invalid date format.
    403 : Attempting to update another user's profile.
    404 : User not found.
    """
    cu = get_current_user()
    if cu.id != user_id:
        return jsonify(error='Unauthorized'), 403
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    for field in ['first_name', 'last_name', 'bio', 'location', 'latitude', 'longitude',
                  'occupation', 'education', 'is_public', 'age_min_pref', 'age_max_pref',
                  'max_distance', 'looking_for', 'gender']:
        if field in data:
            setattr(user, field, data[field])
    if 'date_of_birth' in data:
        try:
            user.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify(error='Invalid date format'), 400
    if 'interests' in data:
        # Replace all interests — look up or create each tag
        user.interests = []
        for name in data['interests'][:15]:   # Cap at 15 interests
            name     = name.strip().lower()
            interest = Interest.query.filter_by(name=name).first()
            if not interest:
                interest = Interest(name=name)
                db.session.add(interest)
            user.interests.append(interest)
    db.session.commit()
    return jsonify(user=user.to_dict(include_private=True)), 200


@api.route('/api/v1/profiles/<int:user_id>/photo', methods=['POST'])
@token_required
def upload_photo(user_id):
    """
    Upload a profile photo for the current user.

    Saves the file to the uploads/ directory with a unique filename and
    updates the user's profile_photo field.  Accepted types: png, jpg, jpeg,
    gif, webp.  Maximum file size enforced by MAX_CONTENT_LENGTH in config.

    Request
    -------
    multipart/form-data with field `photo`.

    Responses
    ---------
    200 : { photo: filename, message }
    400 : No file provided or invalid type.
    403 : Attempting to update another user's photo.
    """
    from flask import current_app
    cu = get_current_user()
    if cu.id != user_id:
        return jsonify(error='Unauthorized'), 403
    if 'photo' not in request.files:
        return jsonify(error='No file provided'), 400
    file = request.files['photo']
    if not file or not allowed_file(file.filename):
        return jsonify(error='Invalid file type'), 400
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    ext      = file.filename.rsplit('.', 1)[1].lower()
    filename = secure_filename(f"user_{user_id}_{int(datetime.utcnow().timestamp())}.{ext}")
    file.save(os.path.join(upload_dir, filename))
    cu.profile_photo = filename
    db.session.commit()
    return jsonify(photo=filename, message='Photo uploaded'), 200


@api.route('/api/v1/uploads/<filename>', methods=['GET'])
def serve_upload(filename):
    """
    Serve an uploaded profile photo by filename.

    Responses
    ---------
    200 : Image file.
    404 : File not found.
    """
    from flask import current_app
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads')
    return send_from_directory(os.path.abspath(upload_dir), filename)


# ─── INTERESTS ENDPOINT ───────────────────────────────────────────────────────

@api.route('/api/v1/interests', methods=['GET'])
def get_interests():
    """
    Return all interest tags in alphabetical order.

    Used by the profile editor to populate interest suggestions.

    Responses
    ---------
    200 : { interests: [{ id, name }] }
    """
    interests = Interest.query.order_by(Interest.name).all()
    return jsonify(interests=[i.to_dict() for i in interests]), 200


# ─── DISCOVERY ENDPOINTS ──────────────────────────────────────────────────────

@api.route('/api/v1/discover', methods=['GET'])
@token_required
def discover():
    """
    Return profiles the current user has not yet swiped on.

    Excludes: already-swiped profiles, blocked users, the user themselves,
    and private profiles.  Applies optional query-string filters and sorts
    by match score (default) or newest first.

    Query Parameters
    ----------------
    min_age  : int    Minimum candidate age.
    max_age  : int    Maximum candidate age.
    location : str    Case-insensitive substring match on location field.
    interest : str    Case-insensitive exact match on one interest name.
    sort     : str    'score' (default) or 'newest'.

    Responses
    ---------
    200 : { profiles: [user + match_score] }
    """
    cu       = get_current_user()
    blocked  = get_blocked_ids(cu.id)
    swiped_ids = {s.swiped_id for s in cu.swipes_sent.all()}
    exclude  = swiped_ids | blocked | {cu.id}
    candidates = User.query.filter(User.id.notin_(exclude), User.is_public == True).all()

    min_age         = request.args.get('min_age',  type=int)
    max_age         = request.args.get('max_age',  type=int)
    location_filter = request.args.get('location', '')
    interest_filter = request.args.get('interest', '')
    sort_by         = request.args.get('sort',     'score')

    results = []
    for c in candidates:
        if min_age and c.age and c.age < min_age: continue
        if max_age and c.age and c.age > max_age: continue
        if location_filter and c.location and location_filter.lower() not in c.location.lower(): continue
        if interest_filter and interest_filter.lower() not in [i.name.lower() for i in c.interests]: continue
        d = c.to_dict()
        d['match_score'] = compute_match_score(cu, c)
        results.append(d)

    results.sort(key=lambda x: x['created_at'] if sort_by == 'newest' else -x['match_score'])
    return jsonify(profiles=results), 200


@api.route('/api/v1/matches', methods=['GET'])
@token_required
def get_matches():
    """
    Return all mutual matches for the current user.

    A mutual match exists when both users have a 'like' swipe toward each
    other.  Blocked users are excluded even if a mutual like exists.
    Results are sorted by match score descending.

    Responses
    ---------
    200 : { matches: [user + match_score], count: int }
    """
    cu           = get_current_user()
    blocked      = get_blocked_ids(cu.id)
    liked_ids    = {s.swiped_id for s in cu.swipes_sent.filter_by(action='like').all()}
    liked_me_ids = {s.swiper_id for s in cu.swipes_received.filter_by(action='like').all()}
    mutual       = (liked_ids & liked_me_ids) - blocked
    matches      = []
    for uid in mutual:
        user = User.query.get(uid)
        if user:
            d = user.to_dict()
            d['match_score'] = compute_match_score(cu, user)
            matches.append(d)
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(matches=matches, count=len(matches)), 200


@api.route('/api/v1/swipe', methods=['POST'])
@token_required
def swipe():
    """
    Record a swipe action (like, dislike, or pass) on a target user.

    If the action is 'like' and the target has also liked the current user,
    `is_match` is returned as True so the frontend can show a match notification.
    Re-swiping an already-swiped profile updates the existing record.

    Request Body (JSON)
    -------------------
    target_id : int   ID of the profile being swiped.
    action    : str   'like' | 'dislike' | 'pass'

    Responses
    ---------
    200 : { action, is_match: bool, target: user }
    400 : Missing or invalid fields.
    400 : Attempting to swipe on yourself.
    404 : Target user not found.
    """
    cu        = get_current_user()
    data      = request.get_json()
    target_id = data.get('target_id')
    action    = data.get('action')
    if not target_id or action not in ('like', 'dislike', 'pass'):
        return jsonify(error='target_id and action required'), 400
    if target_id == cu.id:
        return jsonify(error='Cannot swipe on yourself'), 400
    target   = User.query.get_or_404(target_id)
    existing = Swipe.query.filter_by(swiper_id=cu.id, swiped_id=target_id).first()
    if existing:
        existing.action = action          # Update rather than duplicate
    else:
        db.session.add(Swipe(swiper_id=cu.id, swiped_id=target_id, action=action))
    db.session.commit()
    is_match = False
    if action == 'like':
        reverse  = Swipe.query.filter_by(swiper_id=target_id, swiped_id=cu.id, action='like').first()
        is_match = reverse is not None
    return jsonify(action=action, is_match=is_match, target=target.to_dict()), 200


# ─── MESSAGING ENDPOINTS ──────────────────────────────────────────────────────

@api.route('/api/v1/messages/<int:other_id>', methods=['GET'])
@token_required
def get_messages(other_id):
    """
    Retrieve the full message history between the current user and other_id.

    Access requires:
    1. No active block between the two users.
    2. A mutual match (both users have liked each other).

    All unread messages from other_id are marked as read upon retrieval.
    Messages are returned in chronological order (oldest first).

    Responses
    ---------
    200 : { messages: [message] }
    403 : Block exists, or users are not mutual matches.
    """
    cu = get_current_user()
    if is_blocked_between(cu.id, other_id):
        return jsonify(error='You cannot message this user because a block exists.'), 403
    if not is_mutual_match(cu.id, other_id):
        return jsonify(error='You can only message mutual matches'), 403
    msgs = Message.query.filter(
        ((Message.sender_id == cu.id)    & (Message.receiver_id == other_id)) |
        ((Message.sender_id == other_id) & (Message.receiver_id == cu.id))
    ).order_by(Message.created_at.asc()).all()
    # Mark all incoming unread messages as read
    Message.query.filter_by(sender_id=other_id, receiver_id=cu.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify(messages=[m.to_dict() for m in msgs]), 200


@api.route('/api/v1/messages/<int:other_id>', methods=['POST'])
@token_required
def send_message(other_id):
    """
    Send a message to another user.

    Access requires:
    1. No active block between the two users.
    2. A mutual match.

    Request Body (JSON)
    -------------------
    content : str  The message text (non-empty).

    Responses
    ---------
    201 : { message }  The newly created message.
    400 : Empty content.
    403 : Block exists, or not a mutual match.
    """
    cu = get_current_user()
    if is_blocked_between(cu.id, other_id):
        return jsonify(error='You cannot message this user because a block exists.'), 403
    if not is_mutual_match(cu.id, other_id):
        return jsonify(error='You can only message mutual matches'), 403
    content = (request.get_json() or {}).get('content', '').strip()
    if not content:
        return jsonify(error='Message content required'), 400
    msg = Message(sender_id=cu.id, receiver_id=other_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify(message=msg.to_dict()), 201


@api.route('/api/v1/conversations', methods=['GET'])
@token_required
def get_conversations():
    """
    Return a summary of all active conversations for the current user.

    Only mutual matches that are not blocked are included.  Each entry
    contains the other user's profile, the most recent message (if any),
    and a count of unread messages from that user.

    Results are sorted by the most recent message timestamp, newest first.
    Conversations with no messages appear at the bottom.

    Responses
    ---------
    200 : { conversations: [{ user, last_message, unread_count }] }
    """
    cu           = get_current_user()
    liked_ids    = {s.swiped_id for s in cu.swipes_sent.filter_by(action='like').all()}
    liked_me_ids = {s.swiper_id for s in cu.swipes_received.filter_by(action='like').all()}
    blocked      = get_blocked_ids(cu.id)
    mutual       = (liked_ids & liked_me_ids) - blocked
    convos       = []
    for uid in mutual:
        other = User.query.get(uid)
        if not other:
            continue
        last_msg = Message.query.filter(
            ((Message.sender_id == cu.id)  & (Message.receiver_id == uid)) |
            ((Message.sender_id == uid)    & (Message.receiver_id == cu.id))
        ).order_by(Message.created_at.desc()).first()
        unread = Message.query.filter_by(sender_id=uid, receiver_id=cu.id, is_read=False).count()
        convos.append({
            'user':         other.to_dict(),
            'last_message': last_msg.to_dict() if last_msg else None,
            'unread_count': unread,
        })
    convos.sort(
        key=lambda x: x['last_message']['created_at'] if x['last_message'] else '',
        reverse=True
    )
    return jsonify(conversations=convos), 200


# ─── FAVORITES ENDPOINTS ──────────────────────────────────────────────────────

@api.route('/api/v1/favorites', methods=['GET'])
@token_required
def get_favorites():
    """
    Return all profiles bookmarked by the current user.

    Responses
    ---------
    200 : { favorites: [user] }
    """
    cu   = get_current_user()
    favs = Favorite.query.filter_by(user_id=cu.id).all()
    return jsonify(favorites=[f.favorited.to_dict() for f in favs if f.favorited]), 200


@api.route('/api/v1/favorites/<int:target_id>', methods=['POST'])
@token_required
def add_favorite(target_id):
    """
    Bookmark a profile.  Idempotent — re-bookmarking is not an error.

    Responses
    ---------
    201 : { message }
    404 : Target user not found.
    """
    cu = get_current_user()
    User.query.get_or_404(target_id)
    if not Favorite.query.filter_by(user_id=cu.id, favorited_id=target_id).first():
        db.session.add(Favorite(user_id=cu.id, favorited_id=target_id))
        db.session.commit()
    return jsonify(message='Added to favorites'), 201


@api.route('/api/v1/favorites/<int:target_id>', methods=['DELETE'])
@token_required
def remove_favorite(target_id):
    """
    Remove a bookmarked profile.  Idempotent — no error if not bookmarked.

    Responses
    ---------
    200 : { message }
    """
    cu  = get_current_user()
    fav = Favorite.query.filter_by(user_id=cu.id, favorited_id=target_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return jsonify(message='Removed from favorites'), 200


# ─── REPORT / BLOCK ENDPOINTS (Optional Feature 1) ───────────────────────────

@api.route('/api/v1/report', methods=['POST'])
@token_required
def report_user():
    """
    Report and/or block another user.

    A single Report record covers both actions.  Setting `is_block: true`
    immediately hides the reported user from the reporter's feeds and
    prevents messaging in both directions.

    Re-submitting an existing report (same reporter/reported pair) updates
    the reason, description, and block flag rather than creating a duplicate.

    Request Body (JSON)
    -------------------
    reported_id : int   ID of the user being reported.
    reason      : str   One of: 'fake', 'spam', 'harassment', 'inappropriate', 'other'.
    description : str   (optional) Additional context.
    is_block    : bool  (optional, default false) Whether to also block the user.

    Responses
    ---------
    201 : { message }
    400 : Missing required fields.
    400 : Attempting to report yourself.
    404 : Reported user not found.
    """
    cu          = get_current_user()
    data        = request.get_json() or {}
    reported_id = data.get('reported_id')
    reason      = data.get('reason')
    if not reported_id or not reason:
        return jsonify(error='reported_id and reason required'), 400
    if reported_id == cu.id:
        return jsonify(error='Cannot report yourself'), 400
    User.query.get_or_404(reported_id)
    existing = Report.query.filter_by(reporter_id=cu.id, reported_id=reported_id).first()
    if existing:
        existing.reason      = reason
        existing.description = data.get('description', '')
        existing.is_block    = data.get('is_block', False)
        existing.status      = 'pending'
    else:
        db.session.add(Report(
            reporter_id=cu.id,
            reported_id=reported_id,
            reason=reason,
            description=data.get('description', ''),
            is_block=data.get('is_block', False),
        ))
    db.session.commit()
    action = 'blocked and reported' if data.get('is_block') else 'reported'
    return jsonify(message=f'User has been {action}'), 201


@api.route('/api/v1/blocks', methods=['GET'])
@token_required
def get_blocks():
    """
    Return all users currently blocked by the current user.

    Responses
    ---------
    200 : { blocked_users: [user] }
    """
    cu     = get_current_user()
    blocks = Report.query.filter_by(reporter_id=cu.id, is_block=True).all()
    blocked_users = [
        User.query.get(b.reported_id).to_dict()
        for b in blocks if User.query.get(b.reported_id)
    ]
    return jsonify(blocked_users=blocked_users), 200


@api.route('/api/v1/blocks/<int:target_id>', methods=['DELETE'])
@token_required
def unblock_user(target_id):
    """
    Lift a block against a user.

    Sets is_block=False on the report record rather than deleting it, so the
    report itself (if any) is preserved for moderation purposes.

    Responses
    ---------
    200 : { message }
    """
    cu     = get_current_user()
    report = Report.query.filter_by(reporter_id=cu.id, reported_id=target_id, is_block=True).first()
    if report:
        report.is_block = False
        db.session.commit()
    return jsonify(message='User unblocked'), 200


# ─── SEARCH ENDPOINT ──────────────────────────────────────────────────────────

@api.route('/api/v1/search', methods=['GET'])
@token_required
def search():
    """
    Search for public user profiles by name, bio, or location.

    Blocked users are always excluded from results.  Returns up to 50 profiles
    sorted by match score descending.

    Query Parameters
    ----------------
    q : str  Search term.  If omitted, all visible non-blocked profiles are returned.

    Responses
    ---------
    200 : { results: [user + match_score] }
    """
    cu      = get_current_user()
    q       = request.args.get('q', '').strip()
    blocked = get_blocked_ids(cu.id)
    query   = User.query.filter(
        User.id != cu.id,
        User.id.notin_(blocked),
        User.is_public == True
    )
    if q:
        query = query.filter(
            User.first_name.ilike(f'%{q}%') | User.last_name.ilike(f'%{q}%') |
            User.bio.ilike(f'%{q}%')         | User.location.ilike(f'%{q}%')
        )
    results = []
    for u in query.limit(50).all():
        d = u.to_dict()
        d['match_score'] = compute_match_score(cu, u)
        results.append(d)
    results.sort(key=lambda x: x['match_score'], reverse=True)
    return jsonify(results=results), 200


# ─── AFTER REQUEST HOOK ───────────────────────────────────────────────────────

@api.after_request
def add_header(response):
    """Disable response caching for all API responses."""
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response
