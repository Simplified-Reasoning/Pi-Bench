from typing import Literal, get_args


STATUS_LITERAL = Literal["active", "do_not_disturb", "away"]
VALID_STATUSES = get_args(STATUS_LITERAL)
