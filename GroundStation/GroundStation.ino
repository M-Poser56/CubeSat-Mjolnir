/*
Matt Poser, 11:49pm April 28th 2026
This script is for the ground station radio uplink/downlink comms operation

essentially, the groundstation UI and python backend will 
interact with the associated serial bus, once this script is spun up

this script will operate the uplink and downlink functionality of the groundstation
& LoRa radio module based on the architecture seen in the word doc

it will operate mainly as a listening device, reading telemetry command
packets off the radio and writing them to the serial bus as output

if a command is placed in the serial bus, it will begin its broadcast to the
satellite

let's see how well it works!
*/

#include <SPI.h>
#include <RH_RF95.h>
#include <ArduinoJson.h>
#include <RHReliableDatagram.h>

//constants
#define RFM95_CS   10
#define RFM95_RST   9
#define RFM95_INT   2
#define RF95_FREQ   915.0
#define BAUD_RATE 115200
#define CUBESAT_ADDR       1   //rfm9x.node on the satellite
#define GROUNDSTATION_ADDR 2   //Groundstation node. These values match python script

//variables
uint16_t groundstation_timeout = 30000; //milliseconds
uint8_t buf[RH_RF95_MAX_MESSAGE_LEN + 1];
String cubesat_sensor_packet = "";
String groundstation_command = "";



RH_RF95 rf95(RFM95_CS, RFM95_INT);
RHReliableDatagram manager(rf95, GROUNDSTATION_ADDR); //need manager for 'recieve with ack' functionality

void setup() {
    Serial.begin(BAUD_RATE); //fastest supported on the device
    while (!Serial);

    pinMode(RFM95_RST, OUTPUT);
    digitalWrite(RFM95_RST, HIGH);
    delay(10); //milliseconds
    //board reset
    digitalWrite(RFM95_RST, LOW);
    delay(10);
    digitalWrite(RFM95_RST, HIGH);
    delay(10);


    //manager and frequency inits
    if (!manager.init()) {
    Serial.println("radio init failed");
    while (1);
    }
    if (!rf95.setFrequency(RF95_FREQ)) {
        Serial.println("setFrequency failed");
        while (1);
    }

    //publish with ack parameters
    manager.setRetries(5);
    manager.setTimeout(1000); //double the timeout value on the
    //flight computer for when it publishes commands

    //serial read timeout value
    Serial.setTimeout(2); //very small, essentially an instantaneous check

}


void loop(){
    //this is our groundstation flow of code, which deals with
    //radio comms but also serial printing for the python backend
    //flow of the code is as follows:

    //step 1: listen for incoming packets from the CubeSat
    //how long does this function run for???
    //I think I am going to make it 'blocking' (ie,
    //will wait for much longer than i need it to)
    cubesat_sensor_packet = GroundStationListen(groundstation_timeout);

    //step 2: check the serial bus for commands from python
    //if command recieved, publish command to CubeSat
    //if not, do nothing
    //once done, clear buffer and eliminate queued messages
    if (Serial.available() > 0) { //if there is anything in the buffer
        groundstation_command = Serial.readString(); //'instantaneous'
        //call publish function, to cubesat
        GroundStationPublish(groundstation_command);
        //clear buffer
        clearSerialBuffer();
    }

    //step 3: write CubeSat data packet to serial, for python
    //backend to push to API/frontend
    //this function is instantaneous, and message will be stored in
    //the laptop's serial buffer
    Serial.println(cubesat_sensor_packet);

}



String GroundStationListen(uint16_t timeout){
    //in this function, we will retrieve the sensor packet
    //1. Listen with ack, 30s groundstation timer
    uint8_t len = RH_RF95_MAX_MESSAGE_LEN;
    uint8_t from;
    bool success = manager.recvfromAckTimeout(buf, &len, timeout, &from);

    //2. decode bytes into string (if message returned is valid)
    //if not, return "INVALID PACKET"
    if (!success) return "NO PACKET RECIEVED, 30s TIMEOUT";
    buf[len] = '\0';

    //3. return string object, decoded from bytes
    return String((char*)buf);
}


void GroundStationPublish(String cmd){
    //publish with ack command goes here, should be one line(?)
    manager.sendtoWait((uint8_t *)cmd.c_str(), cmd.length(), CUBESAT_ADDR);
    return;
}


void clearSerialBuffer() {
    while (Serial.available() > 0) {
        Serial.read();
    }
}  //claude wrote this, apparently Serial.flush() doesn't work in the way I think













