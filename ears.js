/*
Simple espruino program for the ear LIDAR sensors that:
   - moves the ears smoothly backwards and forwards as per the hero prop
   - sends LIDAR readings via a USB serial cable to the Pi
   - responds to the following commands from the USB serial port:
        - follow(), aim the ears forward and take readings
        - stop(), stop LIDAR readings and ear movement; reset to forward
        - scan(), move ears continously and scan surroundings
        - fast(), move ears quickly and scan surrroundings
        - think(), move ears without LIDAR readings
LIDAR messages are sent as JSON strings over USB serial
Published under The Unlicense
Richard Hopkins, 7th February 2021
*/
var PWM_l = 0.15; // minimum position for sevo
var PWM_r = 0.8; // maximum position for servo
var PIN_PWM_l = B15; // left ear PWM pin name
var PIN_PWM_r = B14; // right ear PWM pin name
var PIN_LIDARX_l = B4; // pin for LIDAR on/off
var PIN_LIDARX_r = A8; // pin for LIDAR on/off
var PIN_pot_l = B1; // pin for servo potentiometer
var PIN_pot_r = A7; // pin for servo potentiometer
var PIN_sda = B3; // pin for I2C SDA cable
var PIN_scl = B10; // pin for I2C SCL cable
var num_steps = 50; // number of steps in full sweep
var step = 0; // start at step 0
var direction = 1; // direction of first sweep
var LIDAR_l;  // object for left LIDAR sensor
var LIDAR_r; // object for right LIDAR sensor
var vRef = E.getAnalogVRef(); // voltage reference
var num_readings = 1;  // number of times voltage has been read
var lidar_freq = 0; // no readings initially
var move_freq = 0; // no movement initially
var move_callback; // movement callback
var lidar_callback; // reading callback
var transmit = false; // don't transmit data


// position servo as instructed (from 0 to 1)
// using a pulse between 0.75ms and 2.25ms
function setServo(pin,pos) {
   if (pos<0) pos=0;
   if (pos>1) pos=1;
   analogWrite(pin, (1+pos) / 50.0, {freq:20});
}

// initialise the LIDAR and I2C interfaces
// turn off the LIDARs and use the I2C 2 bus at 400kHz
function initHW(){
   digitalWrite(PIN_LIDARX_l,0);
   digitalWrite(PIN_LIDARX_r,0);
   I2C2.setup({sda:PIN_sda, scl:PIN_scl, bitrate:100000});
}

// create the LIDAR objects on the I2C bus
function initLIDAR(){
   digitalWrite(PIN_LIDARX_l,1);
   LIDAR_l = require("VL53L0X").connect(I2C2,{address:0x54});
   digitalWrite(PIN_LIDARX_r,1);
   LIDAR_r = require("VL53L0X").connect(I2C2,{address:0x56});
}

// maintain an average vRef number
function refine_vRef(){
  num_readings = num_readings + 1;
  reading = E.getAnalogVRef();
  vRef = (vRef * (num_readings-1)/num_readings) + (reading/num_readings);
}

function switchConsole(){
    Serial1.setConsole();
    transmit = true;
}

 // move frequency, lidar frequency
 function follow(){
    resetIntervals(0,10);
}

function stop(){
    resetIntervals(0,0);
}

function scan(){
    resetIntervals(20,10);
}

function fast(){
    resetIntervals(75,20);
}

function think(){
    resetIntervals(50,0);
}

function onInit() {
    USB.setup(115200,{bytesize:8,stopbits:1});
    initHW();
    initLIDAR();
    clearInterval();
    clearTimeout();
    transmit = false;
    setTimeout(switchConsole, 30000); // give time for Pi to boot and make USB connection 
 }


// calculate desired servo position based on step
// the trigonometry smooths the movement of the servos
function calculateServoPos(step) {
    // each swing of the ears is separated into a number of steps (num_steps)
    // and the angle is calculated as the fraction of a half circle
    angle = step/num_steps*Math.PI;
    // the position calculated transforms the linear steps into a smoooth
    // natural motion
    position = (angle-(Math.cos(angle)*Math.sin(angle)))/Math.PI;
    return position;
 }

 // translates the relative position to an absolute one
 // this allows the movement of the ears to be constrained
 // if necessary
 function scaleServoPos(position) {
    scaled_pos = PWM_l + ((PWM_r-PWM_l)*position);
    return scaled_pos;
 }

 // send a JSON message to the Rapsberry Pi via a USB serial connection
 function sendMsg(type,sensor,distance,angle) {
    messageStr = JSON.stringify(message);
    if (transmit) {
        USB.println(messageStr);
     }
   }
 
 function volts2angle(volts,ear){
    var MIN_V = 1.33; // lowest likely POT value
    var MAX_V = 2.10; // highest likely POT value
    var MAX_ANG = Math.PI/4;  // ears can travel roughly 45 degrees
    // normalize the voltage to a value between 0 and 1
    angle = Math.min((Math.max(volts - MIN_V,0))/(MAX_V-MIN_V),1.00);
    if (ear == 'l_ear'){
       angle = 1 - angle; // for left ear max volts is minimum angle
    }
    if (ear == 'r_ear'){
       angle = angle * -1; // for right ear, angle is negative
    }
    angle = angle * MAX_ANG;
    return angle;
 }
 
 // take a reading from each of the LIDAR sensors
 function takeReading(){
   takeEarReading(LIDAR_l,PIN_pot_l,"l_ear");
   takeEarReading(LIDAR_r,PIN_pot_r,"r_ear");
}

function takeEarReading(read_lidar,read_pin,ear){
   volts = analogRead(read_pin)*vRef;
   ear_dir=volts2angle(volts,ear);
   dist = read_lidar.performSingleMeasurement().distance;
   // if distance is larger than 20mm, 
   // and smaller than 8m then report distance
   if (dist > 20.0 && dist < 8000.0) {
     dist = dist/1000; // convert to metres from mm
     message = {type:"LIDAR",sensor:ear,distance:dist,angle:ear_dir};
     sendMsg(message);
   }
 }

 // calculate the next position for the servos and move them to it
 function moveEars(){
    step = step + direction;
    if (step > num_steps) {
        direction = -1;
        step = num_steps-1;
    }
    if (step < 0) {
        direction = 1;
        step = 1;
    }
    scaled_pos = step_lookup[step];
    setServo(PIN_PWM_l,scaled_pos);
    setServo(PIN_PWM_r,1-scaled_pos);
}

 // put ears into neutral position
 function resetEars(){
       scaled_pos = step_lookup[num_steps-2];
       setServo(PIN_PWM_l,scaled_pos);
       setServo(PIN_PWM_r,1-scaled_pos);
  }

 function resetIntervals(move_freq,lidar_freq){
    clearInterval();
    setInterval(refine_vRef,1000);
    if (move_freq > 0) {
        move_interval = 1000.0/move_freq;
        move_callback = setInterval(moveEars,move_interval);
    }
    else {
        resetEars();
    }
    if (lidar_freq > 0) {
        reading_interval = 1000.0/lidar_freq;
        lidar_callback = setInterval(takeReading,reading_interval);
    }
 }

 // create an array of all the valid scaled positions
 step_lookup = [];
 for (step = 0; step <= num_steps; step++) {
   step_lookup[step] = scaleServoPos(calculateServoPos(step));
 }
 step = 0;
 setInterval(refine_vRef,1000);