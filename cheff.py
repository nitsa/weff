# Cheff v0.2 for Python 3

# pip install pycryptodome
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto import Random

import _thread
import socket
import sys
import time

BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * (chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)).encode('utf-8')
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

# Global variable
waiter_external_port = 0

# Generate AES key from password
def get_private_key(password):
    salt = b'oDfjr%8Soe9@39!X'
	# pass, salt, dkLen, iterations
    kdf = PBKDF2(password, salt, 64, 1000) 
    key = kdf[:32]
    return key

# Encrypt communications
def aes_encrypt(plaintext, key):
	iv = Random.new().read(AES.block_size)
	cipher = AES.new(key, AES.MODE_CBC, iv)
	data = pad(plaintext)
	ciphertext = cipher.encrypt(data)
	ciphertext = iv + ciphertext
	return ciphertext
	
# Decrypt communications
def aes_decrypt(ciphertext, key):
	iv = ciphertext[:AES.block_size]
	ciphertext = ciphertext[AES.block_size:]
	cipher = AES.new(key, AES.MODE_CBC, iv)
	plaintext = cipher.decrypt(ciphertext)
	plaintext = unpad(plaintext)
	return plaintext

# Keep alive the connection by sending an empty message.
def keep_alive(msg_keepalive, sock, dst_ip, dst_port, key):
	while True:
		encryptedmsg = aes_encrypt(msg_keepalive.encode('utf-8'), key)
		sock.sendto(encryptedmsg, (dst_ip, dst_port))
		time.sleep(5)

# Receive messages from waiter during and after connection establishment.
def msg_receive(waiter_id, sock, dst_ip, dst_port, key):
	while True:
		try:
			global waiter_external_port
			# connection has not yet been established
			if (waiter_external_port == 0):
				data = sock.recv(1024)
				data = aes_decrypt(data, key).decode('utf-8')
				if (len(data) > 8):
					if (data[:8] == waiter_id):
						print ('[*] connection established')
						print(chr(0x0a))
						waiter_external_port = int(str(data[8:len(data)]))
			# connection has been established, process messages recevied from waiter
			else:
				data = sock.recv(1024)
				data = aes_decrypt(data, key).decode('utf-8')
				if (len(data) > 8):
					if (data[:8] == waiter_id):
						print (chr(0x0a) + 'Other> ' + str(data[8:len(data)]) + chr(0x0a) + 'Me   > ', end ="")

		# In case receive times out.
		except socket.timeout:
			pass

def main():

	if (len(sys.argv) != 4):
		print ('Usage : cheff.py 0.0.0.0 192.168.1.2 20000')
		sys.exit()

	# Configuration
	dst_ip   = str(sys.argv[2])
	dst_port = 0
	src_ip   = str(sys.argv[1])
	src_port = 1235
	delay    = int(sys.argv[3])

	print (chr(0x0a))
	print ('[*] dst ip ' + dst_ip)
	print ('[*] dst port ' + str(dst_port))
	print ('[*] src ip ' + src_ip)
	print ('[*] src port ' + str(src_port))
	print ('[*] delay ' + str(delay))
	#print (chr(0x0a))

	# Process messages from those peers only.
	waiter_id = 'waiter01'
	cheff_id  = 'cheff001'

	# Password for generating AES key
	password = b'H3ll0nEarth:)DieCvh#'

	# Generate AES key
	aes_key = get_private_key(password)

	print ('[*] starting in 5 seconds')
	print ('[*] make sure the other side is running first')
	time.sleep(5)

	# Receiver thread UDP protocol.
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((src_ip, src_port))
	_thread.start_new_thread(msg_receive, (waiter_id, sock, dst_ip, dst_port, aes_key, ))

	print ('[*] establishing connection with the other side')

	# Brute force waiter to establish connection
	while(dst_port < 65535):
	
		dst_port = dst_port + 1
		msg_waiter_external_port = cheff_id + str(dst_port)
		encryptedmsg = aes_encrypt(msg_waiter_external_port.encode('utf-8'), aes_key)
		sock.sendto(encryptedmsg, (dst_ip, dst_port))
		a = 0			
		while(a < delay):
			a = a + 1
		
		if (waiter_external_port != 0):
			# terminate brute force if success.
			break

	# Start thread for keeping connection with waiter alive.		
	msg_keepalive = cheff_id + ''
	_thread.start_new_thread(keep_alive, (msg_keepalive, sock, dst_ip, waiter_external_port, aes_key, ))

	# Wait input from command prompt and send to waiter.
	while True:
		msg = input('Me   > ')
		msg = cheff_id + msg
		encryptedmsg = aes_encrypt(msg.encode('utf-8'), aes_key)
		sock.sendto(encryptedmsg, (dst_ip, waiter_external_port))

if __name__ == "__main__":
    main()
        
        
        
