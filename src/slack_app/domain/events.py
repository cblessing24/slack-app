from __future__ import annotations

from dataclasses import dataclass

from . import model


@dataclass(frozen=True)
class Event:
    """Base class for all events."""


@dataclass(frozen=True)
class Subscribed(Event):
    channel_name: model.ChannelName
    subscriber: model.User
    keyword: model.Keyword


@dataclass(frozen=True)
class AlreadySubscribed(Event):
    channel_name: model.ChannelName
    subscriber: model.User
    keyword: model.Keyword


@dataclass(frozen=True)
class UnknownSubscription(Event):
    channel_name: model.ChannelName
    subscriber: model.User
    keyword: model.Keyword


@dataclass(frozen=True)
class Unsubscribed(Event):
    channel_name: model.ChannelName
    subscriber: model.User
    keyword: model.Keyword


@dataclass(frozen=True)
class Mentioned(Event):
    channel_name: model.ChannelName
    subscriber: model.User
    keyword: model.Keyword
    author: model.User
    text: model.Text
