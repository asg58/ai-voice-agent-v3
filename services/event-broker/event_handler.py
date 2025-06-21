import pika
import time
import logging
import os

# Configureer logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('event_broker')

class EventHandler:
    def __init__(self, broker_url):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(broker_url))
            self.channel = self.connection.channel()
            logger.info(f"Verbonden met message broker op {broker_url}")
        except Exception as e:
            logger.error(f"Kan geen verbinding maken met message broker: {str(e)}")
            # Niet direct falen, maar later opnieuw proberen
            self.connection = None
            self.channel = None

    def publish_event(self, event_name, payload):
        if not self.channel:
            logger.warning("Kan event niet publiceren: geen verbinding met broker")
            return False
        
        try:
            self.channel.basic_publish(exchange='', routing_key=event_name, body=payload)
            logger.info(f"Event gepubliceerd: {event_name}")
            return True
        except Exception as e:
            logger.error(f"Fout bij publiceren van event: {str(e)}")
            return False

    def consume_event(self, event_name, callback):
        if not self.channel:
            logger.warning("Kan niet luisteren naar events: geen verbinding met broker")
            return False
        
        try:
            self.channel.queue_declare(queue=event_name)
            self.channel.basic_consume(queue=event_name, on_message_callback=callback, auto_ack=True)
            logger.info(f"Luisteren naar events op queue: {event_name}")
            return True
        except Exception as e:
            logger.error(f"Fout bij opzetten van event consumer: {str(e)}")
            return False
    
    def start_consuming(self):
        if not self.channel:
            logger.warning("Kan niet starten met consumeren: geen verbinding met broker")
            return
        
        try:
            logger.info("Event broker is gestart en wacht op berichten...")
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Event broker wordt gestopt...")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"Fout tijdens consumeren van events: {str(e)}")

def callback(ch, method, properties, body):
    logger.info(f"Bericht ontvangen: {body}")
    # Hier kan de verwerking van het bericht plaatsvinden

def main():
    # Haal broker URL uit omgevingsvariabele of gebruik rabbitmq container naam
    broker_url = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
    
    # Maak een nieuwe EventHandler instantie
    handler = None
    
    # Wacht even zodat RabbitMQ tijd heeft om op te starten
    logger.info("Wachten op RabbitMQ server...")
    time.sleep(10)
    
    # Blijf proberen verbinding te maken
    while True:
        try:
            if not handler or not handler.connection or handler.connection.is_closed:
                logger.info(f"Proberen verbinding te maken met message broker op {broker_url}...")
                handler = EventHandler(broker_url)
                
                # Als we verbinding hebben, stel dan de queues in
                if handler.connection and not handler.connection.is_closed:
                    # Declareer de benodigde queues
                    handler.channel.queue_declare(queue='voice_events')
                    handler.channel.queue_declare(queue='user_events')
                    handler.channel.queue_declare(queue='system_events')
                    
                    # Publiceer een test bericht
                    handler.publish_event('system_events', '{"type": "startup", "message": "Event broker is gestart"}')
                    logger.info("Test bericht gepubliceerd op system_events queue")
                    
                    # Stel consumers in
                    handler.consume_event('voice_events', callback)
                    handler.consume_event('system_events', callback)
                    
                    # Start met luisteren naar events
                    logger.info("Event broker is succesvol verbonden en luistert naar events")
                    handler.start_consuming()
            
            # Als we hier komen, is er iets misgegaan met de verbinding
            logger.warning("Verbinding met message broker verloren, opnieuw proberen over 5 seconden...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("Event broker service wordt gestopt...")
            if handler and handler.connection and not handler.connection.is_closed:
                handler.connection.close()
            break
        except Exception as e:
            logger.error(f"Onverwachte fout: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    main()
