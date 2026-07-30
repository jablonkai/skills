'use strict';

const { TimerApi } = require('affinity:timers');
const { HandleObject } = require('./handleobject.js');

class Timer extends HandleObject {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'Timer';
	}
	
	static create() {
		return new Timer(TimerApi.create());
	}
	
	cancel() {
		TimerApi.cancel(this.handle);
	}
	
	static cancelAll() {
		TimerApi.cancelAll();
	}
	
	static get now() {
		return TimerApi.getNow();
	}
	
	get expiry() {
		return TimerApi.getExpiry(this.handle);
	}
	
	set expiry(value) {
		TimerApi.setExpiry(this.handle, value);
	}

	get expiryBigInt() {
		return TimerApi.getExpiry(this.handle, true);
	}
		
	set expiryBigInt(value) {
		TimerApi.setExpiry(this.handle, value);
	}

	moveExpiry(value) {
		TimerApi.moveExpiry(this.handle, value);
	}
	
	get expiryFromNow() {
		return TimerApi.getExpiryFromNow(this.handle);
	}
	
	set expiryFromNow(value) {
		TimerApi.setExpiryFromNow(this.handle, value);
	}
	
	waitAsync(callback) {
		TimerApi.waitAsync(this.handle, callback);
	}

	dispose() {
		TimerApi.dispose(this.handle);
	}

	// ASIO-esque aliases
	get expiresFromNow() {
		return this.expiryFromNow;
	}
	
	set expiresFromNow(value) {
		this.expiryFromNow = value;
	}
}

function timeoutCallback(errorCode, callback, ...args) {
	callback(errorCode, ...args);
}

function setTimeout(delay, callback, ...args) {
	let timer = Timer.create();
	timer.expiryFromNow = delay;
	if (typeof callback === 'function') {
		timer.waitAsync((errorCode) => timeoutCallback(errorCode, callback, ...args));
	} else {
		timer.waitAsync(callback);
	}
	return timer;
}

function intervalCallback(err, timer, delay, callback, ...args) {
	if (!err) {
		timer.expiryFromNow = delay;
		timer.waitAsync((errorCode) => intervalCallback(errorCode, timer, delay, callback, ...args));
	}
	callback(err, ...args);
}

function setInterval(delay, callback, ...args) {
	let timer = Timer.create();
	timer.expiryFromNow = delay;
	if (typeof callback === 'function') {
		timer.waitAsync((errorCode) => intervalCallback(errorCode, timer, delay, callback, ...args));
	} else {
		timer.waitAsync(callback);
	}
	return timer;
}

// This isn't really like Node's setImmediate because it does the equivalent of setTimeout(0),
// but it will provide some level of compatibility.
function setImmediate(callback, ...args) {
	let timer = Timer.create();
	timer.expiryFromNow = 0;
	if (typeof callback === 'function') {
		timer.waitAsync((errorCode) => timeoutCallback(errorCode, callback, ...args));
	} else {
		timer.waitAsync(callback);
	}
	return timer;
}

module.exports.Timer = Timer;
module.exports.setImmediate = setImmediate;
module.exports.setTimeout = setTimeout;
module.exports.setInterval = setInterval;
