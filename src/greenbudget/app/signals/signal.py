import contextlib
import functools
import weakref

from django import dispatch
from django.dispatch.dispatcher import _make_id
from django.utils.inspect import func_accepts_kwargs

from greenbudget.lib.utils import ensure_iterable


class Registry:
    """
    A maintained registry of the registered instances of :obj:`Signal` in the
    application.  The :obj:`Registry` is used for connecting and/or reconnecting
    all of the registered :obj:`Signal` in the application.
    """

    def __init__(self, signals=None):
        self._signals = signals or []

    @property
    def signals(self):
        return self._signals

    def add(self, signal):
        if signal.name is None:
            raise Exception(
                "A signal must be provided a name to be added to the "
                "internal registry."
            )
        elif signal.name in [sig.name for sig in self._signals]:
            raise Exception(
                "Cannot register multiple signals with the same name.")
        self._signals.append(signal)

    def get_signal(self, name):
        if name not in [sig.name for sig in self._signals]:
            raise LookupError("No registered signal with name %s." % name)
        return [sig for sig in self._signals if sig.name == name][0]


registry = Registry()


class Signal(dispatch.Signal):
    """
    An extension of Django's :obj:`django.dispatch.Signal` that implements
    functionality that this application requires.  This additional functionality
    and behavior includes the following:

    Sender Based Disconnect
    -----------------------
    With traditional Django signals, it is not possible to disconnect a signal
    from it's receivers for only a specific sender.  This extension makes this
    possible, such that we can temporarily disable a signal that is connected
    to all receivers registered for a specific sender type.

    Reconnection
    ------------
    With traditional Django signals, you can disconnect a signal from it's
    receiver.  However, doing so only temporarily on a systematic level is
    problematic, because in order to reconnect the receiver and have things
    behave as they previously did you need to reconnect the receiver with the
    exact same configuration that it was initially connected with (i.e. with
    the same sender, dispatch_uid and weak parameters).

    Here, this extension maintains a record of the connection parameters that
    were used to connect the :obj:`Signal` to each receiver, which allows us
    to disconnect a :obj:`Signal` instance from a given receiver (or all
    receivers) and then reconnect them in the exact same way they were
    originally connected in.

    This allows us to temporarily disable a signal while performing an action:

    >>> with signals.post_delete.disable():
    >>>     ...

    Furthermore, this, in conjunction with the :obj:`Registry`, allows us to
    temporarily disconnect all signals while performing an action, and then
    reconnect them afterwards:

    >>> with signals.disable():
    >>>     ...

    Parameters:
    ----------
    name: :obj:`str` (optional)
        A name used to reference the :obj:`Signal` instance when disabling
        signals in bulk.

        Default: id(instance)

    add_to_registry: :obj:`bool` (optional)
        Whether or not the :obj:`Signal` instance should be added to the
        signal :obj:`Registry`.  If false, the :obj:`Signal` will not be
        available to disable in bulk.

        Default: True
    """

    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop('name', id(self))

        self._add_to_registry = kwargs.pop('add_to_registry', True)
        if self._add_to_registry:
            registry.add(self)

        self._disabled = False
        self._connected_receiver_kwargs = {}

        super().__init__(*args, **kwargs)

    def connect(self, receiver, **kwargs):
        """
        Connects a given receiver to the signal.

        This method has to be entirely overridden from Django's default
        :obj:`dispatch.Signal.connect` method, because in order to temporarily
        disconnect all a signal from all of it's receivers, only to reconnect
        them afterwards, we need to maintain a mapping of how a receiver was
        connected to the signal to begin with (via the sender, weak and
        dispatch_uid arguments).

        Unfortunately, there is no way to implement this behavior without
        overriding the entire method.
        """
        # pylint: disable=import-outside-toplevel
        from django.conf import settings

        if settings.configured and settings.DEBUG \
                and (not callable(receiver)
                or not func_accepts_kwargs(receiver)):
            # Let Django raise the error.
            super().connect(receiver, **kwargs)
            return

        dispatch_uid = kwargs.get('dispatch_uid')
        if dispatch_uid:
            lookup_key = (dispatch_uid, _make_id(kwargs.get('sender')))
        else:
            lookup_key = (_make_id(receiver), _make_id(kwargs.get('sender')))

        if kwargs.get('weak', True):
            ref = weakref.ref
            receiver_object = receiver
            if hasattr(receiver, '__self__') and hasattr(receiver, '__func__'):
                ref = weakref.WeakMethod
                receiver_object = receiver.__self__
            receiver = ref(receiver)
            weakref.finalize(receiver_object, self._remove_receiver)

        with self.lock:
            self._clear_dead_receivers()
            if not any(r_key == lookup_key for r_key, _ in self.receivers):
                self.receivers.append((lookup_key, receiver))
                # This is the only block that does not exist in Django's
                # original connect method.
                self._connected_receiver_kwargs[lookup_key] = kwargs
            self.sender_receivers_cache.clear()

    @contextlib.contextmanager
    def with_disable(self, sender=None):
        disconnected = self.disconnect_all_receivers(sender=sender)
        try:
            yield self
        finally:
            self.reconnect_all_receivers(disconnected)

    def disable(self, *args, **kwargs):
        """
        A decorator or context manager that will disconnect this signal inside
        the decorated function or inside of the context, and then reconnect it
        after the context exits or the function completes.

        If the sender is provided, the signal will only be disabled for the
        provided sender.
        """
        sender = kwargs.pop('sender', None)
        if len(args) == 1 and hasattr(args[0], '__call__'):
            func = args[0]

            @functools.wraps(func)
            def decorated(*args, **kwargs):
                with self.with_disable(sender=sender):
                    return func(*args, **kwargs)
            return decorated
        return self.with_disable(sender=sender)

    def disconnect_all_receivers(self, sender=None):
        """
        Disconnects all receivers from the :obj:`Signal` instance and returns
        the disconnected receivers.  If the `sender` is provided, only the
        receivers that were connected with the provided `sender` are
        disconnected.
        """
        disconnected_receivers = []
        # The list of receivers `self.receivers` is mutated inside of the
        # disconnect method, so we must operate on a copied version otherwise
        # the indicies in the disconnect method will not align with the
        # appropriate signal to disconnect.
        receivers = self.receivers[:]
        for lookup_key, receiver in receivers:
            kwargs = self._connected_receiver_kwargs[lookup_key]

            if isinstance(receiver, weakref.ref):
                receiver = receiver()

            # If the receiver was not connected with the provided sender, do
            # not disconnect it.
            if sender is not None and kwargs['sender'] is not sender:
                continue

            disconnected = self.disconnect(
                receiver=receiver,
                sender=kwargs.get('sender'),
                dispatch_uid=kwargs.get('dispatch_uid')
            )
            if disconnected:
                del self._connected_receiver_kwargs[lookup_key]
                # We need to not only keep track of the receiver function itself
                # that was disconnected, but also the configuration arguments
                # that the receiver was originally connected with.
                disconnected_receivers.append((lookup_key, receiver, kwargs))
        return disconnected_receivers

    def reconnect_all_receivers(self, receivers):
        """
        Reconnects the previously disconnected receivers to the :obj:`Signal`
        instance, using the same configuration parameters that the receiver
        was originally connected with.
        """
        for _, receiver, kwargs in receivers:
            self.connect(receiver=receiver, **kwargs)


class disable(contextlib.ContextDecorator):
    """
    Context manager or function decorator that will temporarily disable
    :obj:`Signal`(s) in bulk inside of the context or inside of the function
    implementation.

    Parameters:
    ----------
    signals: :obj:`list` or :obj:`tuple` or :obj:`Signal` or None
        The specific signal, or iterable of signals, that should be disabled
        inside the context.  Signals can be referenced either by their
        registered name or by the :obj:`Signal` instance itself.  If no
        :obj:`Signal`(s) are provided, all :obj:`Signal`(s) will be disabled
        in the context.

        Default: None
    """

    def __init__(self, **kwargs):
        # Signals that should be disconnected in context, either identified by
        # their name in the registry or the :obj:`Signal` instance.  If not
        # provided, all signals in the registry will be disconnected in
        # context.
        self._signals = kwargs.pop('signals', None)
        # An array of (signal, [receivers]) for the receivers that are currently
        # disconnected for each signal.
        self._disconnected_receivers = []
        super().__init__()

    @property
    def signals(self):
        if not self._signals:
            return registry.signals
        signal_instances = []
        for sig in ensure_iterable(self._signals):
            if isinstance(sig, str):
                signal_instances.append(registry.get_signal(sig))
            else:
                signal_instances.append(sig)
        return signal_instances

    def __enter__(self):
        for signal in self.signals:
            disconnected = signal.disconnect_all_receivers()
            if disconnected:
                self._disconnected_receivers.append((signal, disconnected))
        return self

    def __exit__(self, *exc):
        for signal, receivers in self._disconnected_receivers:
            signal.reconnect_all_receivers(receivers)
        self._disconnected_receivers = []
        return False
