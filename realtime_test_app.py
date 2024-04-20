# from flask import Flask, render_template, Response
#
# def get_kafka_client():
#     return KafkaClient(hosts='127.0.0.1:9092')
#
# app = Flask(__name__)
#
# @app.route('/')
# def index():
#     return(render_template('index.html'))
#
# #Consumer API
# @app.route('/topic/<topicname>')
# def get_messages(topicname):
#     client = get_kafka_client()
#     def events():
#         for i in client.topics[topicname].get_simple_consumer():
#             yield 'data:{0}\n\n'.format(i.value.decode())
#     return Response(events(), mimetype="text/event-stream")
#
# if __name__ == '__main__':
#     app.run(debug=True, port=5001)

from flask import Flask, render_template, Response
from kafka import KafkaConsumer

app = Flask(__name__)


bootstrap_servers = 'localhost:29092'
consumer = KafkaConsumer("topic_test", bootstrap_servers=bootstrap_servers)

@app.route("/")
def realtime_map():
    return(render_template('realtime_tracking.html'))

# Consumer API
@app.route('/topic/topic_test')
def get_messages():
    def events():
        for message in consumer:
            yield 'data:{0}\n\n'.format(message.value.decode())
    return Response(events(), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True, port=5001)
