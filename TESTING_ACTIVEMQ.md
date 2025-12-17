# Testing the ActiveMQ Consumer

This guide explains how to test the ActiveMQ consumer that listens to the `com.zoomsystems.common.PythonConsumerTopic` topic.

## Prerequisites

1. **ActiveMQ Broker Running**: Ensure ActiveMQ is running with STOMP connector enabled
   - Default STOMP port: `61613` (or configure via environment variables)
   - Transport connector: `stomp://0.0.0.0:61613`

2. **Dependencies Installed**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**: The consumer uses configuration from `config.py` which can be overridden with environment variables:
   - `ACTIVEMQ_HOST` (default: `localhost`)
   - `ACTIVEMQ_PORT` (default: `61613` - STOMP port)
   - `ACTIVEMQ_USERNAME` (optional)
   - `ACTIVEMQ_PASSWORD` (optional)
   - `ACTIVEMQ_TOPIC` (default: `com.zoomsystems.common.PythonConsumerTopic`)

## Quick Start Testing

**You don't need a test class to test the consumer!** Here are several simple ways:

### Option 1: Use ActiveMQ Web Console (Easiest - No Code Needed!)

1. Start your consumer:
   ```bash
   python activemq_consumer.py
   ```

2. Open ActiveMQ Web Console (usually at `http://localhost:8161/admin/`)
3. Go to "Topics" → Find `com.zoomsystems.common.PythonConsumerTopic`
4. Click "Send To" button
5. Enter a test message and click "Send"

### Option 2: Simple Test Script (No Classes)

Use the minimal test script:

**Terminal 1 - Start the Consumer:**
```bash
python activemq_consumer.py
```

**Terminal 2 - Send a Test Message:**
```bash
python activemq_simple_test.py
```

This sends a simple message without any class structure.

### Option 3: Send Messages Programmatically

You can send messages directly in Python without any test classes:

```python
import stomp
from config import ACTIVEMQ_CONFIG

conn = stomp.Connection10(
    host_and_ports=[(ACTIVEMQ_CONFIG["host"], ACTIVEMQ_CONFIG["stomp_port"])]
)
conn.connect(wait=True)
conn.send(body="Your message here", destination=f"/topic/{ACTIVEMQ_CONFIG['topic']}")
conn.disconnect()
```

## Why Don't I Need a Test Class?

**Short answer: You don't!** You can test your consumer using:

1. ✅ **ActiveMQ Web Console** (easiest - no code at all)
2. ✅ **Simple Python script** (see `activemq_simple_test.py`)
3. ✅ **Direct STOMP connection** (a few lines of code)
4. ✅ **Any external tool** that can send STOMP messages

For basic testing, the Web Console or simple script is sufficient!

## Manual Testing Steps

### Step 1: Verify ActiveMQ Broker is Running

Check if ActiveMQ is accessible:

```bash
# Test connection (requires telnet or nc)
telnet localhost 61616
# or
nc -zv localhost 61616
```

Or use the ActiveMQ Web Console (usually at `http://localhost:8161/admin/`)

### Step 2: Start the Consumer

```bash
python activemq_consumer.py
```

You should see output like:
```
2024-01-XX XX:XX:XX - __main__ - INFO - Starting ActiveMQ Consumer...
2024-01-XX XX:XX:XX - __main__ - INFO - Configuration: {'host': '0.0.0.0', 'port': 61616, ...}
2024-01-XX XX:XX:XX - __main__ - INFO - Connected to ActiveMQ broker
2024-01-XX XX:XX:XX - __main__ - INFO - Connected to ActiveMQ at 0.0.0.0:61616
2024-01-XX XX:XX:XX - __main__ - INFO - Subscribed to topic: com.zoomsystems.common.PythonConsumerTopic
2024-01-XX XX:XX:XX - __main__ - INFO - Consumer started and listening for messages...
```

### Step 3: Send Test Messages

You can send test messages using any of the methods above:
- Use the simple test script: `python activemq_simple_test.py`
- Use ActiveMQ Web Console
- Send messages programmatically (see Option 3)

### Step 4: Verify Messages Received

You should see messages appearing in the consumer terminal:
```
2024-01-XX XX:XX:XX - __main__ - INFO - Received message on topic: /topic/com.zoomsystems.common.PythonConsumerTopic
2024-01-XX XX:XX:XX - __main__ - INFO - Processing message from /topic/com.zoomsystems.common.PythonConsumerTopic
2024-01-XX XX:XX:XX - __main__ - INFO - Message content: Hello, ActiveMQ! This is a test message.
```

## Testing with Custom Message Handler

To test with your own message processing logic:

1. Create a test script (e.g., `test_consumer_custom.py`):

```python
from activemq_consumer import ActiveMQConsumer
import logging

logging.basicConfig(level=logging.INFO)

def my_message_handler(headers, body):
    print(f"Custom handler received: {body}")
    # Add your processing logic here

consumer = ActiveMQConsumer(message_handler=my_message_handler)
consumer.start(blocking=True)
```

2. Run your test script:
```bash
python test_consumer_custom.py
```

3. Send messages using any method (simple test script, Web Console, or programmatically).

## Testing with Different Configurations

### Using Environment Variables

```bash
# Set environment variables
export ACTIVEMQ_HOST=localhost
export ACTIVEMQ_PORT=61616
export ACTIVEMQ_TOPIC=com.zoomsystems.common.PythonConsumerTopic

# Run consumer
python activemq_consumer.py
```

### Using Different Host/Port

```python
from activemq_consumer import ActiveMQConsumer

consumer = ActiveMQConsumer(
    host="localhost",
    port=61616,
    topic="com.zoomsystems.common.PythonConsumerTopic"
)
consumer.start(blocking=True)
```

## Troubleshooting

### Issue: Connection Refused

**Error**: `Failed to connect to ActiveMQ`

**Solutions**:
- Verify ActiveMQ broker is running
- Check the host and port are correct
- If broker is on a remote server, ensure firewall allows port 61616
- Try using `localhost` instead of `0.0.0.0` for client connections

### Issue: No Messages Received

**Possible causes**:
1. Topic name mismatch - verify the topic name in consumer and producer match
2. Messages sent before consumer subscribed - send messages after consumer is running
3. Wrong topic type - ensure both are using a topic (not a queue)

**Debug steps**:
- Check ActiveMQ web console to see if messages are being sent
- Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
- Verify subscription in ActiveMQ console

### Issue: Authentication Failed

**Error**: Authentication-related errors

**Solutions**:
- Set `ACTIVEMQ_USERNAME` and `ACTIVEMQ_PASSWORD` environment variables
- Or pass credentials when creating consumer:
  ```python
  consumer = ActiveMQConsumer(
      username="admin",
      password="admin"
  )
  ```

### Issue: Topic Path Issues

ActiveMQ STOMP uses `/topic/` prefix. The consumer automatically adds this prefix if not present.

If you have issues:
- Topic name: `com.zoomsystems.common.PythonConsumerTopic`
- Actual path used: `/topic/com.zoomsystems.common.PythonConsumerTopic`

## Using ActiveMQ Web Console

The ActiveMQ Web Console (usually at `http://localhost:8161/admin/`) can help with testing:

1. **View Topics**: Go to "Topics" menu to see active topics
2. **Send Messages**: Use "Send To" feature to manually send messages
3. **Monitor**: View message counts, subscribers, etc.

## Expected Behavior

### Successful Test Flow

1. Consumer starts and connects ✓
2. Consumer subscribes to topic ✓
3. Producer sends messages ✓
4. Consumer receives and logs messages ✓
5. Consumer processes messages (via handler) ✓

### Example Output

**Consumer Terminal:**
```
INFO - Connected to ActiveMQ broker
INFO - Connected to ActiveMQ at 0.0.0.0:61616
INFO - Subscribed to topic: com.zoomsystems.common.PythonConsumerTopic
INFO - Consumer started and listening for messages...
INFO - Received message on topic: /topic/com.zoomsystems.common.PythonConsumerTopic
INFO - Processing message from /topic/com.zoomsystems.common.PythonConsumerTopic
INFO - Message content: Hello, ActiveMQ! This is a test message.
```

**Producer Terminal:**
```
INFO - Connected to ActiveMQ at 0.0.0.0:61616
INFO - Message sent to topic: com.zoomsystems.common.PythonConsumerTopic
INFO - Message sent successfully
```

## Next Steps

Once basic testing is successful:

1. **Integrate with your application**: Modify the message handler to process messages for your use case
2. **Add error handling**: Implement retry logic, dead-letter queues, etc.
3. **Add monitoring**: Set up logging, metrics, alerts
4. **Production deployment**: Configure for production ActiveMQ cluster

## Additional Resources

- [STOMP Protocol Specification](https://stomp.github.io/)
- [ActiveMQ Documentation](https://activemq.apache.org/)
- [stomp.py Documentation](https://github.com/jasonrbriggs/stomp.py)

