import time
import psycopg2
import psycopg2.pool
import datetime
import random
import numpy as np

# Define global variables for database connection and connection pool
conn_pool = None
MAX_CONNECTIONS = 10

def create_postgres_connection():
    global conn_pool
    if conn_pool is None:
        conn_pool = psycopg2.pool.SimpleConnectionPool(
            1, MAX_CONNECTIONS,
            host='localhost',
            database='database',
            user='user',
            password='password',
            port=5432
        )
    return conn_pool.getconn(), conn_pool


def create_fake_orders(total_iterations):
    conn, _ = create_postgres_connection()
    cur = conn.cursor()

    for i in range(total_iterations):
        hour = int(random.gauss(13, 2)) if random.random() < 0.5 else int(random.gauss(20, 2))
        hour %= 24
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=830)
        random_day = start_date + datetime.timedelta(days=random.randint(0, 830))

        email = "user_" + str(random.randint(1, 1000)) + "@example.com"
        phone_number = '+39' + ''.join(str(random.randint(0, 9)) for _ in range(10))

        order_info = {}
        number_of_items = random.randint(2, 6)
        for _ in range(number_of_items):
            item_id = random.randint(1, 10)
            quantity = random.randint(1, 6)
            order_info[item_id] = quantity

        city = random.choice(["Milan", "Rome", "Naples", "Palermo"])
        order_datetime = datetime.datetime.combine(random_day, datetime.time(hour, minute, second))
        lambda_acceptance = 5  # Lambda for acceptance_order_timestamp
        lambda_completion = 10  # Lambda for completion_order_timestamp

        # Generate random variables from Poisson distributions
        acceptance_delay = np.random.poisson(lambda_acceptance)
        completion_delay = np.random.poisson(lambda_completion)

        # Add delays to order_datetime
        acceptance_order_timestamp = order_datetime + datetime.timedelta(minutes=acceptance_delay)
        completion_order_timestamp = acceptance_order_timestamp + datetime.timedelta(minutes=completion_delay)

        delivery_instructions = None

        order = {
            "email": email,
            "phone_number": phone_number,
            "order_data": order_info,
            "city": city,
            "order_created_timestamp": order_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "delivery_instructions": delivery_instructions,
            "acceptance_order_timestamp": acceptance_order_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "completion_order_timestamp": completion_order_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            cur.execute("""
                            INSERT INTO food_ordering.users (email, phone_number, city, registration_date)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (email) DO NOTHING;
                        """, (order['email'], order['phone_number'], order['city'], order['order_created_timestamp']))

            total_amount = 0
            order_details = []

            for item_id, quantity in order['order_data'].items():
                cur.execute("SELECT price FROM food_ordering.menu_items WHERE item_id = %s", (item_id,))
                cost = cur.fetchone()[0]
                subtotal = cost * quantity
                total_amount += subtotal
                order_details.append((item_id, quantity, subtotal))

            cur.execute("""
                            INSERT INTO food_ordering.orders (user_id, order_created_timestamp, total_amount, status, delivery_city, delivery_instructions)
                            VALUES ((SELECT user_id FROM food_ordering.users WHERE email = %s), %s, %s, %s, %s, %s)
                            RETURNING order_id;
                            """, (
                order['email'], order['order_created_timestamp'], total_amount, 'pending', order['city'],
                order.get('delivery_instructions', None)))

            order_id = cur.fetchone()[0]

            cur.execute("""
                            INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_timestamp)
                            VALUES (%s, %s, %s, %s)
                            """,
                        (order_id, 'pending', None, order['order_created_timestamp']))

            cur.executemany("""
                            INSERT INTO food_ordering.order_details (order_id, item_id, quantity, subtotal)
                            VALUES (%s, %s, %s, %s);
                            """,
                            [(order_id, item_id, quantity, subtotal) for item_id, quantity, subtotal in order_details])

            conn.commit()

            print(f"Progress: {i + 1}/{total_iterations}")
        except psycopg2.Error as e:
            conn.rollback()
            print("Error inserting data:", e)
    conn_pool.putconn(conn)


if __name__ == "__main__":
    total_iterations = 50000
    start_time = time.time()
    create_fake_orders(total_iterations)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
