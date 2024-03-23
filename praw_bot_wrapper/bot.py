import praw
import prawcore
import time
import logging
from datetime import datetime, timezone
from praw.models.util import BoundedSet

log = logging.getLogger(__package__)


def handle_praw_errors():
    def __dec__(func):
        def __call__(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (
                praw.exceptions.PRAWException,
                prawcore.exceptions.PrawcoreException,
            ) as ex:
                log.exception(ex)
                return None

        return __call__

    return __dec__


_streams = {}
_recovery_handlers = []


def outage_recovery_handler(outage_threshold):
    def __call__(handler):
        _outage_threshold = outage_threshold
        _recovery_handlers.append((handler,outage_threshold))
        return handler
    return __call__


def _notify_outage_recovery(start_time, error_count):
    for (handler, outage_threshold) in _recovery_handlers:
        if error_count >= outage_threshold:
            handler(start_time)


def stream_handler(generator_func):
    def __call__(handler):
        # handler = list(args)[0]

        if generator_func not in _streams:
            _streams[generator_func] = (
                generator_func(pause_after=-1),
                [],
                BoundedSet(301),
            )
        _, handlers, _ = _streams[generator_func]
        handlers.append(handler)
        return handler

    return __call__


def _reset_streams():
    for generator_func in _streams:
        _, handlers, seen_attributes = _streams[generator_func]
        _streams[generator_func] = (
            generator_func(pause_after=-1),
            handlers,
            seen_attributes,
        )


def run():
    error_count = 0
    error_started = None

    while True:
        try:
            for generator_func, (
                generator,
                handlers,
                seen_attributes,
            ) in _streams.items():
                for item in generator:
                    if item is None:
                        break
                    attribute = str(item)
                    if attribute in seen_attributes:
                        continue
                    for handler in handlers:
                        handler(item)
                    seen_attributes.add(attribute)

            _notify_outage_recovery(error_started, error_count)
            error_count = 0  # no exceptions, reset error count
            error_started = None
        except (
            praw.exceptions.PRAWException,
            prawcore.exceptions.PrawcoreException,
        ) as praw_error:
            log.debug(praw_error)
            # when the reddit apis start misbehaving, we don't need to just crash the app
            error_count += 1
            if error_count == 1:
                error_started = datetime.now(timezone.utc)
            _reset_streams()  # the stream has to be reset when we're hitting exceptions because the listinggenerator has
            # internal exceptions that will cause it to stop trying to yield without throwing any issues. In testing have
            # found this happens after two exceptions on the two streams, so reset every 2 errors with the stream

        log.debug(f"Sleeping for {(1 * len(_streams)) + (60 * min(error_count, 10))}")
        time.sleep((1 * len(_streams)) + (60 * min(error_count, 10)))
        # sleep for at most 1 hour if the errors keep repeating
        # always sleep for at least 1 seconds between loops
