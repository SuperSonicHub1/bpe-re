# bpe-re

A basic regular expression engine for the
[byte pair encodings](https://en.wikipedia.org/wiki/Byte_pair_encoding) of
[OpenAI's LLMs](https://github.com/openai/tiktoken).

I've been nerd-sniped yet again: https://mastodon.social/@rrika/110220304288351185

Uses the builder pattern as a replacement for
a text-based DSL, and supports the basic RE
operators `.?+*[]`.

## Example Usage

```py
from bpe_re import PatternBuilder

text = "I love chicken."

pattern = (
    PatternBuilder()
		.one(b"I")
		.optional(b"do")
		.set({b" love", b" hate"})
		.one(b" chicken")
		.one(b".")
)
print(
    pattern.build("cl100k_base").matches(text)
    and 
	pattern.build("cl100k_base").matches(text.replace("love", "hate"))
)
```

## Miscellaneous Thoughts

I whipped this up in only two hours even though I've never written 
or have heavily looked into the internals of a regular expression engine
before; guess all that reading about automata is finally starting to do
the body good.

This project could be expanded, but I don't think regex for BPE data has
any real-world use case, so I'm not interested; this was just something I
did to fill time while I waited for a bus.

If I were to add one feature, I would get rid of `tiktoken` and use
`transformers`' GPT-2 implementation to support searching for words within a certain
radius of a token; that would allow for a more fuzzy parsing which might actually be useful.
