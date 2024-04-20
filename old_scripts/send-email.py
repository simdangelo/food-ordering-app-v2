import json
from kafka import KafkaConsumer
from common.kafka_topic import *

consumer = KafkaConsumer(
    ORDER_CONFIRMED_KAFKA_TOPIC,
    bootstrap_servers="localhost:29092"
)

email_sent_so_far = set()
print("Email is listening...\n")

while True:
    for message in consumer:
        consumed_message = json.loads(message.value.decode())
        customer_name = consumed_message["user"]
        customer_email = consumed_message["email"]

        print(f"Order is confirmed for {customer_name}. Sending email to {customer_email}. We'll send you another email when the order is READY")

        email_sent_so_far.add(customer_email)
        print(f"So far emails sent to {len(email_sent_so_far)} unique emails.\n")