text = "I love MIT."

from bpe_re import PatternBuilder

pattern = (
    PatternBuilder()
		.one(b"I")
		.set({b" love", b" hate"})
		.one(b" MIT")
		.one(b".")
)
print(
    pattern.build("cl100k_base").matches(text)
    and 
	pattern.build("cl100k_base").matches(text.replace("love", "hate"))
)
