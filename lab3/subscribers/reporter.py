import json
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'rep.*'


def callback(ch, method, properties, body):
    msg = body.decode()
    with open('receiver.log', 'r') as f:
        reports = list(map(lambda r: json.loads(r.strip()), f.readlines()))

    if msg == 'current':
        print(f"{reports[-1]['time']}: Latest CO2 level is {reports[-1]['value']}")
    else:
        print(f"{datetime.now().__str__()}: "
              f"Average CO2 level is {sum(map(lambda r: r['value'], reports)) / len(reports)}")


if __name__ == '__main__':
    connection = BlockingConnection(
        ConnectionParameters(
            host=RMQ_HOST,
            credentials=PlainCredentials(RMQ_USER, RMQ_PASS)
        )
    )
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type=ExchangeType.topic.name,
        durable=True
    )

    queue_name = channel.queue_declare(queue='', exclusive=True).method.queue
    channel.queue_bind(
        exchange=EXCHANGE_NAME,
        queue=queue_name,
        routing_key=ROUTING_KEY
    )

    print('[*] Waiting for queries from the control tower. Press CTRL+C to exit')

    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=True
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print('Received Interrupt. Exiting...')
        exit()
    finally:
        connection.close()
