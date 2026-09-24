'use strict';

const { ConfigurationItemApi, ConfigurationValueType, EnumerationResult } = require('affinity:common');
const { HandleObject } = require('./handleobject.js');

class ConfigurationProperty {
    constructor(name, item) {
        this.name = name;
        this.item = item;
    }

    get [Symbol.toStringTag]() {
        return 'ConfigurationProperty';
    }
}

class ConfigurationItem extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ConfigurationItem';
    }

    static createFromJsonString(jsonStr, allowComments = false) {
        const h = ConfigurationItemApi.createFromJsonString(jsonStr, !!allowComments);
        return (h == null) ? null : new ConfigurationItem(h);
    }

    get valueType() {
        return ConfigurationItemApi.getValueType(this.handle);
    }

    get isObject() {
        return ConfigurationItemApi.isObject(this.handle);
    }

    get isArray() {
        return ConfigurationItemApi.isArray(this.handle);
    }

    get isString() {
        return ConfigurationItemApi.isString(this.handle);
    }

    get isNumber() {
        return ConfigurationItemApi.isNumber(this.handle);
    }

    get isFloat() {
        return ConfigurationItemApi.isFloat(this.handle);
    }

    get isUint() {
        return ConfigurationItemApi.isUint(this.handle);
    }

    get isInt() {
        return ConfigurationItemApi.isInt(this.handle);
    }

    get isBool() {
        return ConfigurationItemApi.isBool(this.handle);
    }

    get isNull() {
        return ConfigurationItemApi.isNull(this.handle);
    }

    get isBinary() {
        return ConfigurationItemApi.isBinary(this.handle);
    }

    get isPrimitive() {
        return ConfigurationItemApi.isPrimitive(this.handle);
    }

    get isStructured() {
        return ConfigurationItemApi.isStructured(this.handle);
    }

    get string() {
        return ConfigurationItemApi.getString(this.handle);
    }

    get float() {
        return ConfigurationItemApi.getFloat(this.handle);
    }

    get int() {
        return ConfigurationItemApi.getInt(this.handle);
    }

    get uint() {
        return ConfigurationItemApi.getUint(this.handle);
    }

    get bool() {
        return ConfigurationItemApi.getBool(this.handle);
    }

    get value() {
        switch (this.valueType) {
            case ConfigurationValueType.String: return this.string;
            case ConfigurationValueType.Float: return this.float;
            case ConfigurationValueType.Int:    return this.int;
            case ConfigurationValueType.Uint:   return this.uint;
            case ConfigurationValueType.Bool:   return this.bool;
            case ConfigurationValueType.Null:   return null;
            case ConfigurationValueType.Array:  return this.items.map(item => item.value);
            case ConfigurationValueType.Object: return Object.fromEntries(this.properties.map(p => [p.name, p.item.value]));
            default:                            return undefined;
        }
    }

    stringOrDefault(defaultValue) {
        return ConfigurationItemApi.getStringOrDefault(this.handle, defaultValue);
    }

    floatOrDefault(defaultValue) {
        return ConfigurationItemApi.getFloatOrDefault(this.handle, defaultValue);
    }

    intOrDefault(defaultValue) {
        return ConfigurationItemApi.getIntOrDefault(this.handle, defaultValue);
    }

    uintOrDefault(defaultValue) {
        return ConfigurationItemApi.getUintOrDefault(this.handle, defaultValue);
    }

    boolOrDefault(defaultValue) {
        return ConfigurationItemApi.getBoolOrDefault(this.handle, defaultValue);
    }

    // Array accessors
    getArrayLength() {
        return ConfigurationItemApi.getArrayLength(this.handle);
    }

    getArrayItem(index) {
        const h = ConfigurationItemApi.getArrayItem(this.handle, index);
        return (h == null) ? null : new ConfigurationItem(h);
    }

    // Object accessors
    get propertyCount() {
        return ConfigurationItemApi.getPropertyCount(this.handle);
    }

    hasProperty(name) {
        return ConfigurationItemApi.hasProperty(this.handle, name);
    }

    getProperty(name) {
        const h = ConfigurationItemApi.getProperty(this.handle, name);
        return (h == null) ? null : new ConfigurationItem(h);
    }

    getPropertyString(name) {
        return ConfigurationItemApi.getPropertyString(this.handle, name);
    }

    getPropertyStringOrDefault(name, defaultValue) {
        return ConfigurationItemApi.getPropertyStringOrDefault(this.handle, name, defaultValue);
    }

    getPropertyFloat(name) {
        return ConfigurationItemApi.getPropertyFloat(this.handle, name);
    }

    getPropertyFloatOrDefault(name, defaultValue) {
        return ConfigurationItemApi.getPropertyFloatOrDefault(this.handle, name, defaultValue);
    }

    getPropertyInt(name) {
        return ConfigurationItemApi.getPropertyInt(this.handle, name);
    }

    getPropertyIntOrDefault(name, defaultValue) {
        return ConfigurationItemApi.getPropertyIntOrDefault(this.handle, name, defaultValue);
    }

    getPropertyUint(name) {
        return ConfigurationItemApi.getPropertyUint(this.handle, name);
    }

    getPropertyUintOrDefault(name, defaultValue) {
        return ConfigurationItemApi.getPropertyUintOrDefault(this.handle, name, defaultValue);
    }

    getPropertyBool(name) {
        return ConfigurationItemApi.getPropertyBool(this.handle, name);
    }

    getPropertyBoolOrDefault(name, defaultValue) {
        return ConfigurationItemApi.getPropertyBoolOrDefault(this.handle, name, defaultValue);
    }

    enumerateProperties(callback) {
        if (typeof callback === 'function') {
            function wrapped(name, valueHandle) {
                return callback(name, (valueHandle == null) ? null : new ConfigurationItem(valueHandle));
            }
            return ConfigurationItemApi.enumerateProperties(this.handle, wrapped);
        }
        return ConfigurationItemApi.enumerateProperties(this.handle, callback);
    }

    enumeratePropertyNames(callback) {
        ConfigurationItemApi.enumeratePropertyNames(this.handle, callback);
    }

    enumerateItems(callback) {
        if (typeof callback === 'function') {
            function wrapped(valueHandle) {
                return callback((valueHandle == null) ? null : new ConfigurationItem(valueHandle));
            }
            return ConfigurationItemApi.enumerateItems(this.handle, wrapped);
        }
        return ConfigurationItemApi.enumerateItems(this.handle, callback);
    }

    get properties() {
        const res = [];
        this.enumerateProperties((name, item) => { res.push(new ConfigurationProperty(name, item)); return EnumerationResult.Continue; });
        return res;
    }

    get propertyNames() {
        const res = [];
        this.enumeratePropertyNames((name) => { res.push(name); return EnumerationResult.Continue; });
        return res;
    }

    // Array / Object accessor
    get items() {
        const res = [];
        this.enumerateItems((item) => { res.push(item); return EnumerationResult.Continue; });
        return res;
    }
}

module.exports.ConfigurationItem = ConfigurationItem;
module.exports.ConfigurationValueType = ConfigurationValueType;
