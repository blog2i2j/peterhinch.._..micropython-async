# broker_test.py Test various types of subscriber

# import primitives.tests.broker_test

import asyncio
from primitives import broker, Queue, RingbufQueue, RegExp

# Periodically publish messages to two topics
async def test(t):
    for x in range(t):
        await asyncio.sleep(1)
        broker.publish("foo_topic", f"dogs {x}")
        broker.publish("bar_topic", f"rats {x}")


# Suscribe via coroutine
async def subs(topic, message):
    await asyncio.sleep_ms(100)
    print("coroutine", topic, message)


# Subscribe via function
def func(topic, message):
    print("function", topic, message)


# Subscribe via Event

event = asyncio.Event()


async def event_test():
    while True:
        await event.wait()
        event.clear()
        print("Event triggered")


class TestClass:
    async def fetch_data(self, topic, message, arg1, arg2):
        await asyncio.sleep_ms(100)
        print("bound coro", topic, message, arg1, arg2)

    def get_data(self, topic, message):
        print("bound method", topic, message)


async def print_queue(q):
    while True:
        topic, message = await asyncio.wait_for(q.get(), 2)
        print(topic, message)


async def print_ringbuf_q(q):
    while True:
        topic, message, args = await asyncio.wait_for(q.get(), 2)
        print(topic, message, args)


async def main():
    Broker.Verbose = False  # Suppress q full messages
    tc = TestClass()
    q = Queue(10)
    rq = RingbufQueue(10)
    print("Subscribing Event, coroutine, Queue, RingbufQueue and bound coroutine.")
    broker.subscribe("foo_topic", tc.fetch_data, 1, 42)  # Bound coroutine
    broker.subscribe("bar_topic", subs)  # Coroutine
    broker.subscribe("bar_topic", event)
    broker.subscribe("foo_topic", q)
    broker.subscribe("bar_topic", rq, "args", "added")

    asyncio.create_task(test(30))  # Publish to topics for 30s
    asyncio.create_task(event_test())
    await asyncio.sleep(5)
    print()
    print("Unsubscribing coroutine")
    broker.unsubscribe("bar_topic", subs)
    await asyncio.sleep(5)
    print()
    print("Unsubscribing Event")
    broker.unsubscribe("bar_topic", event)
    print()
    print("Subscribing function")
    broker.subscribe("bar_topic", func)
    await asyncio.sleep(5)
    print()
    print("Unsubscribing function")
    broker.unsubscribe("bar_topic", func)
    print()
    print("Unsubscribing bound coroutine")
    broker.unsubscribe("foo_topic", tc.fetch_data, 1, 42)  # Async method
    print()
    print("Subscribing method")
    broker.subscribe("foo_topic", tc.get_data)  # Sync method
    await asyncio.sleep(5)
    print()
    print("Unsubscribing method")
    broker.unsubscribe("foo_topic", tc.get_data)  # Async method
    print("Retrieving foo_topic messages from Queue")
    print("Retrieving bar_topic messages from RingbufQueue")
    await asyncio.gather(print_queue(q), print_ringbuf_q(rq), return_exceptions=True)
    # Queues are now empty
    print()
    print("*** Unsubscribing queues ***")
    broker.unsubscribe("foo_topic", q)
    broker.unsubscribe("bar_topic", rq, "args", "added")
    print()

    print("*** Testing error reports and exception ***")
    print()
    Broker.Verbose = True
    print("*** Produce warning messages on invalid unsubscribe ***")
    broker.unsubscribe("rats", "more rats")  # Invalid topic
    broker.unsubscribe("foo_topic", "rats")  # Invalid agent
    print("*** Check exception on invalid subscribe ***")
    try:
        broker.subscribe("foo_topic", "rubbish_agent")
        print("Test FAIL")
    except ValueError:
        print("Test PASS")
    print()
    print("*** Test wildcard subscribe ***")
    broker.subscribe(RegExp(".*_topic"), func)
    broker.publish("FAIL", func)  # No match
    asyncio.create_task(test(5))
    await asyncio.sleep(10)


asyncio.run(main())
