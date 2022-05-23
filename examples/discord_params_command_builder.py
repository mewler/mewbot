# Refinement of the no-params method - to deal with functions which have parameters
# inspired by https://docs.pycord.dev/

import argparse
from typing import Tuple, Union, List
from copy import deepcopy

import functools
import inspect
import shlex

from collections import OrderedDict

from argparse import ArgumentParser as BaseArgumentParser

import functools
import logging

from typing import Any, Dict, Set, Type, Callable, AnyStr
from mewbot.io.discord import DiscordInputEvent, DiscordOutputEvent
from mewbot.core import InputEvent, OutputEvent

from mewbot.api.v1 import Trigger, Action


class ParserError(Exception):
    pass


# ... for the moment ... might be okay to not actually support all the callable options in python
# ... going to work on that later
class SafeArgParserArgumentParser(BaseArgumentParser):

    def __init__(self, *args, func_signature, **kwargs) -> None:
        """
        Passthrough for the
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

        self.func_signature = func_signature

    def parse_command(self, cmd_str: str = "") -> Dict[str, Any]:
        parsed_tokens = shlex.split(cmd_str)

        # Need to match the arguments to the signature to construct and return the args and kwargs
        return vars(self.parse_args(parsed_tokens))

    def error(self, message) -> None:
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        raise ParserError(message)


# ... for the moment ... might be okay to not actually support all the callable options in python
# ... going to work on that later
class PythonArgumentParser(BaseArgumentParser):

    def __init__(self, *args, func_signature, **kwargs) -> None:
        """

        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)

        self.func_signature = func_signature

    def __call__(self, cmd_str: str) -> Dict[str, Any]:
        return self.parse_command(cmd_str=cmd_str)

    def parse_command(self, cmd_str: str) -> Dict[str, Any]:

        command_lexar = shlex.shlex(cmd_str, punctuation_chars="=")
        lexed_tokens = self._lexed_tokens_preflight(list(command_lexar))

        parsed_tokens, kwargs = self.consume_kwargs(lexed_tokens)

        if not parsed_tokens:
            return kwargs

        if kwargs is not None and len(kwargs) == len(self.func_signature) and parsed_tokens:
            raise ParserError("All args accounted for, but tokens remain")

        if kwargs is None:
            kwargs = dict()

        # Now matching to the functional signature to try and include the rest
        for token in parsed_tokens:
            # Trying to match it to the known functional signature
            for cmd_name in self.func_signature:
                # We already have a candidate for that - carry on
                if cmd_name in kwargs:
                    continue

                # We do not have a candidate for that - assign it and continue
                kwargs[cmd_name] = token
                break

        # We have a complete match and nothing else need be done
        if len(kwargs) == len(self.func_signature):
            return kwargs

        raise ParserError("Could not completely parse input")

    def _lexed_tokens_preflight(self, lexed_tokens: List[str]) -> List[str]:
        """
        Preform some post lexing processing on the tokens to deal with, e.g. the
        outer layer of quotes in a pythonic way.
        :param lexed_tokens:
        :return:
        """
        clean_tokens = []

        for token in lexed_tokens:
            if not isinstance(token, str):
                clean_tokens.append(token)
                continue

            if len(token) in (0, 1):
                clean_tokens.append(token)
                continue

            if token[0] == '\"' and token[-1] == "\"":
                clean_tokens.append(token[1:-1])
                continue

            clean_tokens.append(token)

        return clean_tokens

    def consume_kwargs(self, parsed_tokens: List[str], found_kwargs: Union[None, List[str]] = None):
        """
        Parse out the kwargs from the tokens.
        :return:
        """
        # No kwargs present, so abort
        if "=" not in parsed_tokens:
            return parsed_tokens, found_kwargs

        clearer_tokens = []

        # If the current token is "=", and the previous token is a known argument, then consume it, the previous
        # token and the next one
        found_kwargs = dict() if found_kwargs is None else found_kwargs
        for pos in range(len(parsed_tokens)):

            if pos == 0:
                clearer_tokens.append(parsed_tokens[pos])
                continue

            previous_token = parsed_tokens[pos - 1]

            if parsed_tokens[pos] == "=" and previous_token in self.func_signature.keys():

                try:
                    next_token = parsed_tokens[pos + 1]
                except IndexError:
                    raise ParserError(parsed_tokens)

                if previous_token in found_kwargs:
                    raise ParserError("Attempt to define a variable twice?")

                found_kwargs[previous_token] = next_token

                return self.consume_kwargs(
                    parsed_tokens=deepcopy(parsed_tokens[: pos - 1])
                    + deepcopy(parsed_tokens[pos + 2 :]),
                    found_kwargs=found_kwargs,
                )

            clearer_tokens.append(parsed_tokens[pos])

        return clearer_tokens, found_kwargs

    def error(self, message):
        """error(message: string)

        Prints a usage message incorporating the message to stderr and
        exits.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        raise ParserError(message)


class DiscordTriggerActionFactory:
    """
    Register commands with this factory using the decorators it provides. Then call build to get back a trigger and
    action
    """

    def __init__(self):
        self.commands = dict()  # Keyed with the function name and valued with the function
        self.arg_parsers = dict()

        self._trigger = None
        self._action = None

    @staticmethod
    def _get_signature_parameters(target_func):
        return OrderedDict(inspect.signature(target_func).parameters)

    def text_cmd(self, *args, **kwargs):
        """
        Used to decorate a text command that takes no arguments - such as "time".
        Text trigger will be the name of the function - or you can override it with the "trigger" keyword
        :return:
        """
        if len(args) > 1:
            raise NotImplementedError("no_argument_text_cmd decorator does not support ")

        # bracketless mode
        # Callable was deprecated and then undepreciated
        if len(args) == 1 and callable(args[0]) and not kwargs:
            self.register_command(func_trigger=args[0].__name__, output_func=args[0])
            return

        # Empty bracket mode
        if not args and not kwargs:
            return self.text_cmd

        if not args and kwargs:
            return functools.partial(self.text_cmd, **kwargs)

        # We have a full complement of kwargs and the command in hand - now process if
        if "command_trigger" in kwargs:
            command_trigger = kwargs["command_trigger"]
        else:
            command_trigger = args[0].__name__

        if "parser_class" in kwargs:
            parser_class = kwargs["parser_class"]
        else:
            parser_class = None

        # Same object as used in the classes - thus can be freely updated
        self.register_command(command_trigger, args[0], parser_class)

    # Storing the trigger functions here
    def register_command(self, func_trigger, output_func, parser_class=None):
        """
        Register a command.
        :param func_trigger:
        :param output_func:
        :param parser_class: Class which will do the work of converting the text into args and kwargs
        :return:
        """

        # Note - I considered storing the trigger_func and the output_func together in a dict
        # but this turned out not to be viable as the hashes where not useful for my purposes
        # i.e.
        #
        # test = lambda x: x.text == "fish"
        #
        # test_2 = lambda x: x.text == "fish"
        #
        # had different hashes. So, instead, storing the function name and the signature

        assert isinstance(func_trigger, str)

        # Will be used to introspect and build a trigger_func - if one is not provided
        func_signature = self._get_signature_parameters(output_func)

        # We are in the case where there are no parameters for the output_func
        # So we're using a very basic trigger function - just match to a string
        if isinstance(func_trigger, str) and not func_signature:

            self.commands[func_trigger] = output_func
            self.arg_parsers[func_trigger] = None
            return

        if parser_class is None:
            functional_parser = self.get_parser_from_sig(
                func_name=func_trigger,
                func_signature=func_signature,
                parser_class=SafeArgParserArgumentParser,
            )
        else:
            functional_parser = self.get_parser_from_sig(
                func_name=func_trigger,
                func_signature=func_signature,
                parser_class=parser_class,
            )

        self.commands[func_trigger] = output_func
        self.arg_parsers[func_trigger] = functional_parser

    # For the moment, dealing with purely string based arguments - moving onto parsed arguments later
    def get_parser_from_sig(self, func_name, func_signature, parser_class):
        """
        Take a functional signature and construct an argparser from it.
        :param func_name: The name of the function for the help command
        :param func_signature: An OrderedDict of the functional signature
        :param parser_class: A class, ideally derived from argparser, which does the work of turning text into command
                             line arguments.
        :return:
        """
        # argparse is the parsing option most likely to be fully featured and safe
        # note - using shlex.split to properly tokenize the incoming string
        import argparse
        import shlex

        functional_parser = parser_class(
            prog=func_name,
            description=f"An internal mewbot function designed to present function {func_name} on a channel. "
            f"If you are seeing this on the command line then something has gone very not right.",
            exit_on_error=False,  # sys.exit is undesirable,
            func_signature=func_signature,  # Going to need this later when parsing the incoming strs
        )

        # Itterate over the parameters
        for arg_name in func_signature:
            arg_param = func_signature[arg_name]

            if arg_param.kind == inspect.Parameter.POSITIONAL_ONLY:
                self._add_positional_only(arg_param, functional_parser)
                break

            if arg_param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                self._add_positional_or_keyword(arg_param, functional_parser)
                break

            # Note to self - investigate later - can you do variable assignment/mutation in these?
            # IF SO - GIANT SECURITY HOLE
            raise NotImplementedError(f"{arg_name} of unsupported type {arg_param.kind}")

        return functional_parser

    def _add_positional_only(self, arg_param, functional_parser):
        """
        Add a POSITIONAL_ONLY argument to a functional parser.
        :param arg_param:
        :param functional_parser:
        :return:
        """
        assert arg_param.kind == inspect.Parameter.POSITIONAL_ONLY

        functional_parser.add_argument(arg_param.name)

    def _add_positional_or_keyword(self, arg_param, functional_parser):
        """
        Add a POSITIONAL_OR_KEYWORD argument to a functional_parser
        :param arg_param:
        :param functional_parser:
        :return:
        """
        assert arg_param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD

        if arg_param.default == inspect.Parameter.empty:
            # Adding a simple positional argument - no default
            functional_parser.add_argument(arg_param.name)
        else:
            # Add a simple position argument - with default
            # As a default is provided, the argument is not required
            functional_parser.add_argument(
                arg_param.name, nargs="?", default=arg_param.default
            )

    def trigger_action_factory(self):
        """
        Produce the trigger and the action and return.
        :return:
        """

        class TextFieldDictTrigger(Trigger):
            """
            Triggers off the keys of a dictionary - and matches them to the text field of a DiscordInputEvent.
            """

            _funcs_dict: Dict[AnyStr, Callable] = dict()
            _funcs_tuple: Tuple[str]  # Used for efficient match of the first token
            # Which determines if we proceed to action to trigger

            def __init__(self) -> None:
                super().__init__()
                self._logger = logging.getLogger(__name__ + type(self).__name__)

            @classmethod
            def update_funcs_dict(cls, new_funcs_dict: Dict[AnyStr, Callable]) -> None:
                cls._funcs_dict = new_funcs_dict
                cls._funcs_tuple = tuple(str(_) for _ in cls._funcs_dict.keys())

            @staticmethod
            def consumes_inputs() -> Set[Type[InputEvent]]:
                return {DiscordInputEvent}

            def matches(self, event: InputEvent) -> bool:
                if not isinstance(event, DiscordInputEvent):
                    return False

                # Tokenize on spaces - then use the first one to check against the stored funcs
                cmd_tokens = shlex.split(event.text, posix=True)
                if not cmd_tokens:
                    return False

                if cmd_tokens[0] in self._funcs_tuple:
                    return True

                return False

        class TextFieldDictAction(Action):
            """
            Match the input message to the function, execute the function and put the result on the wire.
            """

            _funcs_dict: Dict[AnyStr, Callable] = dict()
            _parser_dict: Dict[AnyStr, Callable] = dict()

            def __init__(self) -> None:
                super().__init__()
                self._logger = logging.getLogger(__name__ + type(self).__name__)

            @classmethod
            def update_funcs_dict(cls, new_funcs_dict: Dict[AnyStr, Callable], new_parser_dict: Dict[AnyStr, Callable]) -> None:
                """

                :param new_funcs_dict:
                    Keyed with the name of the function
                        (which is also the text used to invoke it)
                    Valued with the function itself
                :param new_parser_dict:
                :return:
                """

                # Every function should have an entry in both dicts
                # Even if the parser is None
                assert set(new_funcs_dict.keys()) == set(new_parser_dict.keys())

                cls._funcs_dict = new_funcs_dict
                cls._parser_dict = new_parser_dict

            @staticmethod
            def consumes_inputs() -> Set[Type[InputEvent]]:
                return {DiscordInputEvent}

            @staticmethod
            def produces_outputs() -> Set[Type[OutputEvent]]:
                return {DiscordOutputEvent}

            async def act(self, event: InputEvent, state: Dict[str, Any]) -> None:
                """
                Construct a DiscordOutputEvent with the result of performing the calculation.
                Put it on the wire.
                """
                if not isinstance(event, DiscordInputEvent):
                    self._logger.warning("Received wrong event type %s", type(event))
                    return

                self._logger.info("Called with text %s", event.text)

                # Tokenize on spaces - then use the first one to check against the stored funcs
                cmd_tokens = shlex.split(event.text, posix=True)
                if not cmd_tokens:
                    return

                target_func_name = str(cmd_tokens[0])

                # This will, eventually, depend on the error handling
                if target_func_name not in self._funcs_dict or target_func_name not in self._parser_dict:
                    return

                target_func = self._funcs_dict[target_func_name]
                target_parser = self._parser_dict[target_func_name]

                # In this case, no text is expected - so ignore - just run the func and return
                if target_parser is None:
                    rtn_text = target_func()
                else:

                    # Strip the string of the command and pass it to parser
                    target_cmd = event.text[len(target_func_name):]

                    cmd_kwargs = target_parser.parse_command(target_cmd)

                    if cmd_kwargs is None:
                        rtn_text = target_func()
                    else:

                        try:
                            rtn_text = target_func(**cmd_kwargs)
                        except Exception as e:
                            rtn_text = f"Exception was generated - {e.args}"

                test_event = DiscordOutputEvent(
                    text=rtn_text, message=event.message, use_message_channel=True
                )

                await self.send(test_event)

        if self._trigger is None:
            dict_trigger = TextFieldDictTrigger
            dict_trigger.update_funcs_dict(self.commands)
            self._trigger = dict_trigger

        if self._action is None:
            dict_action = TextFieldDictAction
            dict_action.update_funcs_dict(self.commands, self.arg_parsers)
            self._action = dict_action

        return self._trigger, self._action



# Problme - we need to convert an incoming string into a python functional call
# Ideally without hideously compromising security

# Worrying about alternative parsing options. Effectively alternative functional signatures
# Really would be cool if we could tie into the python functional parser at some point
# Without opening mammoth security holes


# Flow
# - In the Trigger
# - - Tokenize the input string
# - - Compare the first token to the command trigger tokens
# - - If it succeeds - pass it on to the Action

# - In the Action
# - - Could be combined, or a single Action per command

# We're mapping a string to a set of python commands
# So, probably, argparse is the way to go - it being built for that


test_trigger_action_factory = DiscordTriggerActionFactory()


@test_trigger_action_factory.text_cmd()
def date() -> str:

    from datetime import date

    today = date.today()

    return str(today.strftime("%d/%m/%Y"))


@test_trigger_action_factory.text_cmd
def time() -> str:

    from datetime import datetime

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")

    return f"Current time is {current_time}"


# Other command kwargs
# - parser_type
# - error_handling - ("print", "transmit", "suppress")
@test_trigger_action_factory.text_cmd(command_trigger="hello")
def some_arbitrary_function_name() -> str:
    return "world"


@test_trigger_action_factory.text_cmd
def print_no_arguments() -> str:
    return "No arguments"


@test_trigger_action_factory.text_cmd
def print_one_argument(arg1: str) -> str:
    return f"An argument! {arg1}"


@test_trigger_action_factory.text_cmd
def print_one_argument_with_default(arg1: str = "default value was provided") -> str:
    return f"An argument! {arg1}"


@test_trigger_action_factory.text_cmd(parser_class=PythonArgumentParser)
def print_one_argument_with_default_python_arg_parser(
    arg1: str = "default value was provided",
) -> str:
    return f"An argument! {arg1}"


@test_trigger_action_factory.text_cmd(parser_class=PythonArgumentParser)
def print_two_arguments_with_default_python_arg_parser(
    arg1: str = "default value was provided", arg2: str = "another default"
) -> str:
    return f"An argument! {arg1} {arg2}"


# Todo: Test what happens when the names are degenerate
# Todo: An error or warning if we try and create two functions with the same name
# Todo: Give the user the option of attatching their own argument parser - if they want to do that


@test_trigger_action_factory.text_cmd(command_trigger="hello_again")
def another_arbitrary_function_name(
    arg1: str = "default value was provided for renamed func",
) -> str:
    return f"An argument for an arbitary func! {arg1}"


# Considering strings later

# so - what sort of parsing is desirable?
# I mean, people can write and include their own  but what ones should be baked in?
# Such that they can be chosen at config time
# Options

# - emulation of python - as far as possible
# - - so - comma seperated tokens, parsed into args and kwargs - (quotes are assumed in input - emulating python, after all

# - - "test_string" -> ("test_string", ), {}
# - - "test string" -> ("test string", ), {}
# - - test_string -> Error - we're emulating python after all - note - this might be a step too far
# - - test string -> Error - we're emulating python after all

# - - "test_string", "and_another_one" -> ("test_string", "and_another_one"), {}
# - - time="fire" -> (), {"time": "fire"}
# - - "test_string", "and_another_one", time="fire" -> ("test_string", "and_another_one"), {"time": "fire"}

# Note - we can feed the output of this into conversion logic later
# Once parsing and conversion is complete, we can match to signatures


# - python_enhanced - smart detection of spaces as brackets
# - - so - space seperated tokens, parsed into args and kwargs - (quotes helpful guides, but not required)
# - - "test_string" -> ("test_string", ), {}
# - - "test string" -> ("test string", ), {}
# - - test_string -> ("test string", ), {}
# - - test string -> ("test", "string"), {}

# - - "test_string" "and_another_one" -> ("test_string", "and_another_one"), {}
# - - time="fire" -> (), {"time": "fire"}
# - - "test_string" "and_another_one" time="fire" -> ("test_string", "and_another_one"), {"time": "fire"}
# - - time="fire" "test_string" "and_another_one" time="fire" -> Error
# - - time="fire" "test_string" "and_another_one"  -> ("test_string", "and_another_one"), {"time": "fire"}
# - - time = "fire" "test_string" "and_another_one"  -> ("test_string", "and_another_one"), {"time": "fire"}


# USING THE BASE ARGPARSER
import shlex

test_parser_print_one_arg = test_trigger_action_factory.arg_parsers["print_one_argument"]

# WORKS - test_parser_print_one_arg.parse_args(shlex.split("'some argument'"))
# DOES NOT WORK - test_parser_print_one_arg.parse_args(shlex.split("arg1='some argument'"))
# DOES NOT WORK - test_parser_print_one_arg.parse_args(shlex.split("arg1 'some argument'"))
# DOES NOT WORK - test_parser_print_one_arg.parse_args(shlex.split("-arg1 'some argument'"))
# DOES NOT WORK - test_parser_print_one_arg.parse_args(shlex.split(""))

# So that's why we're going to be why we need the alternative signatures
# Or, possibly, tell argparser to be more general

# Running off the default - SafeArgParserArgumentParser
# assert test_parser_print_one_arg.parse_command("") == {'arg1': 'test_string'}
assert test_parser_print_one_arg.parse_command("test_string") == {"arg1": "test_string"}
try:
    assert test_parser_print_one_arg.parse_command("test_string and another str") == {
        "arg1": "test_string and another str"
    }
except ParserError:
    pass
try:
    assert test_parser_print_one_arg.parse_command("") == {"arg1": "test_string"}
except ParserError:
    pass
try:
    assert test_parser_print_one_arg.parse_command() == {"arg1": "test_string"}
except ParserError:
    pass
assert test_parser_print_one_arg.parse_command(
    "'There was a story and it went like this'"
) == {"arg1": "There was a story and it went like this"}
try:
    assert test_parser_print_one_arg.parse_command("-arg1 test_string") == {
        "arg1": "test_string"
    }
except ParserError:
    pass

# WORKS - test_parser_print_one_argument_with_default.parse_args([])
# DOES NOT WORK - test_parser_print_one_argument_with_default.parse_args(shlex.split("arg1 'There was a story and it went like this'"))
# DOES NOT WORK - test_parser_print_one_argument_with_default.parse_args(shlex.split("arg1='There was a story and it went like this'"))
# WORKS - test_parser_print_one_argument_with_default.parse_args(shlex.split("'There was a story and it went like this'"))

# Running off the default - SafeArgParserArgumentParser
test_parser_print_one_argument_with_default = test_trigger_action_factory.arg_parsers[
    "print_one_argument_with_default"
]
assert test_parser_print_one_argument_with_default.parse_command("test_string") == {
    "arg1": "test_string"
}
assert test_parser_print_one_argument_with_default.parse_command("") == {
    "arg1": "default value was provided"
}
assert test_parser_print_one_argument_with_default.parse_command() == {
    "arg1": "default value was provided"
}
assert test_parser_print_one_argument_with_default.parse_command(
    "'There was a story and it went like this'"
) == {"arg1": "There was a story and it went like this"}
try:
    assert test_parser_print_one_argument_with_default.parse_command("-arg1 test_string") == {
        "arg1": "test_string"
    }
except ParserError:
    pass
try:  # This is the expected behavior for argparser - which cannot mix positional and keyword strs
    assert test_parser_print_one_argument_with_default.parse_command(
        "--arg1 test_string"
    ) == {"arg1": "test_string"}
except ParserError:
    pass


test_parser_print_one_argument_with_default_python_arg_parser = (
    test_trigger_action_factory.arg_parsers[
        "print_one_argument_with_default_python_arg_parser"
    ]
)
# assert test_parser_print_one_argument_with_default_python_arg_parser.parse_command("test_string") == {'arg1': 'test_string'}
assert test_parser_print_one_argument_with_default_python_arg_parser.parse_command(
    "arg1=test_string"
) == {"arg1": "test_string"}
assert test_parser_print_one_argument_with_default_python_arg_parser.parse_command(
    "arg1 = test_string"
) == {"arg1": "test_string"}
try:
    assert test_parser_print_one_argument_with_default_python_arg_parser.parse_command(
        "arg1 = test_string arg1 = more_test"
    ) == {"arg1": "test_string"}
except ParserError:
    pass


test_parser_print_two_arguments_with_default_python_arg_parser = (
    test_trigger_action_factory.arg_parsers[
        "print_two_arguments_with_default_python_arg_parser"
    ]
)
assert test_parser_print_two_arguments_with_default_python_arg_parser.parse_command(
    "arg1=test_string"
) == {"arg1": "test_string"}
assert test_parser_print_two_arguments_with_default_python_arg_parser.parse_command(
    "test_string and_again"
) == {"arg1": "test_string", "arg2": "and_again"}
assert test_parser_print_two_arguments_with_default_python_arg_parser.parse_command(
    "arg1=test_string arg2=another_test_str"
) == {"arg1": "test_string", "arg2": "another_test_str"}
try:
    test_parser_print_two_arguments_with_default_python_arg_parser.parse_command(
        "arg1=test_string arg3=another_test_str"
    )
except ParserError:
    pass
try:
    assert test_parser_print_two_arguments_with_default_python_arg_parser.parse_command(
        "arg1=test_string arg2=another_test_str arg1=argle"
    ) == {"arg1": "test_string", "arg2": "another_test_str"}
except ParserError:
    pass
assert test_parser_print_two_arguments_with_default_python_arg_parser.parse_command(
    'arg1="test_string"'
) == {"arg1": "test_string"}
assert test_parser_print_two_arguments_with_default_python_arg_parser.parse_command(
    'arg1  =  "test_string"  '
) == {"arg1": "test_string"}
assert test_parser_print_two_arguments_with_default_python_arg_parser.parse_command(
    ' "test string now with spaces" "not another string - this is silly" '
) == {"arg1": "test string now with spaces", "arg2": "not another string - this is silly"}


# Thought - provide a general method of catching errors and getting them on the wire?


# Aim - register alternative funcions with the same name but a different signature
# Need to deal with alternative function triggers - support both?
# Something like


# @test_trigger_action_factory.text_cmd
# def print_one_argument(arg1: str) -> str:
#     return f"An argument! {arg1}"

# Followed by

# @test_trigger_action_factory.print_one_argument
# def print_one_argument(arg1: str, arg2: str) -> str:
#     return f"... Two arguments! {arg1}, {arg2} - this is the alt sig for this function"

# With resolution ... probably least surprising if it's in the order they where registered


# For later
# Somethink like
# @test_trigger_action_factory.DiscordInputEvent->DesktopNotificationOutputEvent
# Which decorates a function which takes a DiscordInputEvent as an argument
# Then either returns False, or a DesktopNotificationOutputEvent - depending on if the combined trigger works


TestDiscordTrigger, TestDiscordAction = test_trigger_action_factory.trigger_action_factory()
