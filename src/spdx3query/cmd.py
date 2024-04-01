# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

from abc import abstractmethod

COMMANDS = []


def register(name, description):
    def func(cls):
        assert issubclass(cls, Command)
        COMMANDS.append((name, description, cls))
        return cls

    return func


class CommandExit(Exception):
    def __init__(self, exit_code):
        self.exit_code = exit_code


class Command(object):
    @classmethod
    @abstractmethod
    def get_args(cls, parser):
        pass

    @classmethod
    @abstractmethod
    def handle(cls, args, doc):
        pass
