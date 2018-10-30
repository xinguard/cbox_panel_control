#!/usr/bin/env python2.7
import uuid
from bluetooth import *
import RPi.GPIO as GPIO

import time
import os
import subprocess
#import subprocess32 as subprocess
from threading import Thread
import socket
import sys
import syslog

server_address = '/var/run/uds_led'

def send_command(message):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(server_address)
    except socket.error, msg:
        print >>sys.stderr, msg
        return

    try:

        # Send data
        print >>sys.stderr, 'sending "%s"' % message
        sock.sendall(message)

    finally:
        print >>sys.stderr, 'closing socket'
        sock.close()

def getHalfMAC(interface='wlan0'):
  # Return the MAC address of the specified interface
  try:
    str = open('/sys/class/net/%s/address' %interface).read()
    str = (str.split(':')[3]+str.split(':')[4]+str.split(':')[5]).upper().strip('\n')
  except:
    str = "000000"
  return str

if not os.path.exists('/etc/machine-info'):
    message='echo "PRETTY_HOSTNAME=PORTEX-'+getHalfMAC()+'" > /etc/machine-info'
    #print message
    subprocess.call([message], shell=True)
    print >>sys.stderr, 'sending "%s"' % message
os.system('service bluetooth start')
time.sleep(2)
subprocess.call(['/opt/mcs/cbox_panel_control/bin/bluetooth_adv'], shell=True)
#print >>sys.stderr, 'sending "%s"' % message
message = ''

server_socket=BluetoothSocket(RFCOMM)
server_socket.bind(("", PORT_ANY))
server_socket.listen(1)
port = server_socket.getsockname()[1]
service_id = str(uuid.uuid4())
 
advertise_service(server_socket, "LEDServer",
                  service_id = service_id,
                  service_classes = [service_id, SERIAL_PORT_CLASS],
                  profiles = [SERIAL_PORT_PROFILE])
 
try:
    print('press Ctrl-C to exit')
    while True:
        print('wait for RFCOMM channel {} connection'.format(port))
        client_socket, client_info = server_socket.accept()
        print('accecpit from {} connection'.format(client_info))
        try:
            while True:
                data = client_socket.recv(1024).decode()
                if len(data) == 0:
                    break
                if data[0:4] == 'info':
                    #GPIO.output(LED_PIN, GPIO.HIGH) #-> send_command(message)
                    print('info')
                    # Send data
                    message = subprocess.check_output(['/opt/mcs/tnlctl/bin/helper/get-serial.sh'])
                    print >>sys.stderr, 'sending "%s"' % message
                    client_socket.sendall(message)
                    message =''
		elif data[0:4] == 'acti':
                    print('activate')
                    # Send data
                    message = subprocess.check_output(['/opt/mcs/tnlctl/bin/api/reg/v1/activate.sh',data.split(':')[1],data.split(':')[2],data.split(':')[3],data.split(':')[4],data.split(':')[5]])
                    print >>sys.stderr, 'sending "%s"' % message
                    client_socket.sendall(message)
                    message =''
                elif data[0:4] == 'wifi':
                    print data.split(':')
                    # Send data
                    message='echo "ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\ncountry=TW\nnetwork={\nssid=\\"'+data.split(':')[1]+'\\"\npsk=\\"'+data.split(':')[2]+'\\"\n}" > /etc/wpa_supplicant/wpa_supplicant.conf'
                    subprocess.call([message], shell=True)
                    print >>sys.stderr, 'sending "%s"' % message
                    #client_socket.sendall(message)
                    message =''
                    message = subprocess.check_output(['reboot'])

                    #message = subprocess.check_output(['systemctl daemon-reload'])
                    #print >>sys.stderr, 'sending "%s"' % message
                    #client_socket.sendall(message)
                    #message =''
                    #message = subprocess.check_output(['/etc/init.d/dhcpcd', 'restart'])
                    #print >>sys.stderr, 'sending "%s"' % message
                    #client_socket.sendall(message)
                    #message =''

                elif data[0:4] == 'clou':
                    print('cloud connect')
                    #GPIO.output(LED_PIN, GPIO.LOW) #-> send_command(message)
                    try:
                        subprocess.call(['/opt/mcs/tnlctl/bin/tnlctl.sh start'], shell=True)
                    except Exception as e:
                        print("Command failed: {}".format(e))
                    print >>sys.stderr, 'sending "%s"' % message
                    client_socket.sendall(message)



                elif data[0:4] == 'upgr':
                    print('upgrade')
                    #GPIO.output(LED_PIN, GPIO.LOW) #-> send_command(message)
                    try:
                        subprocess.check_output(['apt-get', 'update'])
                    except Exception as e:
                        print("Command failed: {}".format(e))
                    try:
                        message = subprocess.check_output(['apt-get', 'install', 'tnlctl', 'cbox-panel-control'])
                    except Exception as e:
                        print("Command failed: {}".format(e))
                    print >>sys.stderr, 'sending "%s"' % message
                    client_socket.sendall(message)
                else:
                    print('known command: {}'.format(data))
        except IOError:
            pass
        client_socket.close()
        print('disconnect')
except KeyboardInterrupt:
    print('program exit')
finally:
    if 'client_socket' in vars():
        client_socket.close()
    server_socket.close()
    GPIO.cleanup()
    print('disconnect')
