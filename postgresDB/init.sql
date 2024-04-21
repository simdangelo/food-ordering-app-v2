DROP SCHEMA IF EXISTS food_ordering CASCADE;
-- Create the food_ordering schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS food_ordering;

-- Set the search path to include the food_ordering schema
SET search_path TO food_ordering;

-- Create Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    city TEXT NOT NULL,
--    address TEXT NOT NULL, -- we deal only with city and not address
--    password_hash VARCHAR(255) -- we do not deal with authentication for now
    registration_date DATE DEFAULT CURRENT_DATE
);

-- Create status table
CREATE TABLE IF NOT EXISTS status (
    status_id SERIAL PRIMARY KEY,
    status_description VARCHAR(50) NOT NULL
);

-- Insert specific records into the Status table
INSERT INTO status (status_description) VALUES
    ('pending'),
    ('accepted'),
    ('denied');

---- Create Riders table
CREATE TABLE IF NOT EXISTS riders (
    rider_id INTEGER PRIMARY KEY, -- rider_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    vehicle_type VARCHAR(50),
    vehicle_registration VARCHAR(50)
);

INSERT INTO riders (rider_id, name, password, phone_number, vehicle_type)
VALUES
    (1, 'Fabio', 'fabio', '2345324532', 'auto'),
    (2, 'Simone', 'simone', '2253523532', 'moto'),
    (3, 'Matteo', 'matteo', '2253523532', 'auto'),
    (4, 'Alessandro', 'alessandro', '2253523532', 'moto');

-- Create Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50),
--    delivery_address TEXT, -- we deal only with city and not address
    delivery_city TEXT,
    delivery_instructions TEXT, -- eventual notes for the rider by the user
    order_created_timestamp TIMESTAMP,
    order_accepted_timestamp TIMESTAMP,
    order_denied_timestamp TIMESTAMP,
    order_completed_timestamp TIMESTAMP,
    rider_id INTEGER REFERENCES riders(rider_id)
);

-- Create Orders Status table
CREATE TABLE IF NOT EXISTS orders_status (
    order_status_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    status VARCHAR(50),
    rider_id INTEGER REFERENCES riders(rider_id),
    event_timestamp TIMESTAMP
);


-- Create Menu_Items table
CREATE TABLE IF NOT EXISTS menu_items (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL,
    category VARCHAR(50),
    date_added DATE DEFAULT CURRENT_DATE
);

INSERT INTO menu_items (name, description, price, category)
VALUES
    ('Margherita Pizza', 'Classic tomato sauce, mozzarella, basil', 9.99, 'Pizza'),
    ('Pepperoni Pizza', 'Tomato sauce, mozzarella, pepperoni', 11.99, 'Pizza'),
    ('Chicken Caesar Salad', 'Grilled chicken, romaine lettuce, croutons, parmesan cheese, Caesar dressing', 8.99, 'Salad'),
    ('Cheeseburger', 'Beef patty, cheddar cheese, lettuce, tomato, onion, pickles, mayo, ketchup', 10.99, 'Burger'),
    ('Vegetarian Wrap', 'Grilled vegetables, hummus, lettuce, tomato, cucumber, feta cheese, tzatziki sauce', 7.99, 'Wrap'),
    ('Roadhouse', 'Double Beef patty, double cheddar cheese, lettuce, tomato, chimera sauce', 14.99, 'Burger'),
    ('Wrong Margherita', 'Tomato sauce, mozzarella, basil cream', 14.99, 'Pizza'),
    ('Beef Wrap', 'Beef, potatoes, mayo, bacon', 7.99, 'Wrap'),
    ('Coca-Cola', Null, 3.5, 'Drink'),
    ('Water', Null, 2, 'Drink');


-- Create Order_Items table
CREATE TABLE IF NOT EXISTS order_details (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    item_id INTEGER REFERENCES menu_items(item_id),
    quantity INTEGER,
    subtotal NUMERIC(10, 2)
);


--
---- Create Delivery_Assignments table
--CREATE TABLE IF NOT EXISTS Delivery_Assignments (
--    assignment_id SERIAL PRIMARY KEY,
--    order_id INTEGER REFERENCES Orders(order_id),
--    rider_id INTEGER REFERENCES Riders(rider_id),
--    assignment_status VARCHAR(50),
--    delivery_start_time TIMESTAMP,
--    delivery_end_time TIMESTAMP
--);
--
---- Create Reviews table
--CREATE TABLE IF NOT EXISTS Reviews (
--    review_id SERIAL PRIMARY KEY,
--    user_id INTEGER REFERENCES Users(user_id),
--    rating INTEGER,
--    comment TEXT,
--    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
--);
--
---- Create Favorites table
--CREATE TABLE IF NOT EXISTS Favorites (
--    favorite_id SERIAL PRIMARY KEY,
--    user_id INTEGER REFERENCES Users(user_id),
--    item_id INTEGER REFERENCES Menu_Items(item_id),
--);
--
---- Create Promotions table
--CREATE TABLE IF NOT EXISTS Promotions (
--    promotion_id SERIAL PRIMARY KEY,
--    start_date DATE,
--    end_date DATE,
--    discount_percent NUMERIC(5, 2),
--    promo_code VARCHAR(20)
--);

-- Reset the search path to the default
RESET search_path;
