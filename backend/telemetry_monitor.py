import json
import time
from google.cloud import pubsub_v1
from google.api_core import exceptions

PROJECT_ID = "track3codelabs"
TOPIC_ID = "taskninja-events"
SUBSCRIPTION_ID = "taskninja-events-sub"

def callback(message):
    try:
        data = json.loads(message.data.decode("utf-8"))
        decision_id = data.get("decision_id", "???")
        agents = data.get("invoked_agents", [])
        timestamp = data.get("timestamp", "???")
        
        # Format the swarm trace logically
        trace = " -> ".join([f"\033[94m{a}\033[0m" for a in agents])
        
        print("\n" + "="*60)
        print(f"🛰️  [SWARM TRACE RECEIVED] | {timestamp}")
        print(f"🆔 Decision ID: {decision_id}")
        print(f"🧩 Invocation Path: {trace}")
        print("="*60)
        
        message.ack()
    except Exception as e:
        print(f"Error processing message: {e}")
        message.nack()

def start_monitor():
    subscriber = pubsub_v1.SubscriberClient()
    topic_path = f"projects/{PROJECT_ID}/topics/{TOPIC_ID}"
    subscription_path = f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_ID}"

    print(f"--- TaskNinja Telemetry Observer ---")
    print(f"Monitoring topic: {TOPIC_ID}")
    
    # 1. Ensure Subscription exists
    try:
        subscriber.create_subscription(name=subscription_path, topic=topic_path)
        print(f"Created new subscription: {SUBSCRIPTION_ID}")
    except exceptions.AlreadyExists:
        print(f"Using existing subscription: {SUBSCRIPTION_ID}")
    except Exception as e:
        print(f"Failed to setup subscription: {e}")
        return

    print(f"Waiting for traces... (Press CTRL+C to stop)")
    
    # 2. Subscribe
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    
    with subscriber:
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            print("\nObserver stopped.")

if __name__ == "__main__":
    start_monitor()
