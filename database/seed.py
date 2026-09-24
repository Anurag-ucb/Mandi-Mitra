import sqlite3
import os


# ==========================================
# DATABASE PATH
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, "database.db")
SCHEMA_FILE = os.path.join(
    BASE_DIR,
    "database",
    "schema.sql"
)


# ==========================================
# CREATE DATABASE
# ==========================================

def create_database():

    print("========================================")
    print("   KISAN SEVA DATABASE SETUP")
    print("========================================")

    # Connect to SQLite database
    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Read schema.sql
    with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
        schema = file.read()

    # Execute schema
    cursor.executescript(schema)

    print("\nDatabase tables created successfully.")


    # ======================================
    # INSERT CROPS
    # ======================================

    crops = [
        "Wheat",
        "Rice",
        "Maize",
        "Bajra",
        "Barley",
        "Mustard",
        "Potato",
        "Onion",
        "Sugarcane",
        "Cotton"
    ]

    for crop in crops:

        cursor.execute(
            """
            INSERT OR IGNORE INTO crops (name)
            VALUES (?)
            """,
            (crop,)
        )

    print("Crops added successfully.")


    # ======================================
    # INSERT PROCUREMENT CENTRES
    # ======================================

    centres = [
        (
            "Kisan Procurement Centre - Greater Noida",
            "Greater Noida",
            "Knowledge Park, Greater Noida",
            100
        ),

        (
            "Dadri Procurement Centre",
            "Dadri",
            "Main Market Road, Dadri",
            80
        ),

        (
            "Jewar Procurement Centre",
            "Jewar",
            "Agriculture Market, Jewar",
            100
        ),

        (
            "Dankaur Procurement Centre",
            "Dankaur",
            "Mandi Road, Dankaur",
            80
        ),

        (
            "Noida Procurement Centre",
            "Noida",
            "Sector 88 Agricultural Market, Noida",
            120
        )
    ]

    for centre in centres:

        cursor.execute(
            """
            INSERT INTO centres
            (
                name,
                village,
                address,
                capacity
            )
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM centres
                WHERE name = ?
            )
            """,
            (
                centre[0],
                centre[1],
                centre[2],
                centre[3],
                centre[0]
            )
        )

    print("Procurement centres added successfully.")


    # ======================================
    # DEMO FARMER
    # ======================================

    cursor.execute(
        """
        INSERT OR IGNORE INTO farmers
        (
            name,
            phone,
            village,
            password
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "Demo Farmer",
            "9876543210",
            "Greater Noida",
            "1234"
        )
    )

    print("Demo farmer added.")


    # ======================================
    # SAVE DATABASE
    # ======================================

    conn.commit()
    conn.close()

    print("\n========================================")
    print(" DATABASE CREATED SUCCESSFULLY")
    print("========================================")

    print("\nDemo Login:")
    print("Phone    : 9876543210")
    print("Password : 1234")

    print("\nDatabase location:")
    print(DATABASE)


# ==========================================
# RUN
# ==========================================

if __name__ == "__main__":
    create_database()