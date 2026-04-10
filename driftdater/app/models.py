"""
app/models.py
-------------
SQLAlchemy ORM models for DriftDater.

Database Schema (6 tables)
---------------------------
users           - Registered user accounts with profile and preference data
interests       - Normalised interest/hobby tags
user_interests  - Many-to-many junction table linking users to interests
swipes          - Records of like / dislike / pass actions between users
messages        - Individual chat messages between matched users
favorites       - Bookmarked profiles saved by a user
reports         - Reports and/or blocks submitted by one user against another

Design Notes
------------
- All self-referential relationships (Swipe, Message, Favorite, Report) point
  two foreign keys at the `users` table.  SQLAlchemy requires explicit
  `foreign_keys=` arguments on every such relationship to resolve the ambiguity.
- Passwords are stored as bcrypt hashes via Werkzeug helpers; plain-text
  passwords are never persisted.
- Age is computed as a Python property from `date_of_birth` rather than stored,
  so it is always accurate without migration overhead.
"""

from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login callback that reloads a user from the database by primary key.

    Parameters
    ----------
    user_id : str
        The user's primary key as a string (Flask-Login requirement).

    Returns
    -------
    User or None
    """
    return User.query.get(int(user_id))


# ─── Association Table ────────────────────────────────────────────────────────

# Many-to-many junction table: a user can have many interests, and an interest
# can belong to many users.  Defined as a plain Table (not a model class)
# because no extra columns are needed beyond the two foreign keys.
user_interests = db.Table(
    'user_interests',
    db.Column('user_id',    db.Integer, db.ForeignKey('users.id'),     primary_key=True),
    db.Column('interest_id', db.Integer, db.ForeignKey('interests.id'), primary_key=True)
)


# ─── User ─────────────────────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    """
    Registered user account.

    Inherits UserMixin to satisfy Flask-Login's interface (is_authenticated,
    is_active, get_id, etc.).

    Profile Fields
    --------------
    Basic       : first_name, last_name, date_of_birth, gender, bio
    Location    : location (display string), latitude, longitude
    Preferences : looking_for, age_min_pref, age_max_pref, max_distance
    Custom      : occupation, education  (two required custom fields)
    Privacy     : is_public (controls visibility in Discover)

    Relationships
    -------------
    interests       - M2M with Interest via user_interests
    swipes_sent     - Swipes this user has cast on others
    swipes_received - Swipes cast on this user by others
    messages_sent   - Messages this user has sent
    messages_received - Messages this user has received
    favorites       - Profiles bookmarked by this user
    reports_made    - Reports/blocks this user has filed
    reports_received - Reports/blocks filed against this user
    """

    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name    = db.Column(db.String(60),  nullable=False)
    last_name     = db.Column(db.String(60),  nullable=False)
    date_of_birth = db.Column(db.Date,        nullable=True)
    gender        = db.Column(db.String(20),  nullable=True)
    looking_for   = db.Column(db.String(20),  nullable=True)   # 'male','female','non-binary','any'
    bio           = db.Column(db.Text,        nullable=True)
    location      = db.Column(db.String(120), nullable=True)   # Human-readable city/country
    latitude      = db.Column(db.Float,       nullable=True)   # Decimal degrees (WGS-84)
    longitude     = db.Column(db.Float,       nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)   # Filename in uploads/
    is_public     = db.Column(db.Boolean,     default=True)    # False = hidden from Discover
    occupation    = db.Column(db.String(100), nullable=True)   # Custom field 1
    education     = db.Column(db.String(100), nullable=True)   # Custom field 2
    age_min_pref  = db.Column(db.Integer,     default=18)      # Minimum age preference
    age_max_pref  = db.Column(db.Integer,     default=99)      # Maximum age preference
    max_distance  = db.Column(db.Integer,     default=100)     # km radius for location matching
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    # Interests: many-to-many via junction table
    interests = db.relationship('Interest', secondary=user_interests, backref='users')

    # Swipes — two FK paths to users require explicit foreign_keys
    swipes_sent     = db.relationship('Swipe', foreign_keys='Swipe.swiper_id',
                                      backref='swiper', lazy='dynamic')
    swipes_received = db.relationship('Swipe', foreign_keys='Swipe.swiped_id',
                                      backref='swiped', lazy='dynamic')

    # Messages — two FK paths to users require explicit foreign_keys
    messages_sent     = db.relationship('Message', foreign_keys='Message.sender_id',
                                        backref='sender', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id',
                                        backref='receiver', lazy='dynamic')

    # Favorites — user_id is the FK back to this user (the bookmarker)
    favorites = db.relationship('Favorite', foreign_keys='Favorite.user_id',
                                backref='owner', lazy='dynamic')

    # Reports — two FK paths require explicit foreign_keys
    reports_made     = db.relationship('Report', foreign_keys='Report.reporter_id',
                                       backref='reporter', lazy='dynamic')
    reports_received = db.relationship('Report', foreign_keys='Report.reported_id',
                                       backref='reported_user', lazy='dynamic')

    # ── Password helpers ──────────────────────────────────────────────────────

    def set_password(self, password):
        """Hash and store a plain-text password using Werkzeug/bcrypt."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify a plain-text password against the stored hash.

        Returns
        -------
        bool : True if the password matches, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    # ── Computed Properties ───────────────────────────────────────────────────

    @property
    def age(self):
        """
        Calculate the user's current age in years from date_of_birth.

        Returns
        -------
        int or None : Age in years, or None if date_of_birth is not set.
        """
        if self.date_of_birth:
            today = datetime.today()
            dob   = self.date_of_birth
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self, include_private=False):
        """
        Serialise the user to a JSON-safe dictionary.

        Parameters
        ----------
        include_private : bool
            When True, adds fields that should only be visible to the user
            themselves (email, preferences, coordinates).  Defaults to False
            for public-facing profile data.

        Returns
        -------
        dict
        """
        data = {
            'id':            self.id,
            'username':      self.username,
            'first_name':    self.first_name,
            'last_name':     self.last_name,
            'age':           self.age,
            'gender':        self.gender,
            'bio':           self.bio,
            'location':      self.location,
            'profile_photo': self.profile_photo,
            'occupation':    self.occupation,
            'education':     self.education,
            'interests':     [i.name for i in self.interests],
            'created_at':    self.created_at.isoformat() if self.created_at else None,
        }
        if include_private:
            data.update({
                'email':        self.email,
                'looking_for':  self.looking_for,
                'age_min_pref': self.age_min_pref,
                'age_max_pref': self.age_max_pref,
                'max_distance': self.max_distance,
                'is_public':    self.is_public,
                'latitude':     self.latitude,
                'longitude':    self.longitude,
            })
        return data


# ─── Interest ─────────────────────────────────────────────────────────────────

class Interest(db.Model):
    """
    Normalised interest/hobby tag.

    Stored once and referenced by many users via the user_interests junction
    table, avoiding duplication of tag strings.

    Examples: 'hiking', 'gaming', 'cooking', 'photography'
    """

    __tablename__ = 'interests'

    id   = db.Column(db.Integer,    primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False, index=True)

    def to_dict(self):
        """Return a minimal dictionary representation."""
        return {'id': self.id, 'name': self.name}


# ─── Swipe ────────────────────────────────────────────────────────────────────

class Swipe(db.Model):
    """
    Records a swipe action from one user toward another.

    Actions
    -------
    'like'    - The swiper is interested in the swiped user.
    'dislike' - The swiper is not interested.
    'pass'    - The swiper skips without a strong preference.

    A mutual match occurs when both users have a 'like' swipe toward each other.
    The unique constraint prevents duplicate swipe records for the same pair.
    """

    __tablename__ = 'swipes'

    id         = db.Column(db.Integer,    primary_key=True)
    swiper_id  = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False, index=True)
    swiped_id  = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False, index=True)
    action     = db.Column(db.String(10), nullable=False)  # 'like' | 'dislike' | 'pass'
    created_at = db.Column(db.DateTime,   default=datetime.utcnow)

    # Enforce one swipe record per ordered pair (swiper → swiped)
    __table_args__ = (db.UniqueConstraint('swiper_id', 'swiped_id'),)

    def to_dict(self):
        return {
            'id':         self.id,
            'swiper_id':  self.swiper_id,
            'swiped_id':  self.swiped_id,
            'action':     self.action,
            'created_at': self.created_at.isoformat(),
        }


# ─── Message ──────────────────────────────────────────────────────────────────

class Message(db.Model):
    """
    A single chat message sent between two mutually matched users.

    Only users with a mutual 'like' swipe may exchange messages.  If a block
    is placed after messages have been sent, the conversation becomes
    inaccessible via the API while the block is active.

    The `is_read` flag is set to True when the receiver next loads the
    conversation, enabling unread message badge counts.
    """

    __tablename__ = 'messages'

    id          = db.Column(db.Integer,  primary_key=True)
    sender_id   = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False, index=True)
    content     = db.Column(db.Text,     nullable=False)
    is_read     = db.Column(db.Boolean,  default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id':          self.id,
            'sender_id':   self.sender_id,
            'receiver_id': self.receiver_id,
            'content':     self.content,
            'is_read':     self.is_read,
            'created_at':  self.created_at.isoformat(),
        }


# ─── Favorite ─────────────────────────────────────────────────────────────────

class Favorite(db.Model):
    """
    A bookmarked profile saved by a user.

    Favorites are independent of swipes — a user can bookmark a profile
    before or after swiping on it.  The unique constraint prevents a user
    from bookmarking the same profile twice.
    """

    __tablename__ = 'favorites'

    id           = db.Column(db.Integer,  primary_key=True)
    user_id      = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False, index=True)
    favorited_id = db.Column(db.Integer,  db.ForeignKey('users.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'favorited_id'),)

    # Explicit foreign_keys required because two FKs point to the same table.
    # This relationship resolves the favorited_id FK to give the bookmarked user.
    favorited = db.relationship('User', foreign_keys=[favorited_id])


# ─── Report ───────────────────────────────────────────────────────────────────

class Report(db.Model):
    """
    Optional Feature 1 — Report and/or Block a user.

    A single record serves two purposes:
    - Report  : flags the reported user to admins (status workflow).
    - Block   : when is_block=True, hides the reported user from the reporter's
                Discover feed, Matches list, and prevents messaging in both
                directions until the block is lifted.

    Reason Codes
    ------------
    'fake'         - Fake or impersonation account
    'spam'         - Spam or bot behaviour
    'harassment'   - Unwanted or abusive contact
    'inappropriate'- Inappropriate profile content
    'other'        - Anything else (described in `description`)

    Status Workflow
    ---------------
    'pending'  → 'reviewed' → 'resolved'

    The unique constraint allows a user to update an existing report rather
    than creating duplicates for the same pair.
    """

    __tablename__ = 'reports'

    id          = db.Column(db.Integer,    primary_key=True)
    reporter_id = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False, index=True)
    reported_id = db.Column(db.Integer,    db.ForeignKey('users.id'), nullable=False, index=True)
    reason      = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text,       nullable=True)
    is_block    = db.Column(db.Boolean,    default=False)   # True = active block
    status      = db.Column(db.String(20), default='pending')
    created_at  = db.Column(db.DateTime,   default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('reporter_id', 'reported_id'),)

    def to_dict(self):
        return {
            'id':          self.id,
            'reporter_id': self.reporter_id,
            'reported_id': self.reported_id,
            'reason':      self.reason,
            'description': self.description,
            'is_block':    self.is_block,
            'status':      self.status,
            'created_at':  self.created_at.isoformat(),
        }
