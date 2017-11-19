#!/usr/bin/env python3
import asyncio
import logging
import sys
import websockets
from websockets.exceptions import ConnectionClosed
import json

from pytradfri import Gateway
from pytradfri.api.aiocoap_api import APIFactory

root = logging.getLogger()
root.setLevel(logging.INFO)

try:
    # pylint: disable=ungrouped-imports
    from asyncio import ensure_future
except ImportError:
    # Python 3.4.3 and earlier has this as async
    # pylint: disable=unused-import
    from asyncio import async
    ensure_future = async

device_list = {
    'devices': [],
    'groups': [],
}

def find_or_create_item_in_list(needle, haystack):
    found_item = None
    for item in haystack:
        if item['id'] == needle.id:
            found_item = item
            break

    if found_item == None:
        found_item = {}
        haystack.append(found_item)

    found_item['id'] = needle.id

    return found_item

def update_device(device, updated_device):

    device['name'] = updated_device.name

    if updated_device.application_type == 2:
        device['type'] = 'light'
        device['status'] = 1 if updated_device.light_control.lights[0].state else 0
        device['brightness'] = updated_device.light_control.lights[0].dimmer

    elif updated_device.application_type == 0:
        device['type'] = 'remote_control'
        device['battery'] = updated_device.device_info.battery_level

    elif updated_device.application_type == 4:
        device['type'] = 'motion_sensor'
        device['battery'] = updated_device.device_info.battery_level

def observe_device_callback(updated_device):
    print("device %s changed" % updated_device.name)

    device = find_or_create_item_in_list(updated_device, device_list['devices'])
    update_device(device, updated_device)

    for websocket in connectedWebSockets:
        asyncio.ensure_future(ws_send_update(websocket, json.dumps( { 'devices': [ device ] } )))

def update_group(group, updated_group):
    group['name'] = updated_group.name
    group['status'] = 1 if updated_group.state else 0
    group['devices'] = updated_group.member_ids
    group['scenes'] = None #pytradfri doesn't seem to support querying scene details yet

def observe_group_callback(updated_group):
    print("group %s changed" % updated_group.name)

    group = find_or_create_item_in_list(updated_group, device_list['groups'])
    update_group(group, updated_group)

    for websocket in connectedWebSockets:
        asyncio.ensure_future(ws_send_update(websocket, json.dumps( { 'groups': [ group ] } )))

def observe_err_callback(err):
    print('observe error:', err)

@asyncio.coroutine
def run_pytradfri():
    api_factory = APIFactory('192.168.1.123', 'myUserName',
                             'password123456789')
    api = api_factory.request

    gateway = Gateway()

    devices_command = gateway.get_devices()
    devices_commands = yield from api(devices_command)
    devices = yield from api(devices_commands)

    groups_command = gateway.get_groups()
    groups_commands = yield from api(groups_command)
    groups = yield from api(groups_commands)

    for device in devices:
        observe_command = device.observe(observe_device_callback, observe_err_callback, duration=0)
        # Start observation as a second task on the loop.
        ensure_future(api(observe_command))
        yield from asyncio.sleep(0)

    for group in groups:
        observe_command = group.observe(observe_group_callback, observe_err_callback, duration=0)
        # Start observation as a second task on the loop.
        ensure_future(api(observe_command))
        yield from asyncio.sleep(0)

    # Sleep in an infinite loop to keep this running but also allow other tasks to execute
    while True:
        yield from asyncio.sleep(1)

connectedWebSockets = set()

@asyncio.coroutine
def ws_send_update(websocket, data):
    try:
        yield from websocket.send(data)
    except ConnectionClosed:
        print("disconnected client %s:%i" % (websocket.remote_address[0], websocket.remote_address[1]))
        connectedWebSockets.remove(websocket)

@asyncio.coroutine
def consumer_handler(websocket):
    while True:
        # Not much to do here, yet. In future, process tasks received from the client
        # Just echo the message the client sent to the console
        message = yield from websocket.recv()
        print(message)
        #yield from consumer(message)

@asyncio.coroutine
def producer_handler(websocket):
    yield from websocket.send(json.dumps(device_list))
    while True:
        # Not much to do here yet, either.
        #message = yield from producer()
        #yield from websocket.send(message)
        yield from asyncio.sleep(10)

@asyncio.coroutine
def handler(websocket, path):
    global connectedWebSockets

    # Register.
    connectedWebSockets.add(websocket)
    print("connected client %s:%i" % (websocket.remote_address[0], websocket.remote_address[1]))

    consumer_task = asyncio.ensure_future(consumer_handler(websocket))
    producer_task = asyncio.ensure_future(producer_handler(websocket))
    # Huh, if I just waited for the tasks to end it'd block the tasks doing the communication to the gateway
    #done, pending = yield from asyncio.wait(
    #    [consumer_task, producer_task],
    #    return_when=asyncio.FIRST_COMPLETED,
    #)

    #for task in pending:
    #    task.cancel()

    #So for now, just sleep in an infinite loop to keep running but allow other tasks to execute
    while True:#consumer_task.running() or producer_task.running():
        yield from asyncio.sleep(1)

    #if consumer_task.running():
    #    consumer_task.cancel()

    #if producer_task.running():
    #    producer_task.cancel()

    #connectedWebSockets.remove(websocket)

@asyncio.coroutine
def run():
    start_server = websockets.serve(handler, '0.0.0.0', 5678)

    #asyncio.get_event_loop().run_until_complete(start_server)
    pytradfri_task = asyncio.ensure_future(run_pytradfri())
    websocket_task = asyncio.ensure_future(start_server)
    # Huh, if I just waited for the tasks to end it'd block the tasks doing the communication to the gateway
    #done, pending = yield from asyncio.wait(
    #    [websocket_task, pytradfri_task],
    #    return_when=asyncio.FIRST_COMPLETED,
    #)

    #for task in pending:
    #    task.cancel()

    #So for now, just sleep in an infinite loop to keep running but allow other tasks to execute
    while True:#pytradfri_task.running() or websocket_task.running():
        yield from asyncio.sleep(1)

    #if pytradfri_task.running():
    #    pytradfri_task.cancel()

    #if websocket_task.running():
    #    websocket_task.cancel()

asyncio.get_event_loop().run_until_complete(run())
asyncio.get_event_loop().run_forever()
