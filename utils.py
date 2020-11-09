import asyncio

# https://phoolish-philomath.com/asynchronous-task-scheduling-in-python.html

async def run_periodically(wait_time, coro, *args):
    """
    Helper for schedule_task_periodically.
    Wraps a coroutine in another coroutine that will run the
    given coroutine indefinitely
    :param wait_time: seconds to wait between iterations of coro
    :param coro: the coroutine that will be run
    :param args: any args that need to be provided to coro
    """
    while True:
        await coro(*args)
        await asyncio.sleep(wait_time)


def schedule_task_periodically(wait_time, coro, event_loop, *args):
    """
    Schedule a coroutine to run periodically as an asyncio.Task
    :param wait_time: interval (in seconds)
    :param coro: the coroutine that will be run
    :param event_loop: the event loop used
    :param args: any args needed to be provided to coro
    :return: an asyncio Task that has been scheduled to run
    """
    return event_loop.create_task(run_periodically(wait_time, coro, *args))


async def cancel_scheduled_task(task):
    """
    Gracefully cancels a task
    :type task: asyncio.Task
    """
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass