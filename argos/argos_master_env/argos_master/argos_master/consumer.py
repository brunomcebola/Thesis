""" Test module """

import pickle
import time

import pika
import pika.exceptions
import pika.adapters.blocking_connection


RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "dev"
RABBITMQ_PASSWORD = "dev"
QUEUE_NAMES = ["queue1", "queue2", "queue3"]


def create_connection():
    """Create connection to RabbitMQ server"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST, port=RABBITMQ_PORT, credentials=credentials
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        return connection, channel
    except pika.exceptions.AMQPError as e:
        print(f"Error establishing connection: {e}")
        return None, None


def consume_data():
    """Consume data"""
    connection, channel = create_connection()
    if connection and channel:
        try:

            def callback(ch, method, properties, body):
                i, message = pickle.loads(body)
                print(f"[{i}] Received {(len(message) / 1024)} KB @ {time.time()}")

            channel.basic_consume(queue="test", on_message_callback=callback, auto_ack=True)

            print(" [*] Waiting for messages. To exit press CTRL+C")
            channel.start_consuming()

        except pika.exceptions.AMQPError as e:
            print(f"Error consuming data: {e}")
        finally:
            connection.close()


if __name__ == "__main__":
    consume_data()
