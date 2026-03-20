# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 11:16:12 2026

@author: mater
"""

import websocket
ws = websocket.WebSocket()

#%% Connect to device IP:port

ws.connect("ws://192.168.5.111:81")
print(ws.recv())

#%% Request MAC address

ws.send('@')
print(ws.recv())

#%% Request current lid position

ws.send('?')
print(ws.recv())

#%% Open lid on centrifuge 1 (Home position)

ws.send('H1')
#Echo
print(ws.recv())
#Receive "Homed 1" when complete
print(ws.recv())

#%% Open lid on centrifuge 2 (Home position)

ws.send('H2')
#Echo
print(ws.recv())
#Receive "Homed 2" when complete
print(ws.recv())

#%% Close lid on centrifuge 1

ws.send('#1050')
#Echo
print(ws.recv())
#Receive "Ok" when complete
print(ws.recv())

#%% Close lid on centrifuge 2

ws.send('#2050')
#Echo
print(ws.recv())
#Receive "Ok" when complete
print(ws.recv())

#%% Spin centrifuge 1

ws.send('~11')
#Echo
print(ws.recv())

#%% Stop centrifuge 1

ws.send('~10')
#Echo
print(ws.recv())

#%% Spin centrifuge 2

ws.send('~21')
#Echo
print(ws.recv())

#%% Stop centrifuge 2

ws.send('~20')
#Echo
print(ws.recv())