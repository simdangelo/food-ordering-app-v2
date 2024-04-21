from kafka import KafkaConsumer
import psycopg2
from common.postgres_connection import create_postgres_connection
from common.kafka_topic import ORDERS_KAFKA_TOPIC
from common.global_variables import N_RIDERS
import json
from datetime import datetime

# Constants
bootstrap_servers = 'localhost:29092'
rider_id = "1"

# Open database connection
connection, cursor = create_postgres_connection()


def get_rider_name(cursor, rider_id):
    cursor.execute("SELECT name FROM food_ordering.riders WHERE rider_id = %s;", (rider_id,))
    rider_name = cursor.fetchone()[0]
    return rider_name


def update_and_add_order_status(cursor, order_id, new_status, rider_id, change_status_timestamp):
    try:
        # cursor.execute("SELECT status FROM food_ordering.orders_status WHERE order_id = %s;", (order_id,))
        cursor.execute(f"""
                        with tmp as (
                            SELECT 
                                COUNT(DISTINCT CASE WHEN status = 'accepted' THEN rider_id END) AS accepted_count,
                                COUNT(DISTINCT CASE WHEN status = 'denied' THEN rider_id END) AS denied_count
                            FROM food_ordering.orders_status
                                WHERE order_id = {order_id}
                                GROUP BY order_id
                            )
                        SELECT
                            (CASE WHEN accepted_count = 1 or denied_count={N_RIDERS} THEN 'not_pending' ELSE 'pending' END) as status
                        from tmp
                        """)
        current_status = cursor.fetchone()[0]


        if current_status == 'not_pending':
            print("Some other rider has already accepted or denied this order before you. Sorry! Please try again with your next order!\n")
        else:
            cursor.execute("""
                            INSERT INTO food_ordering.orders_status (order_id, status, event_timestamp, rider_id)
                            VALUES (%s, %s, %s, %s)
                            """,
                       (order_id, new_status, change_status_timestamp, rider_id))
            connection.commit()
            if new_status == "accepted":
                print("Order accepted!\n")
            else:
                print("Order denied!\n")

    except psycopg2.Error as e:
        print("Error updating order status:", e)
        connection.rollback()


def orders_still_active(cursor):
    cursor.execute(f"""
            WITH order_status_count AS (
                SELECT 
                    order_id,
                    COUNT(DISTINCT CASE WHEN status = 'denied' THEN rider_id END) AS denied_count,
                    COUNT(DISTINCT CASE WHEN status = 'accepted' THEN rider_id END) AS accepted_count
                FROM food_ordering.orders_status
                GROUP BY order_id
            )
            SELECT COUNT(DISTINCT order_id) AS active_orders
            FROM order_status_count
            WHERE accepted_count = 0 AND denied_count < {N_RIDERS};
            """)
    pending_orders = cursor.fetchone()[0]
    return pending_orders


# Main loop to consume messages from Kafka
def main():
    consumer = KafkaConsumer(ORDERS_KAFKA_TOPIC, bootstrap_servers=bootstrap_servers)

    for message in consumer:
        consumed_message = json.loads(message.value.decode())

        print("Received order n.:", consumed_message["order_id"])
        print("Order details:", consumed_message)

        # Prompt user to accept or deny order
        rider_name = get_rider_name(cursor, rider_id)
        decision = ""
        while decision not in ['yes', 'no']:
            decision = input(
                f"{rider_name} (rider_id {rider_id}), do you want to accept this order? (yes/no): ").lower()
            change_status_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if decision == 'yes':
                update_and_add_order_status(cursor, consumed_message["order_id"], 'accepted', rider_id, change_status_timestamp)
                active_orders = orders_still_active(cursor)
                print(f"Orders still active_orders: {active_orders}\n")

            elif decision == 'no':
                update_and_add_order_status(cursor, consumed_message["order_id"], 'denied', rider_id, change_status_timestamp)
                active_orders = orders_still_active(cursor)
                print(f"Orders still active_orders: {active_orders}\n")

            else:
                print("Invalid input. Please type 'yes' or 'no'.")


if __name__ == "__main__":
    main()

# Close database connection
cursor.close()
connection.close()
