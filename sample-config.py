#!/usr/bin/python3

class SpaceState:
    server = "example.com"
    secret = "foo"
    def getServer():
        return(SpaceState.server)
    def getSecret():
        return(SpaceState.secret)

class AlarmURL:
    ResourceString = "/foo.html"
    Server = "example.com"
    def getResourceString():
        return(AlarmURL.ResourceString)
    def getServer():
	return(AlarmURL.Server)

class smtp:
    server = "example.com"
    port = 587 #STARTTLS-Port
    senderMail = "example@example.com"
    senderPass = "bar"
    receiverMail = "example@example.com"
    receiverMailAlarm = "alarm@example.com"
    def getServer():
        return(smtp.server)
    def getPort():
        return(smtp.port)
    def getSenderPass():
        return(smtp.senderPass)
    def getSenderMail():
        return(smtp.senderMail)
    def getReceiverMail():
        return(smtp.receiverMail)
    def getReceiverMailAlarm():
        return(smtp.receiverMailAlarm)


if __name__ == "__main__":
    exit(1)
