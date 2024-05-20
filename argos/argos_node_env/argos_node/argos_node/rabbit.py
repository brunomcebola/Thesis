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

    def generate_publisher(self, destination: str) -> Callable[[tuple], None]:
        """
        Generates a publisher function.

        Parameters
        - destination: The destination queue.

        Returns
        - A function that publishes messages to the destination queue.
        """

        channel = self._connection.channel()

        channel.queue_declare(queue=destination, durable=True)

        return lambda x: channel.basic_publish(
            exchange="",
            routing_key=destination,
            body=pickle.dumps(x),
            properties=pika.BasicProperties(delivery_mode=2),
        )
