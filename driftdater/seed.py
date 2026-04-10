"""
seed.py
-------
Database seeder for DriftDater.

Generates 100 realistic fake user accounts and inserts them into the
database.  Run this once after `flask db upgrade` to populate the app
with test data so you can immediately browse matches, test the algorithm,
and demo the application without manually creating accounts.

Usage
-----
    python seed.py

Requirements
------------
- The virtual environment must be active.
- The database must already exist (flask db upgrade must have been run).
- Run from the project root directory (same folder as app.py).

What Gets Created
-----------------
- 100 user accounts with realistic Jamaican/Caribbean names and locations
- Varied ages (18–55), genders, occupations, and education backgrounds
- 3–8 interests per user selected from a pool of 30 common interests
- Randomised match preferences (age range, max distance, looking_for)
- Hashed passwords — all accounts use the password:  Test1234!
- Randomised bio sentences
- All profiles set to public so they appear in Discover

No profile photos are generated.  The initials avatar placeholder will
be shown for all seeded users in the frontend.
"""

import random
import sys
import os
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Bootstrap Flask app context so SQLAlchemy models are available
# ---------------------------------------------------------------------------
# This must happen before importing db or any models.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db
from app.models import User, Interest

# ---------------------------------------------------------------------------
# Seed Data Pools
# ---------------------------------------------------------------------------

FIRST_NAMES_FEMALE = [
    "Aaliyah", "Brianna", "Camille", "Danielle", "Ebony", "Faith", "Gabrielle",
    "Hannah", "Imani", "Jade", "Keisha", "Latoya", "Monique", "Nadine", "Olivia",
    "Priya", "Quinta", "Renee", "Simone", "Tiffany", "Unique", "Vanessa",
    "Whitney", "Xiomara", "Yasmine", "Zoe", "Aisha", "Bianca", "Crystal",
    "Deja", "Elena", "Felicia", "Grace", "Harmony", "Iris", "Jada",
]

FIRST_NAMES_MALE = [
    "Aaron", "Brandon", "Calvin", "Darnell", "Emmanuel", "Fabio", "Gabriel",
    "Hassan", "Isaiah", "Jamal", "Kareem", "Leon", "Marcus", "Nathan", "Omar",
    "Patrick", "Quentin", "Rasheed", "Samuel", "Tyrone", "Umar", "Vincent",
    "Wayne", "Xavier", "Yannick", "Zion", "Andre", "Byron", "Clive",
    "Devontae", "Elijah", "Fabian", "Grant", "Hector", "Ivan", "Jermaine",
]

FIRST_NAMES_NB = [
    "Alex", "Blake", "Cameron", "Dakota", "Ellis", "Finley", "Gray",
    "Harper", "Indigo", "Jordan", "Kendall", "Logan", "Morgan", "Nico",
    "Parker", "Quinn", "Riley", "Sage", "Taylor", "Avery",
]

LAST_NAMES = [
    "Brown", "Campbell", "Clarke", "Davis", "Edwards", "Ferguson", "Grant",
    "Henry", "Jackson", "Johnson", "King", "Lewis", "Martin", "Morgan",
    "Nelson", "Patterson", "Reid", "Robinson", "Scott", "Thompson",
    "Walker", "White", "Williams", "Wilson", "Wright", "Young", "Allen",
    "Anderson", "Bailey", "Bennett", "Brooks", "Burke", "Burns", "Carter",
    "Christie", "Cole", "Collins", "Cook", "Cooper", "Cox", "Cunningham",
    "Dixon", "Doyle", "Duncan", "Fletcher", "Foster", "Fraser", "Gibson",
    "Graham", "Green", "Hall", "Hamilton", "Harris", "Harrison", "Harvey",
    "Hill", "Holmes", "Howard", "Hughes", "Hunter", "James",
]

LOCATIONS = [
    ("Kingston, Jamaica",        17.9714,  -76.7928),
    ("Portmore, Jamaica",        17.9433,  -76.8833),
    ("Spanish Town, Jamaica",    17.9941,  -76.9571),
    ("Montego Bay, Jamaica",     18.4762,  -77.8939),
    ("Mandeville, Jamaica",      18.0408,  -77.5032),
    ("May Pen, Jamaica",         17.9644,  -77.2453),
    ("Ocho Rios, Jamaica",       18.4072,  -77.1039),
    ("Negril, Jamaica",          18.2689,  -78.3572),
    ("Old Harbour, Jamaica",     17.9419,  -77.1076),
    ("Linstead, Jamaica",        18.1344,  -77.0305),
    ("Half Way Tree, Jamaica",   17.9942,  -76.7914),
    ("New Kingston, Jamaica",    18.0059,  -76.7851),
    ("Bridgetown, Barbados",     13.1132,  -59.5988),
    ("Port of Spain, Trinidad",  10.6549,  -61.5019),
    ("Georgetown, Guyana",        6.8013,  -58.1553),
    ("Nassau, Bahamas",          25.0480,  -77.3554),
    ("Havana, Cuba",             23.1136,  -82.3666),
    ("Santo Domingo, Dom. Rep.", 18.4861,  -69.9312),
]

OCCUPATIONS = [
    "Software Developer", "Nurse", "Teacher", "Accountant", "Graphic Designer",
    "Marketing Manager", "Chef", "Lawyer", "Engineer", "Journalist",
    "Photographer", "Entrepreneur", "Social Worker", "Pharmacist", "Architect",
    "Doctor", "Data Analyst", "Event Planner", "Police Officer", "Electrician",
    "Fitness Trainer", "Content Creator", "Real Estate Agent", "Mechanic",
    "Fashion Designer", "Project Manager", "Security Guard", "Librarian",
    "Sound Engineer", "Nutritionist",
]

EDUCATION = [
    "UWI Mona",
    "UWI Cave Hill",
    "UTech Jamaica",
    "UTECH",
    "HEART Trust NTA",
    "Community College",
    "High School Graduate",
    "Northern Caribbean University",
    "Caribbean School of Data Science",
    "University of Technology",
    "Edna Manley College",
    "Knox Community College",
    "Portmore Community College",
]

INTERESTS_POOL = [
    "hiking", "gaming", "cooking", "reading", "music", "travel", "art",
    "photography", "fitness", "yoga", "movies", "dancing", "sports", "tech",
    "fashion", "swimming", "cycling", "running", "painting", "crafts",
    "gardening", "volunteering", "poetry", "theatre", "karaoke", "fishing",
    "basketball", "football", "cricket", "netball",
]

BIO_OPENERS = [
    "I love exploring new places and meeting interesting people.",
    "Life is short — spend it doing what you love.",
    "Looking for someone to share adventures with.",
    "I believe laughter is the best medicine.",
    "Passionate about good food and great conversations.",
    "I work hard and play harder.",
    "A simple person with big dreams.",
    "Currently living my best life one day at a time.",
    "Coffee addict and sunset chaser.",
    "I'm the friend everyone comes to for advice.",
    "Music is my therapy and travel is my passion.",
    "Dog lover, beach enthusiast, amateur chef.",
    "I enjoy deep conversations under the stars.",
    "Spontaneous trips are my favourite kind.",
    "Always up for a new experience.",
    "Trying to see every country before I'm 40.",
    "Family first, everything else second.",
    "I will probably talk about my hobbies too much — you have been warned.",
    "Honestly just here to meet genuine people.",
    "Ambitious by day, relaxed by night.",
]

BIO_CLOSERS = [
    "Ask me about my favourite hiking trails.",
    "Swipe right if you love good vibes.",
    "Let's grab coffee and see what happens.",
    "Looking for something real, not just a chat.",
    "Not here for games — just genuine connection.",
    "DM me your favourite song and we'll talk.",
    "I promise I'm more interesting in person.",
    "If you can beat me at Scrabble, I'm impressed.",
    "I cook — that has to count for something.",
    "Bonus points if you love the beach.",
]

LOOKING_FOR_OPTIONS = ["male", "female", "non-binary", "any", "any", "any"]  # 'any' weighted higher
GENDER_OPTIONS      = ["male", "female", "male", "female", "non-binary"]     # weighted realistic split


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def random_dob(min_age=18, max_age=55):
    """Generate a random date of birth for the given age range."""
    today      = date.today()
    max_days   = (max_age - min_age) * 365
    days_back  = random.randint(min_age * 365, (min_age + max_days // 365) * 365)
    return today - timedelta(days=days_back)


def random_username(first, last, existing):
    """
    Generate a unique username from first name + last name + optional number.
    Retries with an incrementing suffix until the name is not in `existing`.
    """
    base = f"{first.lower()}{last.lower()}"
    candidate = base
    n = 1
    while candidate in existing:
        candidate = f"{base}{n}"
        n += 1
    existing.add(candidate)
    return candidate


def random_email(first, last, existing):
    """Generate a unique email address."""
    domains  = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
    base     = f"{first.lower()}.{last.lower()}"
    candidate = f"{base}@{random.choice(domains)}"
    n = 1
    while candidate in existing:
        candidate = f"{base}{n}@{random.choice(domains)}"
        n += 1
    existing.add(candidate)
    return candidate


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def seed_database(count=100):
    """
    Insert `count` fake users into the database.

    Parameters
    ----------
    count : int  Number of users to create (default 100).
    """
    with app.app_context():
        # ------------------------------------------------------------------
        # 1. Ensure all interest tags exist in the interests table
        # ------------------------------------------------------------------
        print("Seeding interests...")
        interest_objects = {}
        for name in INTERESTS_POOL:
            existing = Interest.query.filter_by(name=name).first()
            if not existing:
                existing = Interest(name=name)
                db.session.add(existing)
            interest_objects[name] = existing
        db.session.flush()   # Get IDs without committing yet

        # ------------------------------------------------------------------
        # 2. Check how many users already exist
        # ------------------------------------------------------------------
        existing_count = User.query.count()
        if existing_count > 0:
            print(f"Database already has {existing_count} users.")
            answer = input("Add more users anyway? (y/N): ").strip().lower()
            if answer != 'y':
                print("Seeding cancelled.")
                return

        # ------------------------------------------------------------------
        # 3. Collect existing usernames and emails to ensure uniqueness
        # ------------------------------------------------------------------
        used_usernames = {u.username for u in User.query.with_entities(User.username).all()}
        used_emails    = {u.email    for u in User.query.with_entities(User.email).all()}

        # ------------------------------------------------------------------
        # 4. Generate users
        # ------------------------------------------------------------------
        print(f"Generating {count} users...")
        created = 0

        for i in range(count):
            gender = random.choice(GENDER_OPTIONS)

            # Pick an appropriate name pool for the gender
            if gender == "female":
                first = random.choice(FIRST_NAMES_FEMALE)
            elif gender == "male":
                first = random.choice(FIRST_NAMES_MALE)
            else:
                first = random.choice(FIRST_NAMES_NB)

            last       = random.choice(LAST_NAMES)
            username   = random_username(first, last, used_usernames)
            email      = random_email(first, last, used_emails)
            dob        = random_dob(min_age=18, max_age=55)
            location_data = random.choice(LOCATIONS)
            location   = location_data[0]
            latitude   = location_data[1] + random.uniform(-0.05, 0.05)   # Small random offset
            longitude  = location_data[2] + random.uniform(-0.05, 0.05)

            # Bio: combine a random opener and closer
            bio = f"{random.choice(BIO_OPENERS)} {random.choice(BIO_CLOSERS)}"

            # Age preferences: realistic range around a random midpoint
            pref_center = random.randint(20, 45)
            age_min     = max(18, pref_center - random.randint(3, 10))
            age_max     = min(60, pref_center + random.randint(3, 10))

            user = User(
                email        = email,
                username     = username,
                first_name   = first,
                last_name    = last,
                date_of_birth= dob,
                gender       = gender,
                looking_for  = random.choice(LOOKING_FOR_OPTIONS),
                bio          = bio,
                location     = location,
                latitude     = round(latitude,  6),
                longitude    = round(longitude, 6),
                occupation   = random.choice(OCCUPATIONS),
                education    = random.choice(EDUCATION),
                is_public    = True,
                age_min_pref = age_min,
                age_max_pref = age_max,
                max_distance = random.choice([25, 50, 75, 100, 150, 200]),
            )
            user.set_password("Test1234!")   # All seeded users share this password

            # Assign 3–8 random interests
            num_interests = random.randint(3, 8)
            chosen_interests = random.sample(INTERESTS_POOL, num_interests)
            user.interests = [interest_objects[name] for name in chosen_interests]

            db.session.add(user)
            created += 1

            # Commit in batches of 25 to avoid large memory transactions
            if created % 25 == 0:
                db.session.commit()
                print(f"  {created}/{count} users created...")

        # Final commit for any remainder
        db.session.commit()
        print(f"\n✅ Done! {created} users added to the database.")
        print(f"   Password for all seeded accounts: Test1234!")
        print(f"   Total users in database: {User.query.count()}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    # Allow passing a custom count: python seed.py 50
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed_database(count)
