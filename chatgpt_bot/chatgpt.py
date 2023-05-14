"""Generate chatgpt text for slack. Designed to run as either a command-line
application or as an AWS Lambda pair."""

import argparse
import json
import os
import random
import re
import sys
import traceback
import typing

import openai
import requests


def clean_response(text: str) -> str:
    """Clean the OpenAI disclaimer nonsense from a response."""

    # Remove the "As an AI language model, ..." sentence
    m = re.match(r"^As an AI language model, [^.;]+[.;] (.*)", text)
    if m is not None:
        text = m.group(1)

    return text

def generate_text(system, prompt):
    """Generate the chatgpt text"""
    openai.organization = os.environ['OPENAI_ORGANIZATION']
    openai.api_key = os.environ['OPENAI_API_KEY']
    messages = []
    if len(system) > 0:
        messages.append({"role": "system", "content": system})
    messages.append({"role":"user", "content": prompt})
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    reply = response['choices'][0]['message']['content']
    return clean_response(reply)


def validate_prompt(prompt):
    """Validate's a prompt using OpenAI's Moderation API"""
    openai.organization = os.environ['OPENAI_ORGANIZATION']
    openai.api_key = os.environ['OPENAI_API_KEY']
    response = openai.Moderation.create(input=prompt)
    results = response['results'][0]
    return results


####################################################################################################
# Prompt Manipulation Code                                                                         #
####################################################################################################

class Manipulation(typing.NamedTuple):
    """
    Manipulates source prompts to be something a little more fun. This system is meant as a prank to
    make a friend wonder why so many of his prompts come out with corn-themed results.
    """

    source: str
    """
    The source format string for the manipulation. It must contain a ``{prompt}`` and ``{choice}``
    text, which are the original source prompt and a random choice from the ``potentials``. For
    example, source ``"{choice} of {prompt}"`` and potentials ``["oil painting", "watercolor"]``
    would lead to results like ``"watercolor of Darth Vader trying to drink a milkshake"``.
    """

    potentials: typing.Sequence[str]

    def generate(self) -> str:
        """Alter the ``prompt`` and return the result."""
        return str.format(self.source, choice=random.choice(self.potentials))


def get_user_specific_manipulations(user: str) -> typing.Sequence[Manipulation]:
    """
    Get a list of manipulations for the given ``user``. If the user has no manipulations, this
    returns an empty tuple.
    """
    if user == 'matthew.moskowitz9':
        basic_corn = ("corn",
                      "corn cob",
                      "corn kernel",
                      "corn dog",
                      "creamed corn",
                      "corn puffs",
                      "popcorn",
                      )
        return (Manipulation("Make all responses in this conversation '{choice}' themed.", basic_corn),
                Manipulation("Make all responses in this conversation 'on a {choice}' themed.", basic_corn),
                Manipulation("Make all responses in this conversation 'in a {choice}' themed.", ("corn field", "bowl of creamed corn")),
                Manipulation("Make all responses in this conversation 'holding {choice}' themed.", basic_corn),
                Manipulation("Make all responses in this conversation a '{choice} thinking about {prompt}' themed.", ("corn cob man", "corn dog",)),
                Manipulation("Make all responses in this conversation 'a corn-based {choice}' themed.", ("NFT", "cryptocurrency")),
                )

    return tuple()


def get_system_message(user: str) -> str:
    """Alter the input prompt with user-specific manipulations.

    Returns
    -------
    The new prompt. If the prompt was unmanipulated, the input ``prompt`` is returned directly.
    """
    manips = get_user_specific_manipulations(user)
    if len(manips) == 0:
        return ""
    return random.choice(manips).generate()

def parse_args(input_str):
    """Parse any flags and directives

    Returns
    -------
    The prompt to generate and the text to display.
    """
    opts = input_str.split(' ')
    parser = argparse.ArgumentParser(
        description='Generate chatgpt text')
    parser.add_argument('prompt', nargs='+', help='The text of the prompt')
    parser.add_argument('-e', action='store_true',
                        help='Tell chatgpt to only respond with emojis')

    args = parser.parse_args(opts)
    text = ' '.join(args.prompt)
    if args.e:
        text += ' [Respond only with emojis. No text.]'

    display_text = text.split('[', maxsplit=1)[0].strip()
    prompt_text = text.replace('[', '').replace(']', '')

    return (display_text, prompt_text)

def chatgpt(event, _):
    """Entry point for the lambda that actually generates the image."""
    response_url = None # <- Setting here to prevent NameError in except case
    try:
    # pylint: disable=broad-except
        # Process the SNS message.
        print(f"SNS MESSAGE: {event['Records'][0]['Sns']['Message']}")
        message = json.loads(event['Records'][0]['Sns']['Message'])
        response_url = message['response_url']
        input_str = message['prompt']
        user = message['user']

        (display, prompt) = parse_args(input_str)

        # Don't actually validate the prompt because it gives different results than when chatgpt
        # actually flags.
        # Leave the code in for now in case this changes in the future.
        #
        # print('VALIDATE PROMPT: ' + prompt)
        # validation = validate_prompt(prompt)
        # if validation['flagged']:
        #     requests.post(response_url, data=json.dumps({'text': validation}), timeout=10000)
        #     print('VALIDATION FAILED')
        #     return

        # Process the command.
        system_message = get_system_message(user)
        print('DISPLAY TEXT: ' + display)
        print('GENERATE TEXT: ' + system_message + ", "+ prompt)
        response = generate_text(system_message, prompt)

        print('GENERATE TEXT COMPLETE' + response)

        requests.post(response_url,
                      data=json.dumps({"response_type": "in_channel", "blocks": [
		        {
		        	"type": "section",
		        	"text": {
		        		"type": "mrkdwn",
		        		"text": f'{user} asked chatgpt: "{display}":'
		        	}
		        }],
                "attachments": [
		        {
                    "text": f"{response}"
		        }
            ]}), timeout=10000)

    except Exception as exc:
        print('COMMAND ERROR: ' + str(exc))
        traceback.print_exc()
        requests.post(response_url, data=json.dumps({'text': str(exc)}), timeout=10000)
    # pylint: enable=broad-except

def main():
    """Process the command given on the command line."""
    (display, prompt) = parse_args(' '.join(sys.argv[1:]))
    print(f'Display: {display}')
    print(f'Prompt: {prompt}')
    response = generate_text("Make all responses saxon themed", prompt)
    print(response)

if __name__ == '__main__':
    main()
