import json
from datetime import datetime
import uuid
import time
from kafka import KafkaProducer
KAFKA_TOPIC_TEST = "topic_test"



#READ COORDINATES FROM GEOJSON
input_file = open('./data/bus1.json')
json_array = json.load(input_file)
coordinates = json_array['features'][0]['geometry']['coordinates']

#GENERATE UUID
def generate_uuid():
    return uuid.uuid4()

producer = KafkaProducer(bootstrap_servers="localhost:29092")


#CONSTRUCT MESSAGE AND SEND IT TO KAFKA
data = {}
data['busline'] = '00001'

def generate_checkpoint(coordinates):
    i = 0
    while i < len(coordinates):
        data['key'] = data['busline'] + '_' + str(generate_uuid())
        data['timestamp'] = str(datetime.utcnow())
        data['latitude'] = coordinates[i][1]
        data['longitude'] = coordinates[i][0]
        print(data)
        producer.send(KAFKA_TOPIC_TEST, json.dumps(data).encode("utf-8"))
        time.sleep(0.06)

        #if bus reaches last coordinate, start from beginning
        if i == len(coordinates)-1:
            i = 0
        else:
            i += 1

generate_checkpoint(coordinates)