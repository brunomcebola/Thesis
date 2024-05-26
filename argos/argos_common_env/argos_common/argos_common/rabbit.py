""" Test module """

import pickle
from typing import Callable
import pika
import pika.exceptions
import pika.adapters.blocking_connection


class RabbitMQ:
    """
    A class to abstract the interaction with RabbitMQ.
    """

    _connection: pika.adapters.blocking_connection.BlockingConnection

    def __init__(self, server: str, user: str, pwd: str) -> None:
        """
        Initializes the RabbitMQ connection.

        Parameters
        - server: The RabbitMQ server.
        - user: The RabbitMQ user.
        - pwd: The RabbitMQ password.

        Raises
        - RuntimeError: If the connection with RabbitMQ fails.
        """

        try:
            credentials = pika.PlainCredentials(user, pwd)

            parameters = pika.ConnectionParameters(
                host=server.split(":")[0], port=server.split(":")[1], credentials=credentials
            )

            self._connection = pika.BlockingConnection(parameters)

        except pika.exceptions.AMQPError as e:
            raise RuntimeError("Unable to establish connection with RabbitMQ!") from e

    def generate_publisher(self, queue: str) -> Callable[[tuple], None]:
        """
        Generates a publisher function.

        Parameters
        - destination: The destination queue.

        Returns
        - A function that publishes messages to the destination queue.
        """

        channel = self._connection.channel()

        channel.queue_declare(queue=queue, durable=True)

        return lambda x: channel.basic_publish(
            exchange="",
            routing_key=queue,
            body=pickle.dumps(x),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def register_consumer(self, queue: str, callback: Callable[[tuple], None]) -> None:
        """
        Generates a consumer function.

        Parameters
        - source: The source queue.
        - callback: The callback function that processes the messages.
        """

        channel = self._connection.channel()

        channel.queue_declare(queue=queue, durable=True)

        channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)

        channel.start_consuming()
