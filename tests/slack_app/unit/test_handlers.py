from __future__ import annotations

from dataclasses import dataclass

import pytest

from slack_app.adapters.notifications import AbstractNotifications
from slack_app.bootstrap import bootstrap
from slack_app.domain import commands
from slack_app.service_layer.messagebus import MessageBus
from slack_app.service_layer.unit_of_work import AbstractUnitOfWork

from .conftest import FakeRepository


class FakeUnitOfWork(AbstractUnitOfWork[FakeRepository]):
    def __init__(self) -> None:
        self.committed = False
        self.channels = FakeRepository()

    def _commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


class FakeNotifications(AbstractNotifications):
    @dataclass
    class Message:
        channel: str
        message: str

    def __init__(self) -> None:
        self.messages: list[FakeNotifications.Message] = []
        self.responses: list[str] = []

    def send(self, channel: str, message: str) -> None:
        self.messages.append(self.Message(channel, message))

    def respond(self, message: str) -> None:
        self.responses.append(message)


@pytest.fixture
def notifications() -> FakeNotifications:
    return FakeNotifications()


@pytest.fixture
def messagebus(notifications: FakeNotifications) -> MessageBus[FakeUnitOfWork]:
    messagebus = bootstrap(FakeUnitOfWork(), start_mappers=False, notifications=notifications)
    return messagebus


def test_subscription_gets_added(messagebus: MessageBus[FakeUnitOfWork]) -> None:
    messagebus.handle(commands.Subscribe(channel_name="general", subscriber="bob", keyword="hello"))
    subscriptions = messagebus.handle(commands.ListSubscriptions(channel_name="general", subscriber="bob"))
    assert subscriptions == [{"hello"}]


def test_added_subscription_gets_committed(messagebus: MessageBus[FakeUnitOfWork]) -> None:
    messagebus.handle(commands.Subscribe(channel_name="general", subscriber="bob", keyword="hello"))
    assert messagebus.uow.committed


def test_list_keywords_errors_for_unknown_channe(messagebus: MessageBus[FakeUnitOfWork]) -> None:
    with pytest.raises(ValueError, match="Unknown channel"):
        messagebus.handle(commands.ListSubscriptions(channel_name="general", subscriber="bob"))


def test_subscribers_are_returned(messagebus: MessageBus[FakeUnitOfWork]) -> None:
    in_keyword = ("general", "bob", "World")
    out_keyword = ("general", "alice", "World")
    author_keyword = ("general", "john", "Goodbye")
    for subscription in [in_keyword, out_keyword, author_keyword]:
        messagebus.handle(commands.Subscribe(*subscription))
    subscribers = messagebus.handle(
        commands.ListSubscribers(channel_name="general", author="john", text="Goodbye World")
    )
    assert subscribers == [{"bob", "alice"}]


def test_get_subscribers_errors_for_unknown_channel(messagebus: MessageBus[FakeUnitOfWork]) -> None:
    with pytest.raises(ValueError, match="Unknown channel"):
        messagebus.handle(commands.ListSubscribers(channel_name="general", author="john", text="Goodbye World"))


def test_can_unsubscribe(messagebus: MessageBus[FakeUnitOfWork]) -> None:
    messagebus.handle(commands.Subscribe(channel_name="general", subscriber="bob", keyword="hello"))
    messagebus.handle(commands.Unsubscribe(channel_name="general", subscriber="bob", keyword="hello"))
    subscriptions = messagebus.handle(commands.ListSubscriptions(channel_name="general", subscriber="bob"))
    assert subscriptions == [set()]


def test_unsubscribe_errors_for_unknown_channel(messagebus: MessageBus[FakeUnitOfWork]) -> None:
    with pytest.raises(ValueError, match="Unknown channel"):
        messagebus.handle(commands.Unsubscribe(channel_name="general", subscriber="bob", keyword="hello"))


def test_subscribed_notification_is_sent(
    messagebus: MessageBus[FakeUnitOfWork], notifications: FakeNotifications
) -> None:
    messagebus.handle(commands.Subscribe(channel_name="general", subscriber="bob", keyword="hello"))
    assert notifications.responses == ["You will be notified if 'hello' is mentioned in <#general>"]


def test_already_subscribed_notification_is_sent(
    messagebus: MessageBus[FakeUnitOfWork], notifications: FakeNotifications
) -> None:
    messagebus.handle(commands.Subscribe(channel_name="general", subscriber="bob", keyword="hello"))
    messagebus.handle(commands.Subscribe(channel_name="general", subscriber="bob", keyword="hello"))
    assert "You are already subscribed to 'hello' in <#general>" in notifications.responses


def test_unsubscribed_notifications_is_sent(
    messagebus: MessageBus[FakeUnitOfWork], notifications: FakeNotifications
) -> None:
    messagebus.handle(commands.Subscribe(channel_name="general", subscriber="bob", keyword="hello"))
    messagebus.handle(commands.Unsubscribe(channel_name="general", subscriber="bob", keyword="hello"))
    assert "You will be no longer notified if 'hello' is mentioned in <#general>" in notifications.responses


def test_unknown_subscription_notification_is_sent(
    messagebus: MessageBus[FakeUnitOfWork], notifications: FakeNotifications
) -> None:
    messagebus.handle(commands.Subscribe(channel_name="general", subscriber="bob", keyword="hello"))
    messagebus.handle(commands.Unsubscribe(channel_name="general", subscriber="bob", keyword="hello"))
    messagebus.handle(commands.Unsubscribe(channel_name="general", subscriber="bob", keyword="hello"))
    assert "You are not subscribed to 'hello' in <#general>" in notifications.responses
