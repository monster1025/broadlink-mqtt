import broadlink
import paho.mqtt.client as mqtt
import os
import time
import threading
from plugstate import PlugState

MQTT_SERVER = os.getenv('MQTT_SERVER', "")
MQTT_PORT = os.getenv('MQTT_PORT', 1883)
MQTT_USER = os.getenv('MQTT_USER', "")
MQTT_PASS = os.getenv('MQTT_PASS', "")
QUERY_TIME = os.getenv('QUERY_TIME', 5)
PREFIX = os.getenv('PREFIX', 'home')

ips = dict({
	'192.168.1.49':{'name':'rm2', 'mac':'B4430DCC2255', 'type':'remote'},
	# '192.168.1.62':{'name':'main-humidifier', 'mac':'B4430DCB6AC1', 'type':'plug'},
	 '192.168.1.63':{'name':'kitchen-mini-light', 'mac':'B4430DCB6C07', 'type':'plug'},
	# '192.168.1.64':{'name':'balcony-heater', 'mac':'B4430DCB7276', 'type':'plug'}, 
	# '192.168.1.65':{'name':'kitchen-kettle', 'mac':'B4430DCB5639', 'type':'plug'},
	# '192.168.1.66':{'name':'balcony-lights', 'mac':'B4430DCB6F18', 'type':'plug'},
})

plugs=[]
processNow = False
 
PATH_FMT = PREFIX + "/{model}/{sid}/{prop}" # short_id or sid ?

def prepare_mqtt():
	print("Connecting to MQTT server", MQTT_SERVER, ":", MQTT_PORT, "with username", MQTT_USER,":",MQTT_PASS)
	client = mqtt.Client()
	if (MQTT_USER != "" and MQTT_PASS != ""):
		client.username_pw_set(MQTT_USER, MQTT_PASS)
	client.connect(MQTT_SERVER, MQTT_PORT, 60)
 
	return client
 
def push_data(client, model, sid, data):
	for key, value in data.items():
		path = PATH_FMT.format(model=model,
							   sid=sid,
							   prop=key)
		client.publish(path, payload=value, qos=0, retain=True)

def reverse_hex(s):
	return "".join(map(str.__add__, s[-2::-2] ,s[-1::-2]))

def init_plugs():
	plugs=[]
	for ip in ips:
		for i in range(1,3):
			try:
				props = ips[ip]
				name = props['name']
				mac = props['mac']
				typeName = props['type']
				typeId = 0x2720 #SP2 by default
				if (typeName == "remote"):
					typeId = 0x2712
				macBytes = bytes.fromhex(reverse_hex(mac))
				broadObj = broadlink.gendevice(typeId, (ip, 80) , macBytes)
				broadObj.auth()
				plug = PlugState(ip, typeName, name, broadObj)
				plug.update_properties()
				plugs.append(plug)
				break
			except Exception as e:
				print('['+str(i) + '] Connection to ', str(ip) , ' error:', str(e))
	return plugs

def refresh_plug_states(data_callback):
	global plugs
	for plug in plugs:
		try:
			hashold = plug.hash()
			plug.update_properties(force=True)
			hashnew = plug.hash()
			# print(str(plug.name), hashold, hashnew)

			if (hashold != hashnew):
				print("!!!! ", plug.name, ":", hashold, "->", hashnew)
				data = {'status':plug.status}
				if (plug.type == "remote"):
					data = {'code':plug.learned_code}
				if data_callback is not None:
					data_callback(plug.type, plug.name, data)
		except Exception as e:
			print('Connection to ', str(plug.name) , ' error:', str(e))

def on_mqtt_message(client, userdata, msg):
	global processNow
	print(msg.topic+" "+str(msg.payload))
	parts = msg.topic.split("/")
	if (len(parts) != 5):
		return
	type = parts[1]
	if (type != "plug" and type != "remote"):
		return
	name = parts[2] #name part
	param = parts[3] #param part
	value = (msg.payload).decode('utf-8')

	for plug in plugs:
		if (plug.name != name):
			continue
		plug.process_command(param, value)
		processNow=True

def on_connect(client, userdata, rc, kwargs):
	client.subscribe(PREFIX + "/plug/+/+/set")
	client.subscribe(PREFIX + "/remote/+/+/learn")
	client.subscribe(PREFIX + "/remote/+/+/set")

def refresh_loop(client):
	global processNow
	cb = lambda m, s, d: push_data(client, m, s, d)
	while True:
		refresh_plug_states(cb)
		for x in range(1,10):
			if (processNow):
				processNow=False
				break
			time.sleep(QUERY_TIME/10)

if __name__ == "__main__":
	client = prepare_mqtt()
	plugs = init_plugs()
	print("Founded devices:")
	for plug in plugs:
		print("Device", plug.name, "on ip", plug.ip, "with type", plug.type)

	client.on_message = on_mqtt_message
	client.on_connect = on_connect

	#start thread for lamp refresh loop
	t1 = threading.Thread(target=refresh_loop, args=[client])
	t1.start()

    # and process mqtt messages in this thread
	client.loop_forever()

