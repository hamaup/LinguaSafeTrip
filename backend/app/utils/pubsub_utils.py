import logging
import os
import json
from google.cloud import pubsub_v1
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

class PubSubPublisher:
    def __init__(self, project_id: Optional[str] = GCP_PROJECT_ID):
        if not project_id:
            logger.error("GCP_PROJECT_ID is not set. PubSubPublisher cannot be initialized.")
            raise ValueError("GCP_PROJECT_ID is required for PubSubPublisher.")
        self.project_id = project_id
        self.publisher_client = pubsub_v1.PublisherClient()
        logger.info(f"PubSubPublisher initialized for project: {self.project_id}")

    async def publish_message(self, topic_name: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Publishes a message to the specified Pub/Sub topic.

        Args:
            topic_name: The name of the Pub/Sub topic.
            data: The data to publish (will be JSON serialized).

        Returns:
            The message ID if successful, None otherwise.
        """
        if not self.project_id:
            logger.error("PubSubPublisher cannot publish message, project_id is not set.")
            return None

        topic_path = self.publisher_client.topic_path(self.project_id, topic_name)
        message_data_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")

        try:
            future = self.publisher_client.publish(topic_path, message_data_bytes)
            message_id = await future # Asynchronously wait for the publish result
            logger.info(f"Message published to {topic_path} with ID: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to publish message to {topic_path}: {e}", exc_info=True)
            return None

# Example usage (can be removed or kept for testing)
async def example_publish():
    if not GCP_PROJECT_ID:
        return

    publisher = PubSubPublisher()
    topic = "my-test-topic" # Replace with your topic name
    message_payload = {"key": "value", "timestamp": "2025-05-11T23:00:00Z"}

    # Ensure the topic exists or create it in GCP console / gcloud
    # For this example, we assume the topic exists.

    # Check if topic exists (optional, for robustness)
    # try:
    #     publisher.publisher_client.get_topic(request={"topic": publisher.publisher_client.topic_path(GCP_PROJECT_ID, topic)})
    # except Exception:
    #     logger.warning(f"Topic {topic} may not exist. Please create it.")
    #     # You might want to create the topic here if it doesn't exist,
    #     # but that requires more permissions and logic.
    #     # publisher.publisher_client.create_topic(request={"name": publisher.publisher_client.topic_path(GCP_PROJECT_ID, topic)})


    message_id = await publisher.publish_message(topic, message_payload)
    if message_id:
        pass
    else:
        pass
if __name__ == "__main__":
    import asyncio
    # This part is for direct execution testing, usually not run in a FastAPI app context
    # You would need to set GCP_PROJECT_ID environment variable to run this.
    # asyncio.run(example_publish())
    pass
