import sys

sys.path.append(".")

import chatgpt


def test_parse_args():
    no_directive = "a basic prompt"

    (display, prompt) = chatgpt.parse_args(no_directive)

    assert display == no_directive
    assert prompt == no_directive

    directive = "a basic prompt [with a directive]"

    (display, prompt) = chatgpt.parse_args(directive)

    assert display == "a basic prompt"
    assert prompt == "a basic prompt with a directive"

    post_directive = "a basic prompt [with a directive] and text after"

    (display, prompt) = chatgpt.parse_args(post_directive)

    assert display == "a basic prompt and text after"
    assert prompt == "a basic prompt with a directive and text after"

    no_closing = "a basic prompt [with a directive and text after"

    (display, prompt) = chatgpt.parse_args(no_closing)

    assert display == "a basic prompt"
    assert prompt == "a basic prompt with a directive and text after"

    right_only = "a basic prompt with a directive] and text after"

    (display, prompt) = chatgpt.parse_args(right_only)

    assert display == "a basic prompt with a directive] and text after"
    assert prompt == "a basic prompt with a directive and text after"

    emoji = "-e a basic prompt"

    (display, prompt) = chatgpt.parse_args(emoji)

    assert display == "a basic prompt"
    assert prompt == "a basic prompt Respond only with emojis. No text."
