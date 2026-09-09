#downstream script for reaction wheels functionality

#this will follow the same (rough) architecture as the Mjolnir_Reboot.py and
#Star_tracker.py scripts, but will be a little bit more depth

#this script, will take in command information, and after some initialization of
#GPIO output & PWM pins, update the state of the onboard reaction wheel controls
#the flow of the script will recieve messages in the same way as the other two,
#but will update GPIO settings instead of running a subprocess command function