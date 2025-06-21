import json

def lambda_handler(event, context):
    """
    Serverless functie voor real-time verwerking.
    """
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
