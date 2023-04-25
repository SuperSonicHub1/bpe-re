"""
https://mastodon.social/@rrika/110220304288351185
"""
from typing import Protocol, Union, List, Optional as OptionalType, Set as SetType
from tiktoken import Encoding, get_encoding
from enum import Enum, auto
from collections import deque

# TODO: support matching on string sequences
# alongside 
Token = Union[bytes, int]

def byte_to_token(token: bytes, encoding: Encoding) -> int:
	return encoding.encode_single_token(token)

class MatchingState(Enum):
	MatchConsume = auto()
	MatchNoConsume = auto()
	Continue = auto()
	NoMatch = auto()

class Operation(Protocol):

	def matches(self, token: int, encoding: Encoding) -> MatchingState:
		...

class One(Operation):
	token: Token

	def __init__(self, token: Token) -> None:
		self.token = token

	def matches(self, token_to_match: Token, encoding: Encoding) -> MatchingState:
		token = byte_to_token(self.token, encoding) if isinstance(self.token, bytes) else self.token
		if token == token_to_match:
			return MatchingState.MatchConsume
		else:
			return MatchingState.NoMatch

class Set(Operation):
	tokens: SetType[Token]

	def __init__(self, tokens: SetType[Token]) -> None:
		if not len(tokens):
			raise TypeError("Zero tokens in set.")

		self.tokens = tokens

	def matches(self, token_to_match: Token, encoding: Encoding) -> MatchingState:
		tokens = {
			byte_to_token(token, encoding)
			if isinstance(token, bytes)
			else token
			for token
			in self.tokens
		}

		if token_to_match in tokens:
			return MatchingState.MatchConsume
		else:
			return MatchingState.NoMatch

class OneOrMore(Operation):
	token: Token
	encountered: bool

	def __init__(self, token: Token) -> None:
		self.token = token
		self.encountered = False

	def matches(self, token_to_match: Token, encoding: Encoding) -> MatchingState:
		token = byte_to_token(self.token, encoding) if isinstance(self.token, bytes) else self.token
		if token == token_to_match:
			self.encountered = True
			return MatchingState.Continue
		else:
			return MatchingState.MatchNoConsume if self.encountered else MatchingState.NoMatch
		
class ZeroOrMore(Operation):
	token: Token

	def __init__(self, token: Token) -> None:
		self.token = token
		self.encountered = False

	def matches(self, token_to_match: Token, encoding: Encoding) -> MatchingState:
		token = byte_to_token(self.token, encoding) if isinstance(self.token, bytes) else self.token
		if token == token_to_match:
			return MatchingState.Continue
		else:
			return MatchingState.MatchNoConsume

class Optional(Operation):
	"""
	TODO: In normal regular expressions, ".?.?.?" will
	match on an empty string. Should our optional operator
	have the same behavior? If so, how do we now handling
	matching on the EOT token
	(just assert it before running the pattern?)
	and handle our out-of-tokens check?
	"""
	token: Token

	def __init__(self, token: Token) -> None:
		self.token = token

	def matches(self, token_to_match: Token, encoding: Encoding) -> MatchingState:
		token = byte_to_token(self.token, encoding) if isinstance(self.token, bytes) else self.token
		if token == token_to_match:
			return MatchingState.MatchConsume
		else:
			return MatchingState.MatchNoConsume

class EndOfText(Operation):
	"""
	As this operation has no mutable state, it can be a singleton.
	"""
	__instance__: OptionalType['EndOfText'] = None

	def __init__(self) -> None:
		pass

	def matches(self, token_to_match: Token, encoding: Encoding) -> MatchingState:
		if token_to_match == encoding.eot_token:
			return MatchingState.MatchConsume 
		else:
			return MatchingState.NoMatch
		
	@staticmethod
	def get() -> 'EndOfText':
		if not EndOfText.__instance__:
			EndOfText.__instance__ = EndOfText()
		return EndOfText.__instance__

class Any(Operation):
	"""
	TODO: Could be a singleton in the future, but not right now with
	the way PatternBuilder constructs operations.
	"""
	def __init__(self) -> None:
		pass

	def matches(self, token_to_match: Token, encoding: Encoding) -> MatchingState:
		return MatchingState.MatchConsume

class Pattern:
	operations: List[Operation]
	encoding: Encoding

	def __init__(self, operations: List[Operation], encoding: Encoding) -> None:
		self.operations = operations
		self.encoding = encoding

	def matches(self, text: str) -> bool:
		operation_index = 0
		tokens = deque(self.encoding.encode(text))
		
		while len(tokens):
			if operation_index >= (len(self.operations) - 1):
				# We finished matching on all of our operations early.
				return True

			token = tokens.popleft()
			
			state = self.operations[operation_index].matches(token, self.encoding)

			# !DEBUG!
			print(state)

			# TODO: Generalize Match{No,}Consume behavior to
			# support arbitrary inner expressions.
			if state == MatchingState.MatchConsume:
				operation_index += 1
			elif state == MatchingState.MatchNoConsume:
				tokens.appendleft(token)
				operation_index += 1
			elif state == MatchingState.Continue:
				continue
			# MatchingState.NoMatch
			else:
				return False

		# If we're here, we either perfectly matched all of our tokens
		# or ran out before we could finish.
		return operation_index >= (len(self.operations) - 1)

class PatternBuilder:
	"""
	Being able to create patterns on demand in here makes the
	problem better, but more work needs to done for us to cross the
	finish line of no external mutability.
	"""
	operations: List

	def __init__(self) -> None:
		"""TODO: Flags?"""
		self.operations = []
	
	def one(self, token: Token) -> 'PatternBuilder':
		self.operations.append([One, [token]])
		return self

	def one_or_more(self, token: Token) -> 'PatternBuilder':
		self.operations.append([OneOrMore, [token]])
		return self

	def optional(self, token: Token) -> 'PatternBuilder':
		self.operations.append([Optional, [token]])
		return self

	def zero_or_more(self, token: Token) -> 'PatternBuilder':
		self.operations.append([ZeroOrMore, [token]])
		return self
	
	def any(self,) -> 'PatternBuilder':
		self.operations.append([Any, ()])
		return self
	
	def set(self, tokens: SetType[Token]) -> 'PatternBuilder':
		self.operations.append([Set, [tokens]])
		return self

	def build(self, encoding_name: str) -> Pattern:
		return Pattern([*(operation(*args) for operation, args in self.operations), EndOfText.get()], get_encoding(encoding_name))
