"""
ActiveMQ Consumer for PythonConsumerTopic - STOMP 1.0

This module provides a consumer that listens to ActiveMQ topic:
    com.zoomsystems.common.PythonConsumerTopic

Protocol: STOMP 1.0 (uses Connection10 for ActiveMQ Classic compatibility)
Connection: tcp://localhost:61613 (STOMP port)

Features:
- Durable subscription: Messages are stored when consumer is offline
- Messages are delivered when consumer reconnects
- No message loss during maintenance/shutdown
"""
import time
import logging
import threading
from typing import Callable, Optional
import stomp
from config import ACTIVEMQ_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logging.getLogger('stomp.py').setLevel(logging.WARNING)


class ActiveMQConsumerListener(stomp.ConnectionListener):
    """Listener class for ActiveMQ message handling using STOMP 1.0"""
    
    def __init__(self, message_handler: Optional[Callable] = None):
        """
        Initialize the listener with an optional message handler.
        
        Args:
            message_handler: Callable that processes messages.
                           Should accept (headers, body) as parameters.
        """
        self.message_handler = message_handler
        self.connection = None
        
    def on_connected(self, frame):
        """Called when connection is established"""
        logger.info("Connected to ActiveMQ broker (STOMP 1.0)")
        
    def on_disconnected(self):
        """Called when connection is lost"""
        logger.warning("Disconnected from ActiveMQ broker")
        
    def on_message(self, frame):
        """
        Called when a message is received.
        
        Args:
            frame: STOMP frame containing headers and body
        """
        headers = frame.headers
        body = frame.body
        
        logger.info(f"Received message on topic: {headers.get('destination', 'unknown')}")
        logger.debug(f"Message headers: {headers}")
        logger.debug(f"Message body: {body[:200]}...")  # Log first 200 chars
        
        # Process message with custom handler if provided
        if self.message_handler:
            try:
                self.message_handler(headers, body)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
        else:
            # Default handler - just log the message
            logger.info(f"Message received (no handler defined): {body}")
            
    def on_error(self, frame):
        """Called when an error occurs"""
        logger.error(f"ActiveMQ error: {frame.body}")
        
    def on_heartbeat_timeout(self):
        """Called when heartbeat timeout occurs"""
        logger.warning("Heartbeat timeout - connection may be stale")
        
    def on_receipt(self, frame):
        """Called when a receipt is received"""
        logger.debug(f"Receipt received: {frame.headers.get('receipt-id', 'unknown')}")
        
    def on_receiver_loop_completed(self, *args):
        """Called when receiver loop completes"""
        logger.debug("Receiver loop completed")


class ActiveMQConsumer:
    """ActiveMQ Consumer using STOMP 1.0 protocol"""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        topic: str = None,
        client_id: str = None,
        subscription_name: str = None,
        message_handler: Optional[Callable] = None
    ):
        """
        Initialize the ActiveMQ consumer with STOMP 1.0.
        
        Args:
            host: ActiveMQ broker host (defaults to config)
            port: ActiveMQ broker port (defaults to config)
            username: ActiveMQ username (defaults to config)
            password: ActiveMQ password (defaults to config)
            topic: Topic name to subscribe to (defaults to config)
            client_id: Client ID for durable subscription (defaults to config)
            subscription_name: Durable subscription name (defaults to config)
            message_handler: Optional callback function to handle messages
        """
        self.host = host or ACTIVEMQ_CONFIG["host"]
        self.port = port or ACTIVEMQ_CONFIG["stomp_port"]
        self.username = username or ACTIVEMQ_CONFIG["username"]
        self.password = password or ACTIVEMQ_CONFIG["password"]
        self.topic = topic or ACTIVEMQ_CONFIG["topic"]
        self.client_id = client_id or ACTIVEMQ_CONFIG["client_id"]
        self.subscription_name = subscription_name or ACTIVEMQ_CONFIG["subscription_name"]
        
        self.conn = stomp.Connection10(
            host_and_ports=[(self.host, self.port)]
        )
        
        # Set up listener
        self.listener = ActiveMQConsumerListener(message_handler)
        self.conn.set_listener('', self.listener)
        
        self.connected = False
        self.subscribed = False
        self.running = False
        
    def connect(self):
        """Connect to ActiveMQ broker using STOMP 1.0 with durable subscription support"""
        try:
            # Connect with client-id for durable subscriptions
            # Client ID is required for durable subscriptions to work
            connect_headers = {'client-id': self.client_id}
            
            if self.username and self.password:
                self.conn.connect(
                    username=self.username,
                    passcode=self.password,
                    wait=True,
                    headers=connect_headers
                )
            else:
                self.conn.connect(
                    wait=True,
                    headers=connect_headers
                )
            
            if not self.conn.is_connected():
                logger.error(f"Connection failed. Check if STOMP is enabled on port {self.port}")
                self.connected = False
                return False
                
            self.connected = True
            logger.info(f"Connected to ActiveMQ at {self.host}:{self.port} (STOMP 1.0, Client ID: {self.client_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ActiveMQ: {e}")
            self.connected = False
            return False
            
    def subscribe(self):
        """Subscribe to the configured topic using STOMP 1.0 with durable subscription"""
        if not self.connected:
            logger.error("Cannot subscribe - not connected to broker")
            return False
            
        try:
            topic_path = f"/topic/{self.topic}" if not self.topic.startswith("/") else self.topic
            
            # Durable subscription headers - messages stored when consumer is offline
            subscribe_headers = {
                'activemq.subscriptionName': self.subscription_name,
                'activemq.durableSubscriptionName': self.subscription_name
            }
            
            self.conn.subscribe(
                destination=topic_path,
                id=1,
                ack='auto',
                headers=subscribe_headers
            )
            self.subscribed = True
            logger.info(f"Subscribed to topic: {topic_path} (Durable: {self.subscription_name})")
            logger.info("Messages will be stored when consumer is offline and delivered on reconnect")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to topic: {e}", exc_info=True)
            self.subscribed = False
            return False
            
    def unsubscribe(self):
        """Unsubscribe from the topic using STOMP 1.0"""
        if not self.subscribed:
            return
            
        try:
            self.conn.unsubscribe(id=1)
            self.subscribed = False
            logger.info(f"Unsubscribed from topic: {self.topic}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}", exc_info=True)
            
    def disconnect(self, keep_durable_subscription: bool = True):
        """
        Disconnect from ActiveMQ broker using STOMP 1.0
        
        Args:
            keep_durable_subscription: If True, keeps durable subscription active
                                      so messages are stored while offline
        """
        # For durable subscriptions, don't unsubscribe when disconnecting
        # This allows messages to be stored while consumer is offline
        if self.subscribed and not keep_durable_subscription:
            self.unsubscribe()
            
        if self.connected:
            try:
                self.conn.disconnect()
                self.connected = False
                if keep_durable_subscription:
                    logger.info(f"Disconnected from ActiveMQ broker (durable subscription '{self.subscription_name}' remains active)")
                    logger.info("Messages sent while offline will be stored and delivered on reconnect")
                else:
                    logger.info("Disconnected from ActiveMQ broker")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}", exc_info=True)
                
    def start(self, blocking: bool = True):
        """
        Start the consumer and begin listening for messages.
        
        Args:
            blocking: If True, blocks the current thread. If False, runs in background.
        """
        if not self.connect():
            logger.error("Failed to connect - cannot start consumer")
            return False
            
        if not self.subscribe():
            logger.error("Failed to subscribe - cannot start consumer")
            self.disconnect()
            return False
            
        self.running = True
        logger.info("Consumer started and listening for messages...")
        
        if blocking:
            try:
                # Keep the connection alive
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                self.stop()
        else:
            # Run in background thread
            def run_loop():
                try:
                    while self.running:
                        time.sleep(1)
                except Exception as e:
                    logger.error(f"Error in consumer loop: {e}", exc_info=True)
                    self.running = False
                    
            thread = threading.Thread(target=run_loop, daemon=True)
            thread.start()
            
        return True
        
    def stop(self, keep_durable_subscription: bool = True):
        """
        Stop the consumer
        
        Args:
            keep_durable_subscription: If True, keeps durable subscription active
                                      so messages are stored while offline (default: True)
        """
        logger.info("Stopping consumer...")
        self.running = False
        self.disconnect(keep_durable_subscription=keep_durable_subscription)


def default_message_handler(headers: dict, body: str):
    """
    Default message handler - processes received messages.
    Override this or pass a custom handler to customize behavior.
    
    Args:
        headers: Message headers
        body: Message body
    """
    logger.info(f"Processing message from {headers.get('destination', 'unknown')}")
    logger.info(f"Message content: {body}")
    # Add your custom processing logic here


def main():
    """Main function to run the consumer"""
    logger.info("Starting ActiveMQ Consumer...")
    logger.info(f"Configuration: {ACTIVEMQ_CONFIG}")
    
    # Create consumer with custom message handler
    consumer = ActiveMQConsumer(message_handler=default_message_handler)
    
    try:
        # Start consumer (blocks until interrupted)
        consumer.start(blocking=True)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        consumer.stop()
        logger.info("Consumer stopped")


if __name__ == "__main__":
    main()
