"""
seed_demo_data.py
Run: python seed_demo_data.py
Populates finance.db with a demo user + 5 months of realistic transactions + goals.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone, date
import bcrypt, hashlib, base64
from models.database import engine, SessionLocal, Base
from models.schemas import User, Transaction, Goal

def _pre_hash(password: str) -> str:
    digest = hashlib.sha256(password.encode()).digest()
    return base64.b64encode(digest).decode()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(_pre_hash(password).encode(), bcrypt.gensalt()).decode()

DEMO_USER = {
    "name":                  "Alex Johnson",
    "email":                 "hello@gmail.com",
    "password":              "demo1234",
    "phone":                 "+1 555 010 2030",
    "dob":                   date(1995, 6, 15),
    "monthly_income":        5500.00,
    "monthly_savings_goal":  800.00,
}

# (day, type, category, merchant, amount, description)
MONTHLY_TRANSACTIONS = {
    1: [  # January 2025
        ( 1, "income",  "💼 Income",        "Employer Direct Deposit",   5500.00, "Jan salary"),
        (18, "income",  "💼 Income",        "Freelance Client - Sara",    200.00, "Website fix"),
        ( 1, "expense", "🏠 Housing",       "Apartment Rent",            1200.00, "Jan rent"),
        ( 3, "expense", "🏠 Housing",       "Nepal Electricity Board",     38.50, "Electric bill"),
        ( 5, "expense", "🏠 Housing",       "Internet Provider",           25.00, "Monthly broadband"),
        ( 2, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      91.20, "Weekly groceries"),
        ( 9, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      67.40, "Weekly groceries"),
        (16, "expense", "🛒 Groceries",     "Salesberry Mall",             72.10, "Weekly groceries"),
        (23, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      55.80, "Weekly groceries"),
        (29, "expense", "🛒 Groceries",     "Local Bazaar",                28.50, "Vegetables & fruit"),
        ( 4, "expense", "🍔 Dining",        "Roadhouse Cafe",              19.50, "Dinner with friends"),
        ( 8, "expense", "🍔 Dining",        "Starbucks",                    6.50, "Morning coffee"),
        (13, "expense", "🍔 Dining",        "KFC Durbar Marg",             14.00, "Lunch"),
        (20, "expense", "🍔 Dining",        "Himalayan Java",              10.50, "Working from cafe"),
        (25, "expense", "🍔 Dining",        "Local Momos Stall",            4.00, "Street food"),
        ( 3, "expense", "🚗 Transport",     "Pathao Ride",                  7.50, "Office commute"),
        ( 6, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        (18, "expense", "🚗 Transport",     "Micro Bus Pass",              12.00, "Monthly pass"),
        (24, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        ( 7, "expense", "💊 Health",        "Norvic Hospital",             60.00, "Check-up"),
        (21, "expense", "💊 Health",        "Anytime Fitness",             30.00, "Gym monthly"),
        ( 5, "expense", "🎬 Entertainment", "Netflix",                     15.49, "Monthly subscription"),
        ( 5, "expense", "🎬 Entertainment", "Spotify",                      9.99, "Monthly subscription"),
        (15, "expense", "🎬 Entertainment", "QFX Cinemas",                 14.00, "Movie night"),
        (10, "expense", "🛍️ Shopping",     "Daraz Online",                42.00, "Clothes"),
    ],
    2: [  # February 2025
        ( 1, "income",  "💼 Income",        "Employer Direct Deposit",   5500.00, "Feb salary"),
        (10, "income",  "💼 Income",        "Freelance Client - Ravi",    300.00, "App design"),
        (25, "income",  "💼 Income",        "Cashback Rewards",            12.00, "Credit card cashback"),
        ( 1, "expense", "🏠 Housing",       "Apartment Rent",            1200.00, "Feb rent"),
        ( 3, "expense", "🏠 Housing",       "Nepal Electricity Board",     41.00, "Electric bill"),
        ( 5, "expense", "🏠 Housing",       "Internet Provider",           25.00, "Monthly broadband"),
        ( 2, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      85.60, "Weekly groceries"),
        ( 9, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      60.20, "Weekly groceries"),
        (16, "expense", "🛒 Groceries",     "Salesberry Mall",             78.40, "Weekly groceries"),
        (23, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      52.10, "Weekly groceries"),
        ( 4, "expense", "🍔 Dining",        "Roadhouse Cafe",              24.00, "Valentine dinner"),
        ( 8, "expense", "🍔 Dining",        "Starbucks",                    7.00, "Morning coffee"),
        (14, "expense", "🍔 Dining",        "OR2K Restaurant",             45.00, "Valentine's Day"),
        (20, "expense", "🍔 Dining",        "Himalayan Java",              11.00, "Working from cafe"),
        (25, "expense", "🍔 Dining",        "Local Momos Stall",            5.00, "Street food"),
        ( 3, "expense", "🚗 Transport",     "Pathao Ride",                  8.00, "Office commute"),
        ( 6, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        (18, "expense", "🚗 Transport",     "Micro Bus Pass",              12.00, "Monthly pass"),
        (24, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        (14, "expense", "💊 Health",        "Himalaya Drug Store",         18.50, "Medicines"),
        (21, "expense", "💊 Health",        "Anytime Fitness",             30.00, "Gym monthly"),
        ( 5, "expense", "🎬 Entertainment", "Netflix",                     15.49, "Monthly subscription"),
        ( 5, "expense", "🎬 Entertainment", "Spotify",                      9.99, "Monthly subscription"),
        (22, "expense", "🎬 Entertainment", "Steam",                       24.99, "Game purchase"),
        (13, "expense", "🛍️ Shopping",     "Daraz Online",                65.00, "Headphones"),
    ],
    3: [  # March 2025
        ( 1, "income",  "💼 Income",        "Employer Direct Deposit",   5500.00, "Mar salary"),
        (12, "income",  "💼 Income",        "Freelance Client - Priya",   450.00, "Dashboard UI"),
        ( 1, "expense", "🏠 Housing",       "Apartment Rent",            1200.00, "Mar rent"),
        ( 3, "expense", "🏠 Housing",       "Nepal Electricity Board",     44.20, "Electric bill"),
        ( 5, "expense", "🏠 Housing",       "Internet Provider",           25.00, "Monthly broadband"),
        ( 2, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      93.80, "Weekly groceries"),
        ( 9, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      65.50, "Weekly groceries"),
        (16, "expense", "🛒 Groceries",     "Salesberry Mall",             70.20, "Weekly groceries"),
        (23, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      61.40, "Weekly groceries"),
        (29, "expense", "🛒 Groceries",     "Local Bazaar",                33.10, "Vegetables & fruit"),
        ( 4, "expense", "🍔 Dining",        "Roadhouse Cafe",              21.00, "Dinner with friends"),
        ( 8, "expense", "🍔 Dining",        "Starbucks",                    6.80, "Morning coffee"),
        (12, "expense", "🍔 Dining",        "KFC Durbar Marg",             16.00, "Lunch"),
        (17, "expense", "🍔 Dining",        "OR2K Restaurant",             40.00, "Team dinner"),
        (25, "expense", "🍔 Dining",        "Local Momos Stall",            4.50, "Street food"),
        ( 3, "expense", "🚗 Transport",     "Pathao Ride",                  9.00, "Office commute"),
        ( 6, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        (11, "expense", "🚗 Transport",     "Pathao Ride",                  6.50, "Evening ride"),
        (18, "expense", "🚗 Transport",     "Micro Bus Pass",              12.00, "Monthly pass"),
        (24, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        ( 7, "expense", "💊 Health",        "Norvic Hospital",             75.00, "Check-up & lab"),
        (21, "expense", "💊 Health",        "Anytime Fitness",             30.00, "Gym monthly"),
        ( 5, "expense", "🎬 Entertainment", "Netflix",                     15.49, "Monthly subscription"),
        ( 5, "expense", "🎬 Entertainment", "Spotify",                      9.99, "Monthly subscription"),
        (10, "expense", "🎬 Entertainment", "QFX Cinemas",                 14.00, "Movie night"),
        (20, "expense", "🛍️ Shopping",     "CG Electronics",             150.00, "Monitor stand"),
        (27, "expense", "🛍️ Shopping",     "Daraz Online",                35.00, "Books"),
    ],
    4: [  # April 2025
        ( 1, "income",  "💼 Income",        "Employer Direct Deposit",   5500.00, "Apr salary"),
        ( 8, "income",  "💼 Income",        "Freelance Client - James",   250.00, "SEO audit"),
        (20, "income",  "💼 Income",        "Cashback Rewards",            15.75, "Credit card cashback"),
        ( 1, "expense", "🏠 Housing",       "Apartment Rent",            1200.00, "Apr rent"),
        ( 3, "expense", "🏠 Housing",       "Nepal Electricity Board",     39.80, "Electric bill"),
        ( 5, "expense", "🏠 Housing",       "Internet Provider",           25.00, "Monthly broadband"),
        ( 2, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      88.30, "Weekly groceries"),
        ( 9, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      63.70, "Weekly groceries"),
        (16, "expense", "🛒 Groceries",     "Salesberry Mall",             76.50, "Weekly groceries"),
        (23, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      57.20, "Weekly groceries"),
        (28, "expense", "🛒 Groceries",     "Local Bazaar",                29.80, "Vegetables & fruit"),
        ( 4, "expense", "🍔 Dining",        "Roadhouse Cafe",              23.00, "Dinner with friends"),
        ( 8, "expense", "🍔 Dining",        "Starbucks",                    6.80, "Morning coffee"),
        (13, "expense", "🍔 Dining",        "KFC Durbar Marg",             15.00, "Lunch"),
        (19, "expense", "🍔 Dining",        "OR2K Restaurant",             36.00, "Team dinner"),
        (26, "expense", "🍔 Dining",        "Local Momos Stall",            4.50, "Street food"),
        ( 3, "expense", "🚗 Transport",     "Pathao Ride",                  8.50, "Office commute"),
        ( 6, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        (18, "expense", "🚗 Transport",     "Micro Bus Pass",              12.00, "Monthly pass"),
        (24, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        (14, "expense", "💊 Health",        "Himalaya Drug Store",         22.00, "Medicines"),
        (21, "expense", "💊 Health",        "Anytime Fitness",             30.00, "Gym monthly"),
        ( 5, "expense", "🎬 Entertainment", "Netflix",                     15.49, "Monthly subscription"),
        ( 5, "expense", "🎬 Entertainment", "Spotify",                      9.99, "Monthly subscription"),
        (15, "expense", "🎬 Entertainment", "QFX Cinemas",                 14.00, "Movie night"),
        (26, "expense", "🎬 Entertainment", "YouTube Premium",              6.99, "Monthly subscription"),
        (13, "expense", "🛍️ Shopping",     "Daraz Online",                48.00, "Backpack"),
        (22, "expense", "🛍️ Shopping",     "CG Electronics",              89.00, "USB hub"),
    ],
    5: [  # May 2025
        ( 1, "income",  "💼 Income",        "Employer Direct Deposit",   5500.00, "May salary"),
        (15, "income",  "💼 Income",        "Freelance Client - Ravi",    350.00, "Logo design"),
        (22, "income",  "💼 Income",        "Cashback Rewards",            18.50, "Credit card cashback"),
        ( 1, "expense", "🏠 Housing",       "Apartment Rent",            1200.00, "May rent"),
        ( 3, "expense", "🏠 Housing",       "Nepal Electricity Board",     42.80, "Electric bill"),
        ( 5, "expense", "🏠 Housing",       "Internet Provider",           25.00, "Monthly broadband"),
        ( 2, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      87.40, "Weekly groceries"),
        ( 9, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      62.15, "Weekly groceries"),
        (16, "expense", "🛒 Groceries",     "Salesberry Mall",             74.90, "Weekly groceries"),
        (23, "expense", "🛒 Groceries",     "Bhatbhateni Superstore",      58.30, "Weekly groceries"),
        (29, "expense", "🛒 Groceries",     "Local Bazaar",                31.20, "Vegetables & fruit"),
        ( 4, "expense", "🍔 Dining",        "Roadhouse Cafe",              22.50, "Dinner with friends"),
        ( 8, "expense", "🍔 Dining",        "Starbucks",                    6.80, "Morning coffee"),
        (12, "expense", "🍔 Dining",        "KFC Durbar Marg",             15.60, "Lunch"),
        (17, "expense", "🍔 Dining",        "OR2K Restaurant",             38.00, "Team dinner"),
        (20, "expense", "🍔 Dining",        "Starbucks",                    7.20, "Coffee & snack"),
        (25, "expense", "🍔 Dining",        "Local Momos Stall",            4.50, "Street food"),
        (28, "expense", "🍔 Dining",        "Himalayan Java",              11.00, "Working from cafe"),
        ( 3, "expense", "🚗 Transport",     "Pathao Ride",                  8.50, "Office commute"),
        ( 6, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        (11, "expense", "🚗 Transport",     "Pathao Ride",                  6.20, "Evening ride"),
        (18, "expense", "🚗 Transport",     "Micro Bus Pass",              12.00, "Monthly pass top-up"),
        (24, "expense", "🚗 Transport",     "Indreni Fuel Station",        45.00, "Fuel top-up"),
        ( 7, "expense", "💊 Health",        "Norvic Hospital",             80.00, "Check-up & lab tests"),
        (14, "expense", "💊 Health",        "Himalaya Drug Store",         23.40, "Medicines"),
        (21, "expense", "💊 Health",        "Anytime Fitness",             30.00, "Gym monthly"),
        ( 5, "expense", "🎬 Entertainment", "Netflix",                     15.49, "Monthly subscription"),
        ( 5, "expense", "🎬 Entertainment", "Spotify",                      9.99, "Monthly subscription"),
        (10, "expense", "🎬 Entertainment", "QFX Cinemas",                 14.00, "Movie night"),
        (19, "expense", "🎬 Entertainment", "Steam",                       29.99, "Game purchase"),
        (26, "expense", "🎬 Entertainment", "YouTube Premium",              6.99, "Monthly subscription"),
        (13, "expense", "🛍️ Shopping",     "Daraz Online",                55.00, "Shoes"),
        (20, "expense", "🛍️ Shopping",     "CG Electronics",             120.00, "Keyboard"),
        (27, "expense", "🛍️ Shopping",     "Daraz Online",                28.75, "Phone case & cables"),
    ],
}

RAW_GOALS = [
    {
        "title":          "Emergency Fund",
        "target_amount":  5000.00,
        "current_amount": 2150.00,
        "deadline":       datetime(2025, 12, 31),
    },
    {
        "title":          "Laptop Upgrade",
        "target_amount":  1200.00,
        "current_amount":  480.00,
        "deadline":       datetime(2025, 9, 1),
    },
    {
        "title":          "Trip to Pokhara",
        "target_amount":   800.00,
        "current_amount":  310.00,
        "deadline":       datetime(2025, 10, 15),
    },
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing = db.query(User).filter(User.email == DEMO_USER["email"]).first()
    if existing:
        print(f"  ↳ Removing existing demo user (id={existing.id}) …")
        db.delete(existing)
        db.commit()

    user = User(
        name                 = DEMO_USER["name"],
        email                = DEMO_USER["email"],
        password             = hash_password(DEMO_USER["password"]),
        phone                = DEMO_USER["phone"],
        dob                  = DEMO_USER["dob"],
        monthly_income       = DEMO_USER["monthly_income"],
        monthly_savings_goal = DEMO_USER["monthly_savings_goal"],
        created_at           = datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    db.add(user)
    db.flush()
    print(f"  ✔ Demo user created  →  id={user.id}  email={user.email}")

    total_count = 0
    for month, transactions in MONTHLY_TRANSACTIONS.items():
        income_total  = sum(a for (_, t, *_, a, __) in transactions if t == "income")
        expense_total = sum(a for (_, t, *_, a, __) in transactions if t == "expense")
        for (day, t_type, category, merchant, amount, desc) in transactions:
            tx = Transaction(
                amount      = amount,
                category    = category,
                merchant    = merchant,
                date        = datetime(2025, month, day, 10, 0, 0),
                type        = t_type,
                description = desc,
                user_id     = user.id,
            )
            db.add(tx)
        total_count += len(transactions)
        print(f"  ✔ Month {month:02d}/2025 → {len(transactions):2d} transactions | Income: ${income_total:,.2f} | Expense: ${expense_total:,.2f} | Net: ${income_total - expense_total:,.2f}")

    print(f"  ✔ {total_count} total transactions inserted")

    for g in RAW_GOALS:
        goal = Goal(
            title          = g["title"],
            target_amount  = g["target_amount"],
            current_amount = g["current_amount"],
            deadline       = g["deadline"],
            created_at     = datetime(2025, 1, 1),
            user_id        = user.id,
        )
        db.add(goal)

    print(f"  ✔ {len(RAW_GOALS)} savings goals inserted")

    db.commit()
    db.close()

    print("\n✅  Done!  Login credentials for demo:")
    print(f"     Email   : {DEMO_USER['email']}")
    print(f"     Password: {DEMO_USER['password']}")


if __name__ == "__main__":
    print("\n🌱  Seeding demo data …\n")
    seed()
    print()