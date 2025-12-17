"""
Simple ActiveMQ Test Script

Send test messages to the ActiveMQ topic.
Run this while the consumer is running.
"""
import stomp
from config import ACTIVEMQ_CONFIG


def send_test_message(message):
    """Send a test message to the topic"""
    host = ACTIVEMQ_CONFIG["host"]
    stomp_port = ACTIVEMQ_CONFIG["stomp_port"]
    username = ACTIVEMQ_CONFIG["username"] or ""
    password = ACTIVEMQ_CONFIG["password"] or ""
    topic = ACTIVEMQ_CONFIG["topic"]
    
    conn = stomp.Connection10(
        host_and_ports=[(host, stomp_port)]
    )
    
    try:
        if username and password:
            conn.connect(username=username, passcode=password, wait=True)
        else:
            conn.connect(wait=True)
        
        topic_path = f"/topic/{topic}" if not topic.startswith("/") else topic
        conn.send(body=message, destination=topic_path)
        
        print(f"✓ Message sent: {message[:50]}...")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        raise
    finally:
        conn.disconnect()


if __name__ == "__main__":
    send_test_message("Hello from test script!")
