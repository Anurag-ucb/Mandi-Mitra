-- ==========================================
-- KISAN SEVA / KISAN QUEUE DATABASE
-- ==========================================

PRAGMA foreign_keys = ON;

-- ==========================================
-- FARMERS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    village TEXT NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- PROCUREMENT CENTRES TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS centres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    village TEXT NOT NULL,
    address TEXT,
    capacity INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- CROPS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS crops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);


-- ==========================================
-- BOOKINGS / TOKENS TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    farmer_id INTEGER NOT NULL,
    crop_id INTEGER NOT NULL,
    centre_id INTEGER NOT NULL,

    weight REAL NOT NULL,

    token_number INTEGER NOT NULL,

    status TEXT DEFAULT 'Waiting',

    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (farmer_id)
        REFERENCES farmers(id)
        ON DELETE CASCADE,

    FOREIGN KEY (crop_id)
        REFERENCES crops(id)
        ON DELETE CASCADE,

    FOREIGN KEY (centre_id)
        REFERENCES centres(id)
        ON DELETE CASCADE
);


-- ==========================================
-- INDEXES
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_farmer_phone
ON farmers(phone);

CREATE INDEX IF NOT EXISTS idx_booking_farmer
ON bookings(farmer_id);

CREATE INDEX IF NOT EXISTS idx_booking_centre
ON bookings(centre_id);

CREATE INDEX IF NOT EXISTS idx_booking_status
ON bookings(status);