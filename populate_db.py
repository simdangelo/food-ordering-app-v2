import time
import psycopg2
import psycopg2.pool
import datetime
import random
import numpy as np
from common.global_variables import N_RIDERS
from common.postgres_connection import create_postgres_connection

# Define global variables for database connection and connection pool
conn_pool = None
MAX_CONNECTIONS = 10

# def create_postgres_connection():
#     global conn_pool
#     if conn_pool is None:
#         conn_pool = psycopg2.pool.SimpleConnectionPool(
#             1, MAX_CONNECTIONS,
#             host='localhost',
#             database='database',
#             user='user',
#             password='password',
#             port=5432
#         )
#     return conn_pool.getconn(), conn_pool


def add_deny(order_id, refusal_timestamp):
    conn, _ = create_postgres_connection()
    cur = conn.cursor()

    for i in range(1, N_RIDERS):
        cur.execute("""
                    INSERT INTO food_ordering.orders_status (order_id, status, event_timestamp)
                    VALUES (%s, %s, %s)
                    """,
                    (order_id, 'denied', i, refusal_timestamp))


def create_fake_orders(total_iterations):
    conn, _ = create_postgres_connection()
    cur = conn.cursor()

    for iteration in range(total_iterations):
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

        delivery_instructions = None

        order = {
            "email": email,
            "phone_number": phone_number,
            "order_data": order_info,
            "city": city,
            "delivery_instructions": delivery_instructions,
        }

        creation_order_timestamp = order_datetime.strftime("%Y-%m-%d %H:%M:%S")

        try:
            cur.execute("""
                            INSERT INTO food_ordering.users (email, phone_number, city, registration_date)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (email) DO NOTHING;
                        """, (order['email'], order['phone_number'], order['city'], creation_order_timestamp))

            total_amount = 0
            order_details = []

            for item_id, quantity in order['order_data'].items():
                cur.execute("SELECT price FROM food_ordering.menu_items WHERE item_id = %s", (item_id,))
                cost = cur.fetchone()[0]
                subtotal = cost * quantity
                total_amount += subtotal
                order_details.append((item_id, quantity, subtotal))

            cur.execute("""
                            INSERT INTO food_ordering.orders (user_id, total_amount, status, delivery_city, delivery_instructions)
                            VALUES ((SELECT user_id FROM food_ordering.users WHERE email = %s), %s, %s, %s, %s)
                            RETURNING order_id;
                            """, (
                order['email'], total_amount, 'pending', order['city'],
                order.get('delivery_instructions', None)))

            order_id = cur.fetchone()[0]

            cur.execute("""
                            INSERT INTO food_ordering.orders_status (order_id, status, event_timestamp)
                            VALUES (%s, %s, %s)
                            """,
                        (order_id, 'pending', creation_order_timestamp))

            positive_or_negative = random.choices(["positive", "negative"], weights=[0.82, 0.18], k=1)[0]

            lambda_refusal = 5
            if positive_or_negative == 'negative':

                for i in range(1, N_RIDERS+1):
                    refusal_delay = np.random.poisson(lambda_refusal)
                    refusal_timestamp = order_datetime + datetime.timedelta(minutes=refusal_delay)
                    cur.execute("""
                                INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_timestamp)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (order_id, 'denied', i, refusal_timestamp))

            else:
                refusal_count = 0
                rider_id = None
                last_denied_timestamp = None
                refusal_delay = np.random.poisson(lambda_refusal)
                while refusal_count < N_RIDERS:
                    if refusal_count > 0:
                        refusal_delay = np.random.poisson(lambda_refusal)
                        refusal_timestamp = order_datetime + datetime.timedelta(minutes=refusal_delay)
                        cur.execute("""
                                    INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_timestamp)
                                    VALUES (%s, %s, %s, %s)
                                    """,
                                    (order_id, 'denied', rider_id, refusal_timestamp))
                        last_denied_timestamp = refusal_timestamp

                    rider_id = random.choices([1, 2, 3, 4], weights=[0.7, 0.2, 0.5, 0.1], k=1)[0]
                    # Check if the rider has already denied the order
                    cur.execute("""
                                SELECT COUNT(*)
                                FROM food_ordering.orders_status
                                WHERE order_id = %s AND rider_id = %s AND status = 'denied'
                                """,
                                (order_id, rider_id))
                    already_denied = cur.fetchone()[0] > 0
                    if not already_denied:
                        # Define acceptance probability with some randomness
                        acceptance_probability = random.uniform(0.2, 0.8)
                        # Check if the rider accepts the order
                        if random.random() < acceptance_probability:
                            accepted_timestamp = order_datetime + 1.5 * datetime.timedelta(minutes=refusal_delay)
                            cur.execute("""
                                        INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_timestamp)
                                        VALUES (%s, %s, %s, %s)
                                        """,
                                        (order_id, 'accepted', rider_id, accepted_timestamp))
                            completed_timestamp = order_datetime + 3*datetime.timedelta(minutes=refusal_delay)
                            cur.execute("""
                                        INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_timestamp)
                                        VALUES (%s, %s, %s, %s)
                                        """,
                                        (order_id, 'completed', rider_id, completed_timestamp))

                            break  # Exit the loop if the order is accepted
                        else:
                            refusal_count += 1
                # If all riders refuse, the last rider must accept
                if refusal_count == N_RIDERS:
                    cur.execute("""
                                INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_timestamp)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (order_id, 'accepted', rider_id, order_datetime))
                # Ensure that the accepted timestamp is greater than the last denied timestamp
                elif last_denied_timestamp:
                    cur.execute("""
                                UPDATE food_ordering.orders_status
                                SET event_timestamp = %s
                                WHERE order_id = %s AND status = 'accepted' AND rider_id = %s AND event_timestamp <= %s
                                """,
                                (order_datetime, order_id, rider_id, last_denied_timestamp))

            cur.executemany("""
                            INSERT INTO food_ordering.order_details (order_id, item_id, quantity, subtotal)
                            VALUES (%s, %s, %s, %s);
                            """,
                            [(order_id, item_id, quantity, subtotal) for item_id, quantity, subtotal in order_details])

            conn.commit()

            print(f"Progress: {iteration + 1}/{total_iterations}")
        except psycopg2.Error as e:
            conn.rollback()
            print("Error inserting data:", e)


if __name__ == "__main__":
    total_iterations = 50000
    start_time = time.time()
    create_fake_orders(total_iterations)
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
