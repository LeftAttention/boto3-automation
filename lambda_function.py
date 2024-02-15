import json

def lambda_handler(event, context):
    print("Hello, Lambda was triggered by CloudWatch Events")
    return {
        'statusCode': 200,
        'body': json.dumps('Success!')
    }
