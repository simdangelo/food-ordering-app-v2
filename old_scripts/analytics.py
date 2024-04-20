import json

from kafka import KafkaConsumer
from common.kafka_topic import *

consumer = KafkaConsumer(
    bootstrap_servers="localhost:29092"
)
consumer.subscribe([ORDER_CONFIRMED_KAFKA_TOPIC, ORDER_COMPLETED_KAFKA_TOPIC])

from cassandra.cluster import Cluster

cluster = Cluster(['localhost'])
session = cluster.connect()


def calculate_active_orders():
    result = session.execute("SELECT COUNT(*) FROM spark_streams.orders WHERE order_completed = 0 ALLOW FILTERING")
    return result.one()[0]

def calculate_orders_today():
    result = session.execute("SELECT COUNT(*) FROM spark_streams.orders")
    return result.one()[0] or 0

def calculate_total_revenue():
    result = session.execute("SELECT SUM(cost) FROM spark_streams.orders")
    return result.one()[0] or 0


print("Analytics listening...\n")


for message in consumer:
    if message.topic == ORDER_CONFIRMED_KAFKA_TOPIC:
        # time.sleep(0.5)
        # consumed_message = json.loads(message.value.decode())

        total_orders_count_today = calculate_orders_today()
        total_revenue = calculate_total_revenue()

        print("A NEW order has just been made!")
        print(f"Orders so far today: {total_orders_count_today}") # +1 because otherwise the order is not yet in the database. I don't understand why instead it shows the right "Orders still active" value when I click the button. I expect the same problem as here.
        print(f"Revenue so far: {total_revenue}")
        print("\n")


    elif message.topic == ORDER_COMPLETED_KAFKA_TOPIC:
        consumed_message = json.loads(message.value.decode())

        active_orders = calculate_active_orders()

        order_id = consumed_message["order_id"]
        email_id = consumed_message["email_id"]

        print(f"The order {order_id} is just COMPLETED and an email is sent to {email_id}!")
        print(f"Orders still active: {active_orders}!!")
        print("\n")
