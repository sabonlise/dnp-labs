import json

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'co2.*'


def callback(ch, method, properties, body):
    data = json.loads(body.decode())
    with open('receiver.log', 'a') as f:
        f.write(json.dumps(data) + '\n')

    print(data['time'], end='')
    print(': WARNING' if data['value'] > 500 else ': OK')


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

    print('[*] Waiting for CO2 data. Press CTRL+C to exit')

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
