from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'

if __name__ == '__main__':
    connection = BlockingConnection(
        ConnectionParameters(
            host=RMQ_HOST,
            credentials=PlainCredentials(RMQ_USER, RMQ_PASS)
        )
    )
    try:
        while True:
            assert (query := input('Enter Query: ').strip()) in ['current', 'average']
            channel = connection.channel()

            channel.exchange_declare(
                exchange=EXCHANGE_NAME,
                exchange_type=ExchangeType.topic.name,
                durable=True
            )

            channel.basic_publish(
                exchange=EXCHANGE_NAME,
                routing_key=f'rep.{query}',
                body=query.encode()
            )
    except KeyboardInterrupt:
        print('Received Interrupt. Exiting...')
    except AssertionError:
        print('Invalid query')
    finally:
        connection.close()
