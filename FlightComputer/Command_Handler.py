#file for the command handler script
#will recieve packets via mqtt, parse the strings, and decide on which topic
#to appropriately publish commands
import queue
import paho.mqtt.client as mqtt
import re


command_queue = queue.Queue() #initialize script local queue to store upstream command messages

#NEED TO TEST THE COMMANDS ARE GETTING THROUGH BEFORE WRITING ANY MORE CODE
def CommandHandlerPublish(topublish):
    #check string against known commands, directly
    #if match, publish
    #if not, thrown away
    topublish = topublish.strip() #immense, immense, paranoia
    if topublish == "CMD:REBOOT":
        #instantaneous (ish) publish to the reboot downstream appropriate topic
        Command_Handler_client.publish("CMD/REBOOT", topublish)
    elif topublish == "CMD:STARTRACKER":
        Command_Handler_client.publish("CMD/STARTRACKER", topublish)
    elif bool(re.fullmatch(r"CMD:REACTIONWHEELS\{-?\d+,-?\d+,-?\d+\}", topublish)): #checks for signed integers in PWM% spots
        Command_Handler_client.publish("CMD/REACTIONWHEELS", topublish)
    else:
        print(f"INVALID HANDLER COMMAND: {topublish}, DISCARDED")
        print("The little things, that make me so happy")
        print("All I wanna do is live by the sea!")
        print("- Oasis")

    return
        



#mqtt functions
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"mqtt localhost connected with result code {reason_code}")
    client.subscribe("CMD/HANDLER") #upstream being published to by LoRA_ULDL in the CommandHandler() function

def on_message(client, userdata, msg):
    command_queue.put(msg.payload.decode()) #adds command string to queue, FIFO

Command_Handler_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
Command_Handler_client.on_connect = on_connect
Command_Handler_client.on_message = on_message
Command_Handler_client.connect("localhost", 1883)
Command_Handler_client.loop_start()


try:
    while True:
        #basic flow of this script is as follows:

        #step 1: use mqtt subscribe & queue architecture to wait for a command string
        #until one is published, then this hangs here (as expected)
        #based on architecture upstream, we should essentially never recieve more than one in
        #quick succession. It should only ever be one 'once in a while'
        recieved_command = command_queue.get()


        #step 2: string parsing & publishing function
        #this function simply takes in the the recieved_command string
        #variable, and does the following (~instantaneously)
        #1-parses string to match with a valid onboard command set. 
        #If no match (slips by initial check)
        #command is thrown out as garbage
        #2-sends the categorized command string to the proper downstream topic.
        #There will be 3: STARTRACKER, REBOOT, REACTIONWHEELS
        CommandHandlerPublish(recieved_command)

        

finally:
    print("Flight Computer Command Handler Deactivated")