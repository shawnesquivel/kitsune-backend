import boto3


"""
PRE-REQUISITES:
1. Your AWS account is setup.
2. Installed to your Virtual Environment: `pip install boto3`
3. Permissions: DynamoDBFullAccess or a custom IAM policy that allows dynamodb:CreateTable actions.
4. Change the region_name to your region (us-east-1, us-west2, etc.)

"""

# Initialize a DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name="us-west-2")


# Create a DynamoDB table for storing chat messages
def create_chat_table(table_name):
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                "AttributeName": "ChatID",  # Partition key
                "KeyType": "HASH",  # Partition key is represented by 'HASH'
            },
            {
                "AttributeName": "timestamp",  # Sort key
                "KeyType": "RANGE",  # Sort key is represented by 'RANGE'
            },
        ],
        AttributeDefinitions=[
            {
                "AttributeName": "ChatID",
                "AttributeType": "S",  # 'S' represents string data type
            },
            {
                "AttributeName": "timestamp",
                "AttributeType": "N",  # 'N' represents number data type
            },
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,  # Provisioned read capacity
            "WriteCapacityUnits": 5,  # Provisioned write capacity
        },
    )

    # Wait until the table exists, this will take a moment
    table.meta.client.get_waiter("table_exists").wait(TableName=table_name)

    print(f"Table {table_name} created successfully.")
    return table


# Call the function to create the table
# Takes 15-30 seconds.
chat_table = create_chat_table("ChatMessages")
