# Waiter v0.2 for Python 3

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

# Receive messages from cheff after establishing connection.
def msg_receive(cheff_id, sock, dst_ip, dst_port, key):
	while True:
		try:
			data = sock.recv(1024)
			data = aes_decrypt(data, key).decode('utf-8')
			# Do not process empty messages from cheff keep_alive routine.
			if (len(data) > 8):
				if (data[:8] == cheff_id):
					print (chr(0x0a) + 'Other> ' + str(data[8:len(data)]) + chr(0x0a) + 'Me   > ', end ="")

		# In case receive times out.
		except socket.timeout:
			pass

def main():

	if (len(sys.argv) != 3):
		print ('Usage : waiter.py 0.0.0.0 192.168.1.2')
		sys.exit()

	# Configuration
	dst_ip   = str(sys.argv[2])
	dst_port = 1235
	src_ip   = str(sys.argv[1])
	src_port = 1235

	print (chr(0x0a))
	print ('[*] dst ip ' + dst_ip)
	print ('[*] dst port ' + str(dst_port))
	print ('[*] src ip ' + src_ip)
	print ('[*] src port ' + str(src_port))


	# Process messages from those peers only.
	waiter_id = 'waiter01'
	cheff_id  = 'cheff001'

	# Password for generating AES key
	password = b'H3ll0nEarth:)DieCvh#'

	# Generate AES key
	aes_key = get_private_key(password)

	# Bind to source ip and port using UDP protocol.
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((src_ip, src_port))

	# Start thread for keeping connection with cheff alive.
	msg_keepalive = waiter_id + ''
	_thread.start_new_thread(keep_alive, (msg_keepalive, sock, dst_ip, dst_port, aes_key, ))

	print ('[*] waiting for other side to establish connection')

	# Process firt message received from cheff.
	while True:
		try:
			data = sock.recv(1024)
			data = aes_decrypt(data, aes_key).decode('utf-8')
			if (len(data) > 8):
				if (data[:8] == cheff_id):
					print ('[*] connection established')
					print(chr(0x0a))
					# Extract my (waiter) external port which cheff is sending.
					# Send it back to cheff so that there is no need to brute force any more.
					my_external_port = data[8:len(data)]
					msg_sendmyport = waiter_id + my_external_port
					encryptedmsg = aes_encrypt(msg_sendmyport.encode('utf-8'), aes_key)
					sock.sendto(encryptedmsg, (dst_ip, dst_port))
					# terminate loop.
					break
		# In case receive times out.
		except socket.timeout:
			pass

	# Start thread for processing received messages from cheff.
	_thread.start_new_thread(msg_receive, (cheff_id, sock, dst_ip, dst_port, aes_key, ))

	# Wait input from command prompt and send to cheff.
	while True:
		msg = input('Me   > ')
		msg = waiter_id + msg
		encryptedmsg = aes_encrypt(msg.encode('utf-8'), aes_key)
		sock.sendto(encryptedmsg, (dst_ip, dst_port))

if __name__ == "__main__":
    main()