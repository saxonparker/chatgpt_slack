"""ChatGPT conversations for slack. Designed to run as either a command-line
application or as an AWS Lambda pair."""

import base64
import json
import os
import traceback
import urllib.parse
import urllib.request

import boto3

def dispatch(event, _):
    """Entry point for the initial lambda. Just posts so an SNS topic to invoke
    the lambda that actually does the work. This is annoying, but the
    processing can take more than 3 seconds, which is the response time limit
    for slack."""

    def generate_response(message):
        """Generate a full HTTP JSON response."""
        return {
            'statusCode': str(200),
            'body': json.dumps({'text': message}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

    try:
        print(event)
        params = dict(urllib.parse.parse_qsl(base64.b64decode(str(event['body'])).decode('ascii')))
        print(params)
        if 'text' not in params or not params['text']:
            return generate_response('Usage:\n' +
                                     '/chatgpt prompt')
        prompt = params['text']
        user = params['user_name']
        print('DISPATCH COMMAND: ' + prompt + ' ' + user)

        # Publish an SNS notification to invoke the second-state lambda.
        message = {
            "response_url": params['response_url'],
            "prompt": prompt,
            "user": user
        }
        response = boto3.client('sns').publish(
            TopicArn=os.environ['CHATGPT_SNS_TOPIC'],
            Message=json.dumps({'default': json.dumps(message)}),
            MessageStructure='json'
        )
        print('SNS PUBLISH: ' + str(response))

        return generate_response(f'Processing prompt "{prompt}"...')
    # pylint: disable=broad-except
    except Exception as exc:
        print('DISPATCH ERROR: ' + str(exc))
        traceback.print_exc()
        return generate_response(str(exc))
    # pylint: enable=broad-except
