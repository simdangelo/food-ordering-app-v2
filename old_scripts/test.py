# from kafka import KafkaConsumer, KafkaProducer
# import json
# import time
# import threading
#
# # Kafka setup
# bootstrap_servers = 'localhost:9092'
# group_id = 'riders_group'
# order_topic = 'new_orders'
# response_topic = 'order_responses'
#
# # Create Kafka consumer and producer
# consumer = KafkaConsumer(
#     order_topic,
#     group_id=group_id,
#     bootstrap_servers=bootstrap_servers,
#     auto_offset_reset='earliest',
#     enable_auto_commit=True,
#     value_deserializer=lambda x: json.loads(x.decode('utf-8'))
# )
# producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
#                          value_serializer=lambda x: json.dumps(x).encode('utf-8'))
#
# # Dictionary to track accepted orders
# accepted_orders = {}
#
#
# def process_order(order_info):
#     print("New Order: ", order_info['message'])
#
#     # Simulate processing time
#     print("Simulating order processing...")
#     time.sleep(5)  # Simulate processing time
#
#     # Simulate order completion
#     print("Order completed!")
#
#
# def handle_order_acceptance(order_id, rider_id):
#     print(f"Rider {rider_id} accepted order {order_id}")
#
#     # Add order to accepted_orders dictionary
#     accepted_orders[order_id] = rider_id
#
#     # Publish response to response topic
#     response_msg = {
#         'order_id': order_id,
#         'rider_id': rider_id,
#         'status': 'accepted'
#     }
#     producer.send(response_topic, value=response_msg)
#
#
# def handle_order_rejection(order_id, rider_id):
#     print(f"Rider {rider_id} rejected order {order_id}")
#
#     # Publish response to response topic
#     response_msg = {
#         'order_id': order_id,
#         'rider_id': rider_id,
#         'status': 'rejected'
#     }
#     producer.send(response_topic, value=response_msg)
#
#
# def wait_for_response(order_id, rider_id):
#     while True:
#         response = input(f"Rider {rider_id}, do you want to accept this order? (yes/no): ").lower()
#         if response == 'yes':
#             handle_order_acceptance(order_id, rider_id)
#             break
#         elif response == 'no':
#             handle_order_rejection(order_id, rider_id)
#             break
#         else:
#             print("Invalid response. Please enter 'yes' or 'no'.")
#
#
# def process_message(msg):
#     order_info = msg.value
#     order_id = order_info['order_id']
#     rider_id = order_info['rider_id']
#
#     process_order(order_info)
#
#     # Prompt rider for acceptance
#     response_thread = threading.Thread(target=wait_for_response, args=(order_id, rider_id))
#     response_thread.start()
#
#
# def rider_simulation():
#     for msg in consumer:
#         process_message(msg)
#
#
# # Simulate multiple riders with threads
# NUM_RIDERS = 3
# threads = []
# for i in range(NUM_RIDERS):
#     t = threading.Thread(target=rider_simulation)
#     threads.append(t)
#     t.start()
#
# try:
#     for t in threads:
#         t.join()
# except KeyboardInterrupt:
#     pass
#
# finally:
#     # Close the consumer and producer
#     # consumer.close()
#     # producer.close()
#     print("ok")

import psycopg2
from common.postgres_connection import create_postgres_connection

def add_menu_item(name, description, price, category):
    try:
        connection, cursor = create_postgres_connection()

        cursor.execute("""
            INSERT INTO food_ordering.Menu_Items (name, description, price, category)
            VALUES (%s, %s, %s, %s)
        """, (name, description, price, category))

        connection.commit()
        cursor.close()
        connection.close()
        print("Menu item added successfully.")
    except (Exception, psycopg2.Error) as error:
        print("Error adding menu item:", error)

# Example usage:
add_menu_item("Cheeseburger", "Juicy beef patty with cheese", 221.99, "as")
add_menu_item("Margherita Pizza", "Classic pizza with tomato sauce and mozzarella", 421.99, "s")
add_menu_item("Caesar Salad", "Fresh romaine lettuce with Caesar dressing", 112.49, "sssss")