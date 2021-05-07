#!/usr/bin/python3

import RPi.GPIO as GPIO
import sys
import time
import smtplib, ssl
import signal
import http.client
from config import *

def SetWerkstattStatusWebseite(status):
	if status == "open":
		status = "1"
	elif status == "closed":
		status = "0"
	else:
		print("Falscher Parameter (\"open \"|\"closed\"): {}".format(str(status)), file=sys.stderr)
		return(False)

	RequestString = "/wstatus.php?secret={}&s={}".format(SpaceState.getSecret() ,str(status))

	try:
		conn = http.client.HTTPSConnection(SpaceState.getServer())
		conn.request("GET", RequestString)
		r1 = conn.getresponse()
	except Exception as e:
		print(e, file=sys.stderr)
		return(False)

	if r1.status==200:
		return (True)
	print("Der HTTP-Statuscode war: {}".format(str(r1.status)), file=sys.stderr)
	return (False)

class GracefulKiller: # Hier wird auf Kill-Signale des Betriebssystems reagiert
	kill_now = False
	def __init__(self):
		signal.signal(signal.SIGINT, self.exit_gracefully)
		signal.signal(signal.SIGTERM, self.exit_gracefully)
		signal.signal(signal.SIGQUIT, self.exit_gracefully)
	def exit_gracefully(self,signum, frame):
		SendMail("Raspberrypi wurde heruntergefahren oder ein Fehler ist aufgetreten","ab jetzt folgen keine Statusmeldungen mehr!\nDie Alarmanlage laeuft moeglicherweise noch...\nBeendet durch Signal: " + str(signum))
		sys.exit(0)


def GetCurrentState():
	state = "unknown"
	try:
		GPIO.setmode(GPIO.BCM)
		#GPIO.setup(26, GPIO.IN, pull_up_down = GPIO.PUD_DOWN) # ReservePin, aktuell nicht verwendet
		GPIO.setup(19, GPIO.IN, pull_up_down = GPIO.PUD_DOWN) # High, wenn Alarm ausgelöst wurde, nur gültig in verbindung mit GPIO19=1 UND GPIO33=0
		GPIO.setup(13, GPIO.IN, pull_up_down = GPIO.PUD_DOWN) # High, wenn Anlage unscharf
		GPIO.setup(6, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)  # High, wenn Anlage scharf
		#GPIO.setup(5, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)  # 10min Versatz zu GPIO19, Für dieses Programm aber nicht relevant

		if(GPIO.input(13) == 1 and GPIO.input(6) == 0):
			state = "unarmed"
		if(GPIO.input(13) == 0 and GPIO.input(6) == 1 and GPIO.input(19) == 1):
			state = "alarm"
		if(GPIO.input(13) == 0 and GPIO.input(6) == 1 and GPIO.input(19) == 0):
			state = "armed"

	except Exception as err:
		print(err, file=sys.stderr)
		state = "error"

	finally:
		GPIO.cleanup() # cleanup all GPIO
		return(state)

def SendMail(subject,body):
	smtp_server = smtp.getServer()
	port = smtp.getPort()  # For starttls
	sender_email = smtp.getSenderMail()
	receiver_email = smtp.getReceiverMail()
	password = smtp.getSenderPass()
	message = "From:\"Alarmanlage\" <alarmanlage@diyww.de>\nTo:\"Alarmempfaenger\"\nSubject:[AlarmanlageStatus] {}\n\n{}".format(subject,body)

	# Create a secure SSL context
	context = ssl.create_default_context()

	# Try to log in to server and send email
	try:
		server = smtplib.SMTP(smtp_server,port)
		server.ehlo() # Can be omitted
		server.starttls(context=context) # Secure the connection
		server.ehlo() # Can be omitted
		server.login(sender_email, password)
		server.sendmail(sender_email, receiver_email, message)
	except Exception as e:
		# Print any error messages to stdout
		print(e, file=sys.stderr)
	finally:
		if "server" in locals():
			server.quit()




def main():
	killer = GracefulKiller()  # Fängt Kill-Signale des Betriebssystems auf, in reagiert dann auf diese
	state = "unset"

	while not killer.kill_now: # Solange vom OS kein Kill-Signal kommt, dann Endlosschleife
		privious_state = state
		state = GetCurrentState()

		if(state == privious_state):
			time.sleep(10)
			continue

		if(privious_state == "unset"):
			print("The alarm system has just started")
			SendMail("Das Ueberwachungsprogramm wurde gestartet" , "ab jetzt folgen Statusaenderungen...")
			time.sleep(1)

		if(state == "armed"):
			print("The alarm system is in armed state")
			if SetWerkstattStatusWebseite("closed") == False:
				SendMail("Anlage scharf mit Fehler" , "Die Alarmanlage wurde soeben scharf geschaltet.\nBeim Setzen des Status auf der Webseite ist ein Fehler aufgetreten.")
			else:
				SendMail("Anlage scharf" , "Die Alarmanlage wurde soeben scharf geschaltet.")

		if(state == "unarmed"):
			print("The alarm system is in unarmed state")
			if SetWerkstattStatusWebseite("open") == False:
				SendMail("Anlage unscharf mit Fehler" , "Die Alarmanlage wurde soeben unscharf geschaltet.\nBeim Setzen des Status auf der Webseite ist ein Fehler aufgetreten.")
			else:
				SendMail("Anlage unscharf" , "Die Alarmanlage wurde soeben unscharf geschaltet.")

		if(state == "alarm"):
			print("The alarm system is in active alarm state")
			SendMail("ALARM!" , "Die Alarmanlage hat soeben Alarm ausgeloest!\nEs folgt keine weitere Meldung zu diesem Alarm!")

		if(state == "error" or state == "unknown"):
			print("The alarm system is in faulty state", file=sys.stderr)
			SendMail("Systemfehler" , "Die Alarmanlage meldet einen unbekannten Status oder arbeitet fehlerhaft.")


if __name__ == "__main__": # Wenn dieses Programm direkt aufgerufen wird, dann Starte die Funktion main()
	main()
