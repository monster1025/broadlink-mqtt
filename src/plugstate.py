import broadlink
import os
import time
import threading
import binascii

class PlugState:
	status = "off"
	ip = ""
	name = ""
	type = ""
	learned_code = ""

	learn_temp = ""
	broadlink = None # yeelight object


	def __init__(self, ip, typeName, name, broadlinkObj):
		self.broadlink = broadlinkObj
		self.name = name
		self.type = typeName
		self.ip = ip

	def update_properties(self, force = False):
		#need to copy nearned code
		if (self.type == "remote" and force):
			self.learned_code = self.learn_temp
			self.learn_temp = ""

		if (self.type == "plug" and force):
			state = self.broadlink.check_power()
			if (state):
				self.status = "on"
			else:
				self.status = "off"

	def hash(self):
		return str(self.status) + ":" + str(self.learned_code)
	
	def is_int(self, x):
		try:
			tmp = int(x)
			return True
		except Exception as e:
			return False

	def process_command(self, param, value):
		try:
			if (param == 'status'):
				if (value == "on"):
					print("Turning on plug", self.name)
					self.broadlink.set_power(True)
				if (value == "off"):
					print("Turning off plug", self.name)
					self.broadlink.set_power(False)
			if (param == 'learn' and self.type == 'remote'):
				self.broadlink.enter_learning()
				time.sleep(5)
				ir_packet = self.broadlink.check_data()
				#sample data
				# ir_packet = bytearray([0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x08 ,0x00 ,0x00 ,0x00 ,0xe0 ,0x07 ,0x25 ,0x32 ,0x07 ,0x01 ,0x03 ,0x0a ,0x00 ,0x00 ,0x00 ,0x00 ,0xc0 ,0xa8 ,0x00 ,0x81 ,0x53 ,0xf1 ,0x00 ,0x00 ,0x3d ,0xc3 ,0x00 ,0x00 ,0x00 ,0x00 ,0x06 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00])
				if (ir_packet == None):
					print("No ir packets recieved")
					return
				self.learn_temp = binascii.hexlify(ir_packet)
				print("Learned code:", ir_packet)
			if (param == 'code' and self.type == 'remote'):
				if (value == None or value == ""):
					print("No ir packets in value")
					return
				print("Sending IR packet:", value)
				#sample data
				# ir_packet = bytearray([0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x08 ,0x00 ,0x00 ,0x00 ,0xe0 ,0x07 ,0x25 ,0x32 ,0x07 ,0x01 ,0x03 ,0x0a ,0x00 ,0x00 ,0x00 ,0x00 ,0xc0 ,0xa8 ,0x00 ,0x81 ,0x53 ,0xf1 ,0x00 ,0x00 ,0x3d ,0xc3 ,0x00 ,0x00 ,0x00 ,0x00 ,0x06 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00])
				ir_packet = bytes.fromhex(value)
				self.broadlink.send_data(ir_packet)

		except Exception as e:
			print ('Error while set value of plug', self.name , ' error:', e)
