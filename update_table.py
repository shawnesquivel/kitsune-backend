from datetime import datetime
import time
import boto3
import logging
from decimal import Decimal

# Initialize a DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
table = dynamodb.Table("ChatMessages")


def current_epoch_time():
    """Return current time in epoch seconds."""
    return int(time.time())


def iso_to_epoch(timestamp):
    """Convert a timestamp to epoch time. Adjusted to handle integers."""
    # If the timestamp is already an integer, no conversion is needed
    if isinstance(timestamp, int):
        return timestamp
    # If the timestamp is a string, convert it as originally intended
    elif isinstance(timestamp, str):
        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        return int(dt.timestamp())


def store_message(
    chat_id, timestamp, message, message_type="user", audio_file_url=None
):
    epoch_time = iso_to_epoch(timestamp)

    item = {
        "ChatID": str(chat_id),
        "timestamp": epoch_time,
        "message": message,
        "type": message_type,
    }
    logging.info("========================")
    logging.info(f"Creating item: {item}")
    # Add audio_file_url to the item if it's provided
    if audio_file_url:
        item["AudioFileURL"] = audio_file_url

    response = table.put_item(Item=item)
    logging.info("========================")
    logging.info(f"Item stored: {response}")

    return response


def get_all_messages_for_chat(chat_id):
    """
    Retrieve chat messages from DynamoDB.
    """
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("ChatID").eq(chat_id)
    )
    return response["Items"]


# Insert a sample conversation
if __name__ == "__main__":
    # For testing
    store_message(
        "9000", "2024-03-18T12:00:00Z", "Hi, your name is Bobby. I'm Shawn.", "user"
    )
    store_message(
        "9000",
        "2024-03-18T12:00:02Z",
        "Hi Shawn, how are you doing?!",
        "ai",
        "https://google.ca",
    )
    store_message(
        "9000", "2024-03-18T12:00:04Z", "I'm doing well. What's your name?", "user"
    )
    store_message(
        "9000",
        "2024-03-18T12:00:10Z",
        "My name is Bobby, as you said.",
        "ai",
        "https://google.ca",
    )
