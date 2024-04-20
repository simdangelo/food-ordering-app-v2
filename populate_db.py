import psycopg2
import datetime
import random
from common.postgres_connection import create_postgres_connection
import numpy as np


def create_fake_order():

    total_iterations = 50000
    for i in range(total_iterations):

        conn, cur = create_postgres_connection()

        hour = int(random.gauss(13, 2)) if random.random() < 0.5 else int(random.gauss(20, 2))
        hour %= 24
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=830)
        random_day = start_date + datetime.timedelta(days=random.randint(0, 830))

        email = "user_" + str(random.randint(1, 1000)) + "@example.com"
        phone_number = '+39' + ''.join(str(random.randint(0,9)) for _ in range(10))

        order_data = {}
        number_of_items = random.randint(2, 6)
        for _ in range(1, number_of_items, 1):
            item_id = random.randint(1, 10)
            quantity = random.randint(1, 6)
            order_data[item_id] = quantity

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
            "order_data": order_data,
            "city": city,
            "order_datetime": order_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "delivery_instructions": delivery_instructions,
            "acceptance_order_timestamp": acceptance_order_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "completion_order_timestamp": completion_order_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            cur.execute("""
                            INSERT INTO food_ordering.users (email, phone_number, city, registration_date)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (email) DO NOTHING;
                        """, (order['email'], order['phone_number'], order['city'], order['order_datetime']))

            total_amount = 0  # Initialize total amount
            order_details = []  # store data details for the current order to store it into Order_Details table

            # order['order_data'] is a dictionary with "item_id" as key and "quantity" as value
            for item_id, quantity in order['order_data'].items():
                cur.execute("SELECT price FROM food_ordering.menu_items WHERE item_id = %s", (item_id,))
                cost = cur.fetchone()[0]
                subtotal = cost * quantity  # cost of each specific item
                total_amount = total_amount + (cost * quantity)  # cost of the entire order

                # Append order details of each specific item of this order -> 2 item in the order means 2 elements in this list
                order_details.append((item_id, quantity, subtotal))

            # Inserting data into ORDERS table (1 row per order)
            cur.execute("""
                        INSERT INTO food_ordering.orders (user_id, order_timestamp, total_amount, status, delivery_city, delivery_instructions, acceptance_order_timestamp, completion_order_timestamp)
                        VALUES ((SELECT user_id FROM food_ordering.Users WHERE email = %s), %s, %s, %s, %s, %s, %s, %s);
                        """, (order['email'], order['order_datetime'], total_amount, 'pending', order['city'],
                              order.get('delivery_instructions', None), order["acceptance_order_timestamp"], order["completion_order_timestamp"]))

            # fetch the order_id of the order just done
            cur.execute("""
                            SELECT order_id FROM food_ordering.orders ORDER BY order_id DESC;
                        """)
            order_id = cur.fetchone()[0]

            # inserting data into ORDER_DETAILS about each item in this order
            cur.executemany("""
                                INSERT INTO food_ordering.order_details (order_id, item_id, quantity, subtotal)
                                VALUES (%s, %s, %s, %s);
                                """,
                            [(order_id, item_id, quantity, subtotal) for item_id, quantity, subtotal in order_details])

            conn.commit()

            print(f"Progress: {i + 1}/{total_iterations}")
        #     return True
        except psycopg2.Error as e:
            conn.rollback()
            print("Error inserting data:", e)
        #     return False
        # finally:
        #     cur.close()
        #     conn.close()



if __name__ == "__main__":

    create_fake_order()