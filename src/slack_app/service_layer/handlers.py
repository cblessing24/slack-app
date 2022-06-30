from collections.abc import ItemsView
from typing import Any, Protocol, Type, TypeVar, Union, cast

from ..adapters.notifications import AbstractNotifications
from ..domain import commands, events, model
from ..domain.commands import Command
from ..domain.events import Event
from .unit_of_work import AbstractUnitOfWork, R


def subscribe(command: commands.Subscribe, uow: AbstractUnitOfWork[R]) -> None:
    with uow:
        channel = uow.channels.get(model.ChannelName(command.channel_name))
        if not channel:
            channel = model.Channel(model.ChannelName(command.channel_name))
            uow.channels.add(channel)
        subscription = model.Subscription(
            model.ChannelName(command.channel_name), model.User(command.subscriber), model.Keyword(command.keyword)
        )
        channel.subscribe(subscription)
        uow.commit()


def list_subscribers(command: commands.ListSubscribers, uow: AbstractUnitOfWork[R]) -> set[str]:
    with uow:
        channel = uow.channels.get(model.ChannelName(command.channel_name))
        if not channel:
            raise ValueError("Unknown channel")
        message = model.Message(
            model.ChannelName(command.channel_name), model.User(command.author), model.Text(command.text)
        )
        return set(channel.find_subscribed(message))


def list_subscriptions(command: commands.ListSubscriptions, uow: AbstractUnitOfWork[R]) -> set[str]:
    with uow:
        channel = uow.channels.get(model.ChannelName(command.channel_name))
        if not channel:
            raise ValueError("Unknown channel")
        return {s.keyword for s in channel.subscriptions if s.subscriber == model.User(command.subscriber)}


def unsubscribe(command: commands.Unsubscribe, uow: AbstractUnitOfWork[R]) -> None:
    with uow:
        channel = uow.channels.get(model.ChannelName(command.channel_name))
        if not channel:
            raise ValueError("Unknown channel")
        subscription = model.Subscription(
            model.ChannelName(command.channel_name), model.User(command.subscriber), model.Keyword(command.keyword)
        )
        channel.unsubscribe(subscription)
        uow.commit()


Message = Union[commands.Command, events.Event]


def send_subscribed_notification(event: events.Subscribed, notifications: AbstractNotifications) -> None:
    notifications.respond(f"You will be notified if '{event.keyword}' is mentioned in <#{event.channel_name}>")


def send_unsubscribed_notification(event: events.Unsubscribed, notifications: AbstractNotifications) -> None:
    notifications.respond(
        f"You will be no longer notified if '{event.keyword}' is mentioned in <#{event.channel_name}>"
    )


def send_unknown_subscription_notification(
    event: events.UnknownSubscription, notifications: AbstractNotifications
) -> None:
    notifications.respond(f"You are not subscribed to '{event.keyword}' in <#{event.channel_name}>")


M = TypeVar("M", bound=Message, contravariant=True)


class MessageHandler(Protocol[M]):
    def __call__(self, message: M) -> Any:
        ...


C = TypeVar("C", bound=commands.Command, contravariant=True)


class CommandHandlerMap(Protocol):
    def __getitem__(self, command: Type[C]) -> MessageHandler[C]:
        """Return the appropriate command handler for the given command."""

    def items(self) -> ItemsView[Type[Command], MessageHandler[Command]]:
        """Return a view of the command handlers, keyed by command type."""


COMMAND_HANDLERS = cast(
    CommandHandlerMap,
    {
        commands.Subscribe: subscribe,
        commands.ListSubscriptions: list_subscriptions,
        commands.ListSubscribers: list_subscribers,
        commands.Unsubscribe: unsubscribe,
    },
)


E = TypeVar("E", bound=events.Event, contravariant=True)


class EventHandlerMap(Protocol):
    def __getitem__(self, event: Type[E]) -> list[MessageHandler[E]]:
        """Return the appropriate list of event handlers for the given event."""

    def items(self) -> ItemsView[Type[Event], list[MessageHandler[Event]]]:
        """Return a view of the event handlers, keyed by event type."""


EVENT_HANDLERS = cast(
    EventHandlerMap,
    {
        events.Subscribed: [send_subscribed_notification],
        events.Unsubscribed: [send_unsubscribed_notification],
        events.UnknownSubscription: [send_unknown_subscription_notification],
        events.AlreadySubscribed: [],
    },
)
