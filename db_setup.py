"""
SQLite Database Setup Script for Event Planning System
Creates tables and optionally seeds sample data
"""

import sqlite3
from pathlib import Path
from typing import Optional


def create_database(db_path: str = "event_planning.db"):
    """
    Create the SQLite database with moderators and participants tables.
    
    Args:
        db_path: Path to the database file
    """
    # Check if database already exists
    db_file = Path(db_path)
    if db_file.exists():
        print(f"Database already exists at: {db_path}")
        response = input("Do you want to recreate it? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Keeping existing database.")
            return
        db_file.unlink()
        print("Deleted existing database.")
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Creating database at: {db_path}")
    
    # Create moderators table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moderators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT,
            description TEXT,
            email TEXT,
            phone TEXT,
            expertise TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created 'moderators' table")
    
    # Create participants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            company TEXT,
            role TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created 'participants' table")
    
    # Create indexes for better query performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_moderators_name 
        ON moderators(name)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_moderators_expertise 
        ON moderators(expertise)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_participants_name 
        ON participants(name)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_participants_email 
        ON participants(email)
    """)
    print("✓ Created indexes")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Database created successfully at: {db_path}")


def seed_sample_data(db_path: str = "event_planning.db"):
    """
    Seed the database with sample moderators and participants.
    
    Args:
        db_path: Path to the database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nSeeding sample data...")
    
    # Sample moderators
    sample_moderators = [
        ("Jai Kumar", "Hyderabad", "Experienced technical event moderator with 10+ years", 
         "jai.kumar@example.com", "+91-9876543210", "Technical, AI/ML, Cloud Computing"),
        ("Priya Sharma", "Bangalore", "Expert in corporate events and team building activities",
         "priya.sharma@example.com", "+91-9876543211", "Corporate, Team Building, Leadership"),
        ("Rahul Verma", "Mumbai", "Specialist in tech conferences and workshops",
         "rahul.verma@example.com", "+91-9876543212", "Conferences, Workshops, Technology"),
        ("Anita Desai", "Delhi", "Professional moderator for academic and research events",
         "anita.desai@example.com", "+91-9876543213", "Academic, Research, Science"),
        ("Vikram Singh", "Chennai", "Creative events and cultural program coordinator",
         "vikram.singh@example.com", "+91-9876543214", "Cultural, Creative, Entertainment")
    ]
    
    cursor.executemany("""
        INSERT INTO moderators (name, city, description, email, phone, expertise)
        VALUES (?, ?, ?, ?, ?, ?)
    """, sample_moderators)
    print(f"✓ Added {len(sample_moderators)} sample moderators")
    
    # Sample participants
    sample_participants = [
        ("Alice Smith", "alice.smith@techcorp.com", "TechCorp", "Software Engineer", "+1-555-0101"),
        ("Bob Johnson", "bob.johnson@innovate.com", "Innovate Inc", "Product Manager", "+1-555-0102"),
        ("Carol White", "carol.white@datalytics.com", "DataLytics", "Data Scientist", "+1-555-0103"),
        ("David Brown", "david.brown@cloudnet.com", "CloudNet", "DevOps Engineer", "+1-555-0104"),
        ("Emma Davis", "emma.davis@aitech.com", "AI Tech", "ML Engineer", "+1-555-0105"),
        ("Frank Miller", "frank.miller@startup.io", "StartupIO", "CTO", "+1-555-0106"),
        ("Grace Lee", "grace.lee@enterprise.com", "Enterprise Co", "Architect", "+1-555-0107"),
        ("Henry Wilson", "henry.wilson@solutions.com", "Solutions Ltd", "Consultant", "+1-555-0108"),
        ("Iris Taylor", "iris.taylor@innovation.com", "Innovation Labs", "Researcher", "+1-555-0109"),
        ("Jack Anderson", "jack.anderson@digital.com", "Digital Corp", "Team Lead", "+1-555-0110")
    ]
    
    cursor.executemany("""
        INSERT INTO participants (name, email, company, role, phone)
        VALUES (?, ?, ?, ?, ?)
    """, sample_participants)
    print(f"✓ Added {len(sample_participants)} sample participants")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Sample data seeded successfully!")


def view_database_contents(db_path: str = "event_planning.db"):
    """
    Display the contents of the database.
    
    Args:
        db_path: Path to the database file
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("MODERATORS TABLE")
    print("="*60)
    cursor.execute("SELECT * FROM moderators")
    moderators = cursor.fetchall()
    
    if moderators:
        for mod in moderators:
            print(f"\nID: {mod['id']}")
            print(f"Name: {mod['name']}")
            print(f"City: {mod['city']}")
            print(f"Email: {mod['email']}")
            print(f"Expertise: {mod['expertise']}")
            print(f"Description: {mod['description']}")
            print("-" * 40)
    else:
        print("No moderators found.")
    
    print("\n" + "="*60)
    print("PARTICIPANTS TABLE")
    print("="*60)
    cursor.execute("SELECT * FROM participants")
    participants = cursor.fetchall()
    
    if participants:
        for part in participants:
            print(f"\nID: {part['id']}")
            print(f"Name: {part['name']}")
            print(f"Email: {part['email']}")
            print(f"Company: {part['company']}")
            print(f"Role: {part['role']}")
            print("-" * 40)
    else:
        print("No participants found.")
    
    conn.close()


def add_moderator(
    db_path: str,
    name: str,
    city: str,
    description: str,
    email: str,
    phone: Optional[str] = None,
    expertise: Optional[str] = None
):
    """Add a single moderator to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO moderators (name, city, description, email, phone, expertise)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, city, description, email, phone, expertise))
    
    conn.commit()
    conn.close()
    print(f"✓ Added moderator: {name}")


def add_participant(
    db_path: str,
    name: str,
    email: str,
    company: Optional[str] = None,
    role: Optional[str] = None,
    phone: Optional[str] = None
):
    """Add a single participant to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO participants (name, email, company, role, phone)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, company, role, phone))
        
        conn.commit()
        print(f"✓ Added participant: {name}")
    except sqlite3.IntegrityError:
        print(f"✗ Participant with email {email} already exists!")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    db_path = "event_planning.db"
    
    print("="*60)
    print("EVENT PLANNING DATABASE SETUP")
    print("="*60)
    
    # Create database
    create_database(db_path)
    
    # Ask if user wants to seed sample data
    response = input("\nDo you want to add sample data? (yes/no): ").strip().lower()
    if response == 'yes':
        seed_sample_data(db_path)
        view_database_contents(db_path)
    
    print("\n" + "="*60)
    print("Setup complete! You can now use the database with your event planning system.")
    print(f"Database location: {Path(db_path).absolute()}")
    print("="*60)