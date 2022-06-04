from typing import NoReturn


# py311 introduces typing.assert_never which uses the typing.Never
def assert_never(_: NoReturn) -> NoReturn:
    assert False
