from kafka import KafkaProducer, KafkaConsumer
import json
import threading
import time

# Kafka broker address
bootstrap_servers = 'localhost:29092'

# Topics
order_topic = 'orders_topic'
response_topic = 'rider_responses'

producer = KafkaProducer(bootstrap_servers="localhost:29092")

# Function to simulate rider receiving notification and responding
def simulate_rider(rider_id):
    consumer = KafkaConsumer(order_topic,
                             bootstrap_servers=bootstrap_servers,
                             auto_offset_reset='latest',
                             group_id=f'rider_group_{rider_id}')
    # consumer_group = 'rider_group'
    # consumer = KafkaConsumer(
    #     order_topic,
    #     bootstrap_servers=['localhost:29092'],
    #     group_id=consumer_group,
    #     auto_offset_reset='earliest',  # Start reading from the beginning of the topic
    #     enable_auto_commit=True,  # Commit offsets automatically
    #     value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    # )

    for message in consumer:
        # order_data = json.loads(message.value.decode('utf-8'))
        order_data = message.value
        print(f"Rider {rider_id} received order.")

        # Simulate rider deciding whether to accept or decline order
        response = input(f"Rider {rider_id}, do you accept this order? (yes/no): ").lower()
        while response not in ['yes', 'no']:
            print("Please type 'yes' or 'no'.")
            response = input(f"Rider {rider_id}, do you accept this order? (yes/no): ").lower()

        # Send response to Kafka topic
        producer.send(response_topic, json.dumps(response).encode("utf-8"))

# Function to simulate multiple riders
def simulate_riders(num_riders):
    threads = []
    for i in range(num_riders):
        t = threading.Thread(target=simulate_rider, args=(i + 1,))
        threads.append(t)
        t.start()

    # for t in threads:
    #     t.join()


# Example usage
if __name__ == "__main__":
    simulate_riders(3)
