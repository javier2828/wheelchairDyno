var mqtt = require('mqtt');
//const Gpio = require('pigpio').Gpio;
//const pin = new Gpio(18, {mode: Gpio.OUTPUT});
//let freq = 100000;
var execSync = require('child_process').execSync; //execute terminal commands from js
var client  = mqtt.connect('mqtt://0.0.0.0',{
    username: process.env.TOKEN
});
// mqtt protocal
client.on('connect', function () {
    console.log('connected');
    client.subscribe('v1/devices/me/rpc/request/+')
});

client.on('message', function (topic, message) {
   // console.log('request.topic: ' + topic);
     test = message.toString()
     string = test.slice(31,32) // get level number from terminal
     num = parseInt(string)
     //console.log(test.slice(31,32))
    var requestId = topic.slice('v1/devices/me/rpc/request/'.length);
    //client acts as an echo service
    client.publish('v1/devices/me/rpc/response/' + requestId, message);
    
    if ( num == 1) { // save string state to text file
        execSync('rm /var/www/html/level.txt', {encoding: 'utf-8'}); //remove then echo state to file
        execSync('echo "1" >> /var/www/html/level.txt', {encoding: 'utf-8'});
     //   pin.hardwarePwmWrite(freq, 0*10000);
    }
    if ( num == 2) {
        execSync('rm /var/www/html/level.txt', {encoding: 'utf-8'});
        execSync('echo "2" >> /var/www/html/level.txt', {encoding: 'utf-8'});
      //  pin.hardwarePwmWrite(freq, 80*10000);
    }
    if ( num == 3) {
        execSync('rm /var/www/html/level.txt', {encoding: 'utf-8'});
        execSync('echo "3" >> /var/www/html/level.txt', {encoding: 'utf-8'});
     //   pin.hardwarePwmWrite(freq, 85*10000);
    }
    if ( num == 4) {
        execSync('rm /var/www/html/level.txt', {encoding: 'utf-8'});
        execSync('echo "4" >> /var/www/html/level.txt', {encoding: 'utf-8'});
     //   pin.hardwarePwmWrite(freq, 88*10000);
    }
    if ( num == 5) {
        execSync('rm /var/www/html/level.txt', {encoding: 'utf-8'});
        execSync('echo "5" >> /var/www/html/level.txt', {encoding: 'utf-8'});
     //   pin.hardwarePwmWrite(freq, 93*10000);
    }
    if ( num == 6) {
        execSync('rm /var/www/html/level.txt', {encoding: 'utf-8'});
        execSync('echo "6" >> /var/www/html/level.txt', {encoding: 'utf-8'});
       // pin.hardwarePwmWrite(freq, 100*10000);
    }
    // pin settings now changed from main py file 
   // pin.hardwarePwmWrite(freq, parseInt(string)*10000);

});
