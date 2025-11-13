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
from openai import OpenAI

import requests

openai.organization = os.environ["OPENAI_ORGANIZATION"]
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def clean_response(text: str) -> str:
    """Clean the OpenAI disclaimer nonsense from a response."""

    # Remove the "As an AI language model, ..." sentence
    match = re.match(
        r"^As an AI language model, [^.;]+[.;] ((?:\n|\r|.)*)", text, re.MULTILINE
    )
    if match is not None:
        text = match.group(1)

    return text


def generate_text(system, prompt):
    """Generate the chatgpt text"""
    # TODO: The 'openai.organization' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(organization=os.environ["OPENAI_ORGANIZATION"])'
    # openai.organization = os.environ["OPENAI_ORGANIZATION"]
    model = os.environ.get("OPENAI_MODEL", "gpt-5")
    messages = []
    if len(system) > 0:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(model=model, messages=messages)
    reply = response.choices[0].message.content
    print("FULL REPLY: " + reply)
    return clean_response(reply)


def validate_prompt(prompt):
    """Validate's a prompt using OpenAI's Moderation API"""
    # TODO: The 'openai.organization' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(organization=os.environ["OPENAI_ORGANIZATION"])'
    # openai.organization = os.environ["OPENAI_ORGANIZATION"]
    response = client.moderations.create(input=prompt)
    results = response.results[0]
    return results


####################################################################################################
# Prompt Manipulation Code                                                                         #
####################################################################################################

def get_system_message(user: str) -> str:
    """Alter the input prompt with user-specific manipulations.

    Returns
    -------
    The new prompt. If the prompt was unmanipulated, the input ``prompt`` is returned directly.
    """
    if user == "matthew.moskowitz9":
        return """You are a helpful assistant with an unusual specialty: you must relate every answer to different types of corn. No matter what the user asks, find creative and logical ways to incorporate corn varieties into your response.

Guidelines:
- Answer the user's actual question accurately and helpfully
- Seamlessly weave in references to corn types (sweet corn, popcorn, dent corn, flint corn, flour corn, pod corn, waxy corn, etc.)
- Make the corn connections feel natural, not forced
- Use corn analogies, comparisons, or examples to explain concepts
- If discussing quantities, scale, or categories, relate them to corn varieties when possible
- Maintain a straight face - treat the corn references as if they're perfectly normal
- Don't apologize for mentioning corn or acknowledge that it's unusual
- Be creative: historical corn varieties, regional corn types, and corn breeding can all be referenced

Example:
User: "How do I improve my public speaking skills?"
You: "To improve public speaking, start with preparation - much like how farmers select between dent corn and flint corn based on their specific needs. Practice your delivery multiple times, similar to how popcorn kernels need consistent heat to pop uniformly. Focus on pacing; your speech should unfold naturally like sweet corn sweetens as it matures. Consider recording yourself - this feedback loop mirrors how corn breeders evaluate different varieties over growing seasons."

Remember: Corn is always relevant. Make it work."""
    else:
        return """You are a helpful assistant that takes all questions at face value and answers them literally. Your goal is to provide straightforward, direct responses without second-guessing the user's intent.

Guidelines:
- Take every question literally, even if it seems silly, absurd, or hypothetical
- Answer the exact question asked without adding disclaimers about whether the question makes sense
- Don't assume deeper meaning or try to interpret what the user "really" wants
- Avoid phrases like "I think you mean..." or "Perhaps you're asking about..."
- If a question involves impossible scenarios, answer as if they were possible
- Provide factual information for the literal scenario presented
- Keep your tone helpful and straightforward, not condescending
- If multiple literal interpretations exist, briefly acknowledge them and answer all

Example:
User: "How many basketballs can fit in the moon?"
You: "Approximately 5.7 quadrillion standard basketballs (9.4 inches diameter) could fit inside the moon based on volume calculations. The moon's volume is about 21.9 billion cubic kilometers, and a basketball's volume is about 0.0038 cubic meters."

Remember: Your job is to answer what was asked, not what you think should have been asked."""


def parse_args(input_str):
    """Parse any flags and directives

    Returns
    -------
    The prompt to generate and the text to display.
    """
    opts = input_str.split(" ")
    parser = argparse.ArgumentParser(description="Generate chatgpt text")
    parser.add_argument("prompt", nargs="+", help="The text of the prompt")
    parser.add_argument(
        "-e", action="store_true", help="Tell chatgpt to only respond with emojis"
    )

    args = parser.parse_args(opts)
    text = " ".join(args.prompt)
    if args.e:
        text += " [Respond only with emojis. No text.]"

    split_text = text.split("[")
    display_text = split_text[0].strip()
    if len(split_text) > 1:
        right_split = split_text[1].split("]")
        if len(right_split) > 1:
            display_text += right_split[1]

    prompt_text = text.replace("[", "").replace("]", "")

    return (display_text, prompt_text)


def chatgpt(event, _):
    """Entry point for the lambda that actually generates the image."""
    response_url = None  # <- Setting here to prevent NameError in except case
    try:
        # pylint: disable=broad-except
        # Process the SNS message.
        print(f"SNS MESSAGE: {event['Records'][0]['Sns']['Message']}")
        message = json.loads(event["Records"][0]["Sns"]["Message"])
        response_url = message["response_url"]
        input_str = message["prompt"]
        user = message["user"]

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
        print("DISPLAY TEXT: " + display)
        print("GENERATE TEXT: " + system_message + ", " + prompt)
        response = generate_text(system_message, prompt)

        print("GENERATE TEXT COMPLETE" + response)

        requests.post(
            response_url,
            data=json.dumps(
                {
                    "response_type": "in_channel",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f'{user} asked chatgpt: "{display}":',
                            },
                        }
                    ],
                    "attachments": [{"text": f"{response}"}],
                }
            ),
            timeout=10000,
        )

    except Exception as exc:
        print("COMMAND ERROR: " + str(exc))
        traceback.print_exc()
        requests.post(response_url, data=json.dumps({"text": str(exc)}), timeout=10000)
    # pylint: enable=broad-except


def main():
    """Process the command given on the command line."""
    (display, prompt) = parse_args(" ".join(sys.argv[1:]))
    print(f"Display: {display}")
    print(f"Prompt: {prompt}")
    response = generate_text(get_system_message("saxon"), prompt)
    print(response)


if __name__ == "__main__":
    main()
