""" Test module """

import pickle
import numpy as np
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


def produce_data():
    """Produce data"""
    connection, channel = create_connection()
    if connection and channel:
        times = []

        try:
            i = 0
            while True:
                # generate a random bytes array
                message = np.random.bytes(1024 * np.random.randint(900, 901))

                # print how many mega bytes the message is
                print(f"[{i}] Sent {(len(message) / 1024)} KB @ {time.time()}")

                s = time.time()

                channel.basic_publish(
                    exchange="",
                    routing_key="test",
                    body=pickle.dumps((i, message)),
                    properties=pika.BasicProperties(delivery_mode=2),
                )

                f = time.time()

                times.append(f - s)

                i = i + 1

                time.sleep(0.033)

        except pika.exceptions.AMQPError as e:
            print(f"Error producing data: {e}")
        except KeyboardInterrupt:
            print(f"Average time to send message: {np.mean(times)}")
        finally:
            connection.close()


if __name__ == "__main__":
    produce_data()
