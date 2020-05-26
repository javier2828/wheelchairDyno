
// script for button operation
var mqtt = require('mqtt');
var exec = require('child_process').exec;
// start server
var client = mqtt.connect('mqtt://0.0.0.0', {
    username: process.env.TOKEN2
});
// mqtt protocol
client.on('connect', function () {
    client.subscribe('v1/devices/me/rpc/request/+')
     console.log('0');
});

client.on('message', function (topic, message) {
    
    
    temp = message.toString() // get state from terminal
    string = temp.slice(30)
    string = string.slice(0, -1) // slice to get false or true seperated
    if (string === "false"){
        exec('echo 0 > /home/pi/log')
    }
    if (string === "true"){
        exec('echo 1 > /home/pi/log')
    }
    
});
