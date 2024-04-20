import json
from kafka import KafkaConsumer
from kafka import KafkaProducer
from common.kafka_topic import *


producer = KafkaProducer(
    bootstrap_servers="localhost:29092"
)

consumer = KafkaConsumer(
    ORDER_CONFIRMED_KAFKA_TOPIC,
    bootstrap_servers="localhost:29092"
)


print("Transactions listening...\n")
while True:
    for message in consumer:
        consumed_message = json.loads(message.value.decode())

        user = consumed_message["user"]
        email = consumed_message["email"]
        food = consumed_message["food"]
        size = consumed_message["size"]
        food_cost = consumed_message["cost"]
        time = consumed_message["time"]

        print(f"Order by: {user}: {food} (size {size}). Cost: {food_cost}. Order time: {time}\n")

        # data = {
        #     "customer_name": user,
        #     "customer_email": email,
        #     "food_cost": food_cost
        # }
        
        # producer.send(
        #     ORDER_CONFIRMED_KAFKA_TOPIC,
        #     json.dumps(data).encode("utf-8")
        # )