from kafka import KafkaConsumer
import psycopg2
from common.postgres_connection import create_postgres_connection
from common.kafka_topic import ORDERS_KAFKA_TOPIC
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


def update_order_status(cursor, order_id, new_status, rider_id, decision_timestamp):
    try:
        cursor.execute("SELECT status FROM food_ordering.orders WHERE order_id = %s;", (order_id,))
        current_status = cursor.fetchone()[0]

        if current_status == 'accepted':
            print(
                "Some other rider has already accepted or denied this order before you. Sorry! Please try again with your next order!\n")
        else:
            cursor.execute(
                "UPDATE food_ordering.orders SET status = %s, acceptance_order_timestamp = %s, rider_id = %s WHERE order_id = %s",
                (new_status, decision_timestamp, rider_id, order_id))

            cursor.execute("""
                        INSERT INTO food_ordering.orders_status (order_id, status, rider_id, event_time)
                        VALUES (%s, %s, %s, %s);
                        """, (order_id, new_status, rider_id, decision_timestamp))

            connection.commit()
            if new_status == 'accepted':
                print("Order accepted!\n")
            else:
                print("Order denied!\n")

    except psycopg2.Error as e:
        print("Error updating order status:", e)
        connection.rollback()


def orders_still_active(cursor):
    cursor.execute("SELECT count(*) FROM food_ordering.orders WHERE status != 'accepted'")
    pending_orders = cursor.fetchone()[0]
    return pending_orders


# Main loop to consume messages from Kafka
def main():
    consumer = KafkaConsumer(ORDERS_KAFKA_TOPIC, bootstrap_servers=bootstrap_servers)

    for message in consumer:
        consumed_message = json.loads(message.value.decode())

        cursor.execute("SELECT order_id FROM food_ordering.orders ORDER BY order_id DESC;")
        order_id = cursor.fetchone()[0]

        print("Received order n.:", order_id)
        print("Order details:", consumed_message)

        # Prompt user to accept or deny order
        rider_name = get_rider_name(cursor, rider_id)
        decision = ""
        while decision not in ['yes', 'no']:
            decision = input(f"{rider_name} (rider_id {rider_id}), do you want to accept this order? (yes/no): ").lower()
            decision_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if decision == 'yes':
                update_order_status(cursor, order_id, 'accepted', rider_id, decision_timestamp)
                active_orders = orders_still_active(cursor)
                print(f"Orders still active_orders: {active_orders}")

            elif decision == 'no':
                update_order_status(cursor, order_id, 'denied', rider_id, decision_timestamp)
                active_orders = orders_still_active(cursor)
                print(f"Orders still active_orders: {active_orders}")

            else:
                print("Invalid input. Please type 'yes' or 'no'.")


if __name__ == "__main__":
    main()

# Close database connection
cursor.close()
connection.close()
