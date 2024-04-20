from kafka import KafkaConsumer, KafkaProducer
import json
import psycopg2

# Kafka producer to send rider responses
response_producer = KafkaProducer(bootstrap_servers=['localhost:29092'],
                                  value_serializer=lambda x: json.dumps(x).encode('utf-8'))


def create_postgres_connection():
    # Function to create a connection to PostgreSQL
    conn = psycopg2.connect(
        host='localhost',
        database='database',
        user='user',
        password='password',
        port=5432
    )
    cursor = conn.cursor()
    return conn, cursor


def close_postgres_connection(conn, cursor):
    # Function to close the connection to PostgreSQL
    cursor.close()
    conn.close()


def get_active_riders():
    # Function to retrieve active riders from the database
    conn, cursor = create_postgres_connection()
    cursor.execute("SELECT rider_id FROM food_ordering.riders")
    active_riders = [row[0] for row in cursor.fetchall()]
    close_postgres_connection(conn, cursor)
    return active_riders


def update_order_status(order_id, status):
    # Function to update order status in the database
    conn, cursor = create_postgres_connection()
    cursor.execute("UPDATE food_ordering.orders SET status = %s WHERE order_id = %s", (status, order_id))
    conn.commit()
    close_postgres_connection(conn, cursor)


def rider_consumer():
    consumer_group = 'rider_group'
    order_topic = 'orders_topic'
    response_topic = 'rider_responses_topic'

    consumer = KafkaConsumer(
        order_topic,
        bootstrap_servers=['localhost:29092'],
        group_id=consumer_group,
        auto_offset_reset='earliest',  # Start reading from the beginning of the topic
        enable_auto_commit=True,  # Commit offsets automatically
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    for message in consumer:
        order = message.value

        conn, cursor = create_postgres_connection()
        cursor.execute("""
                        SELECT order_id FROM food_ordering.orders ORDER BY order_id DESC;
                    """)
        order_id = cursor.fetchone()[0]

        active_riders = get_active_riders()

        for rider_id in active_riders:
            # Simulate rider processing order
            print(f"Rider {rider_id} received order: {order}")

            # Send rider response to Kafka
            response_message = {
                "rider_id": rider_id,
                "order_id": order_id,
                "order_details": order
            }
            response_producer.send(response_topic, response_message)
            print(f"Rider {rider_id} processing order: {order_id}")

            # Wait for rider response
            consumer_response = KafkaConsumer(
                response_topic,
                bootstrap_servers=['localhost:29092'],
                group_id=f'rider_response_group_{rider_id}',
                auto_offset_reset='earliest',  # Start reading from the beginning of the topic
                enable_auto_commit=True,  # Commit offsets automatically
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )

            for response_message in consumer_response:
                response = response_message.value
                if response['order_id'] == order_id:
                    if response['rider_id'] == rider_id:
                        rider_response = input(f"Rider {rider_id}, do you accept order {order_id}? (Yes/No): ").lower()
                        if rider_response == 'yes':
                            update_order_status(order_id, "Pending to accept")
                            print(f"Order {order_id} status updated to 'Pending to accept'")
                            consumer_response.close()
                            break
                        elif rider_response == 'no':
                            print(f"Rider {rider_id} rejected order {order_id}")
                            consumer_response.close()
                            break


# Call the rider_consumer function directly
rider_consumer()
