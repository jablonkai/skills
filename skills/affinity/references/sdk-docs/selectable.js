'use strict';

const { SelectableApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

class Selectable extends HandleObject {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'Selectable';
	}
	
	get isSelectable() {
		return true;
	}
}

module.exports.Selectable = Selectable;
