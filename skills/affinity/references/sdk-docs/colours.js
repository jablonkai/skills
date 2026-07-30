'use strict';

const { ColourApi, ColourProfileApi, ColourProfileSetApi, ColourSpaceType, GradientApi } = require('affinity:colours');
const { EnumerationResult } = require('affinity:common');
const { RasterFormat, RasterIntent } = require('affinity:raster');
const { HandleObject } = require('./handleobject.js');

class Colour extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Colour';
    }

    get isColour() {
        return true;
    }

    static createRGBA8(data) {
        return new Colour(ColourApi.createRGBA8(data));
    }

    static createRGBA16(data) {
        return new Colour(ColourApi.createRGBA16(data));
    }

    static createRGBAuf(data) {
        return new Colour(ColourApi.createRGBAuf(data));
    }

    static createIA8(data) {
        return new Colour(ColourApi.createIA8(data));
    }

    static createIA16(data) {
        return new Colour(ColourApi.createIA16(data));
    }

    static createCMYKA8(data) {
        return new Colour(ColourApi.createCMYKA8(data));
    }

    static createCMYKAf(data) {
        return new Colour(ColourApi.createCMYKAf(data));
    }

    static createLABA16(data) {
        return new Colour(ColourApi.createLABA16(data));
    }

    static createHSLAf(data) {
        return new Colour(ColourApi.createHSLAf(data));
    }

    static createDefault() {
        return new Colour(ColourApi.createDefault());
    }

    clone() {
        return new Colour(ColourApi.clone(this.handle));
    }

    getRGBA8(applyTint, colourProfileSet) {
        return ColourApi.getRGBA8(this.handle, applyTint, colourProfileSet?.handle);
    }

    getRGBA16(applyTint, colourProfileSet) {
        return ColourApi.getRGBA16(this.handle, applyTint, colourProfileSet?.handle);
    }

    getRGBAuf(applyTint, colourProfileSet) {
        return ColourApi.getRGBAuf(this.handle, applyTint, colourProfileSet?.handle);
    }

    getIA8(applyTint, colourProfileSet) {
        return ColourApi.getIA8(this.handle, applyTint, colourProfileSet?.handle);
    }

    getIA16(applyTint, colourProfileSet) {
        return ColourApi.getIA16(this.handle, applyTint, colourProfileSet?.handle);
    }

    getCMYKA8(applyTint, colourProfileSet) {
        return ColourApi.getCMYKA8(this.handle, applyTint, colourProfileSet?.handle);
    }

    getCMYKAf(applyTint, colourProfileSet) {
        return ColourApi.getCMYKAf(this.handle, applyTint, colourProfileSet?.handle);
    }

    getHSLAf(applyTint, colourProfileSet) {
        return ColourApi.getHSLAf(this.handle, applyTint, colourProfileSet?.handle);
    }

    get alpha() {
        return ColourApi.getAlpha(this.handle);
    }

    set alpha(value) {
        ColourApi.setAlpha(this.handle, value);
    }

    get intensity() {
        return ColourApi.getIntensity(this.handle);
    }

    set intensity(value) {
        ColourApi.setIntensity(this.handle, value);
    }

    get noise() {
        return ColourApi.getNoise(this.handle);
    }

    set noise(value) {
        ColourApi.setNoise(this.handle, value);
    }

    get overprint() {
        return ColourApi.getOverprint(this.handle);
    }

    set overprint(value) {
        ColourApi.setOverprint(this.handle, value);
    }

    get tint() {
        return ColourApi.getTint(this.handle);
    }

    set tint(value) {
        ColourApi.setTint(this.handle, value);
    }
    
    convertProfile(srcProfile, destProfile, intent, blackPointCompensation) {
        ColourApi.convertProfile(this.handle, srcProfile.handle, destProfile.handle, intent, blackPointCompensation);
        return this;
    }
    
    get rgba8() {
        return ColourApi.getRGBA8(this.handle);
    }

    get rgba16() {
        return ColourApi.getRGBA16(this.handle);
    }

    get rgbauf() {
        return ColourApi.getRGBAuf(this.handle);
    }

    get ia8() {
        return ColourApi.getIA8(this.handle);
    }

    get ia16() {
        return ColourApi.getIA16(this.handle);
    }

    get cmyka8() {
        return ColourApi.getCMYKA8(this.handle);
    }

    get cmykaf() {
        return ColourApi.getCMYKAf(this.handle);
    }

    get laba16() {
        return ColourApi.getLABA16(this.handle);
    }

    get hslaf() {
        return ColourApi.getHSLAf(this.handle);
    }

    // convenience / aliases
    get rgb() {
        return this.rgba8;
    }

    get rgba() {
        return this.rgba8;
    }

    get rgb16() {
        return this.rgba16;
    }

    get rgbf() {
        return this.rgbauf;
    }
    
    get rgbaf() {
        return this.rgbauf;
    }

    get i() {
        return this.ia8;
    }

    get i8() {
        return this.ia8;
    }

    get ia() {
        return this.ia8;
    }

    get i16() {
        return this.ia16;
    }

    get cmyk() {
        return this.cmyka8;
    }

    get cmyka() {
        return this.cmyka8;
    }

    get cmykf() {
        return this.cmykaf;
    }

    get lab() {
        return this.laba16;
    }

    get lab16() {
        return this.laba16;
    }

    get hsl() {
        return this.hslaf;
    }
}

function RGB8(r, g, b) {
    return Colour.createRGBA8({r:r, g:g, b:b, alpha:255});
}

function RGBA8(r, g, b, alpha) {
    if (alpha == null)
        alpha = 255;
    return Colour.createRGBA8({r:r, g:g, b:b, alpha:alpha});
}

function RGB16(r, g, b) {
    return Colour.createRGBA16({r:r, g:g, b:b, alpha:65535});
}

function RGBA16(r, g, b, alpha) {
    if (alpha == null)
        alpha = 65535;
    return Colour.createRGBA16({r:r, g:g, b:b, alpha:alpha});
}

function RGBAuf(r, g, b, alpha) {
    if (alpha == null)
        alpha = 1.0;
    return Colour.createRGBAuf({r:r, g:g, b:b, alpha:alpha});
}

function I8(intensity) {
    return Colour.createIA8({i:intensity, alpha:255});
}

function IA8(intensity, alpha) {
    if (alpha == null)
        alpha = 255;
    return Colour.createIA8({i:intensity, alpha:alpha});
}

function I16(intensity) {
    return Colour.createIA8({i:intensity, alpha:65535});
}

function IA16(intensity, alpha) {
    if (alpha == null)
        alpha = 65535;
    return Colour.createIA8({i:intensity, alpha:alpha});
}

function CMYK8(c, m, y, k) {
    return Colour.createCMYKA8({c:c, m:m, y:y, k:k, alpha:255});
}

function CMYKA8(c, m, y, k, alpha) {
    if (alpha == null)
        alpha = 255;
    return Colour.createCMYKA8({c:c, m:m, y:y, k:k, alpha:alpha});
}

function CMYKf(c, m, y, k) {
    return Colour.createCMYKAf({c:c, m:m, y:y, k:k, alpha:1.0});
}

function CMYKAf(c, m, y, k, alpha) {
    if (alpha == null)
        alpha = 1.0;
    return Colour.createCMYKAf({c:c, m:m, y:y, k:k, alpha:alpha});
}

function LAB16(l, a, b) {
    return Colour.createLABA16({l:l, a:a, b:b, alpha:65535});
}

function LABA16(l, a, b, alpha) {
    if (alpha == null)
        alpha = 65535;
    return Colour.createLABA16({l:l, a:a, b:b, alpha:alpha});
}

function HSLf(h, s, l) {
    return Colour.createHSLAf({h:h, s:s, l:l, alpha:1.0});
}

function HSLAf(h, s, l, alpha) {
    if (alpha == null)
        alpha = 1.0;
    return Colour.createHSLAf({h:h, s:s, l:l, alpha:alpha});
}

// SVG 1.1 named colours
// https://www.w3.org/TR/SVG11/types.html#ColorKeywords
class SVG11 {
    static get aliceblue() {
        return RGBA8(240, 248, 255);
    }
    static get antiquewhite() {
        return RGBA8(250, 235, 215);
    }
    static get aqua() {
        return RGBA8(0, 255, 255);
    }
    static get aquamarine() {
        return RGBA8(127, 255, 212);
    }
    static get azure() {
        return RGBA8(240, 255, 255);
    }
    static get beige() {
        return RGBA8(245, 245, 220);
    }
    static get bisque() {
        return RGBA8(255, 228, 196);
    }
    static get black() {
        return RGBA8(0, 0, 0);
    }
    static get blanchedalmond() {
        return RGBA8(255, 235, 205);
    }
    static get blue() {
        return RGBA8(0, 0, 255);
    }
    static get blueviolet() {
        return RGBA8(138, 43, 226);
    }
    static get brown() {
        return RGBA8(165, 42, 42);
    }
    static get burlywood() {
        return RGBA8(222, 184, 135);
    }
    static get cadetblue() {
        return RGBA8(95, 158, 160);
    }
    static get chartreuse() {
        return RGBA8(127, 255, 0);
    }
    static get chocolate() {
        return RGBA8(210, 105, 30);
    }
    static get coral() {
        return RGBA8(255, 127, 80);
    }
    static get cornflowerblue() {
        return RGBA8(100, 149, 237);
    }
    static get cornsilk() {
        return RGBA8(255, 248, 220);
    }
    static get crimson() {
        return RGBA8(220, 20, 60);
    }
    static get cyan() {
        return RGBA8(0, 255, 255);
    }
    static get darkblue() {
        return RGBA8(0, 0, 139);
    }
    static get darkcyan() {
        return RGBA8(0, 139, 139);
    }
    static get darkgoldenrod() {
        return RGBA8(184, 134, 11);
    }
    static get darkgray() {
        return RGBA8(169, 169, 169);
    }
    static get darkgreen() {
        return RGBA8(0, 100, 0);
    }
    static get darkgrey() {
        return RGBA8(169, 169, 169);
    }
    static get darkkhaki() {
        return RGBA8(189, 183, 107);
    }
    static get darkmagenta() {
        return RGBA8(139, 0, 139);
    }
    static get darkolivegreen() {
        return RGBA8(85, 107, 47);
    }
    static get darkorange() {
        return RGBA8(255, 140, 0);
    }
    static get darkorchid() {
        return RGBA8(153, 50, 204);
    }
    static get darkred() {
        return RGBA8(139, 0, 0);
    }
    static get darksalmon() {
        return RGBA8(233, 150, 122);
    }
    static get darkseagreen() {
        return RGBA8(143, 188, 143);
    }
    static get darkslateblue() {
        return RGBA8(72, 61, 139);
    }
    static get darkslategray() {
        return RGBA8(47, 79, 79);
    }
    static get darkslategrey() {
        return RGBA8(47, 79, 79);
    }
    static get darkturquoise() {
        return RGBA8(0, 206, 209);
    }
    static get darkviolet() {
        return RGBA8(148, 0, 211);
    }
    static get deeppink() {
        return RGBA8(255, 20, 147);
    }
    static get deepskyblue() {
        return RGBA8(0, 191, 255);
    }
    static get dimgray() {
        return RGBA8(105, 105, 105);
    }
    static get dimgrey() {
        return RGBA8(105, 105, 105);
    }
    static get dodgerblue() {
        return RGBA8(30, 144, 255);
    }
    static get firebrick() {
        return RGBA8(178, 34, 34);
    }
    static get floralwhite() {
        return RGBA8(255, 250, 240);
    }
    static get forestgreen() {
        return RGBA8(34, 139, 34);
    }
    static get fuchsia() {
        return RGBA8(255, 0, 255);
    }
    static get gainsboro() {
        return RGBA8(220, 220, 220);
    }
    static get ghostwhite() {
        return RGBA8(248, 248, 255);
    }
    static get gold() {
        return RGBA8(255, 215, 0);
    }
    static get goldenrod() {
        return RGBA8(218, 165, 32);
    }
    static get gray() {
        return RGBA8(128, 128, 128);
    }
    static get grey() {
        return RGBA8(128, 128, 128);
    }
    static get green() {
        return RGBA8(0, 128, 0);
    }
    static get greenyellow() {
        return RGBA8(173, 255, 47);
    }
    static get honeydew() {
        return RGBA8(240, 255, 240);
    }
    static get hotpink() {
        return RGBA8(255, 105, 180);
    }
    static get indianred() {
        return RGBA8(205, 92, 92);
    }
    static get indigo() {
        return RGBA8(75, 0, 130);
    }
    static get ivory() {
        return RGBA8(255, 255, 240);
    }
    static get khaki() {
        return RGBA8(240, 230, 140);
    }
    static get lavender() {
        return RGBA8(230, 230, 250);
    }
    static get lavenderblush() {
        return RGBA8(255, 240, 245);
    }
    static get lawngreen() {
        return RGBA8(124, 252, 0);
    }
    static get lemonchiffon() {
        return RGBA8(255, 250, 205);
    }
    static get lightblue() {
        return RGBA8(173, 216, 230);
    }
    static get lightcoral() {
        return RGBA8(240, 128, 128);
    }
    static get lightcyan() {
        return RGBA8(224, 255, 255);
    }
    static get lightgoldenrodyellow() {
        return RGBA8(250, 250, 210);
    }
    static get lightgray() {
        return RGBA8(211, 211, 211);
    }
    static get lightgreen() {
        return RGBA8(144, 238, 144);
    }
    static get lightgrey() {
        return RGBA8(211, 211, 211);
    }
    static get lightpink() {
        return RGBA8(255, 182, 193);
    }
    static get lightsalmon() {
        return RGBA8(255, 160, 122);
    }
    static get lightseagreen() {
        return RGBA8(32, 178, 170);
    }
    static get lightskyblue() {
        return RGBA8(135, 206, 250);
    }
    static get lightslategray() {
        return RGBA8(119, 136, 153);
    }
    static get lightslategrey() {
        return RGBA8(119, 136, 153);
    }
    static get lightsteelblue() {
        return RGBA8(176, 196, 222);
    }
    static get lightyellow() {
        return RGBA8(255, 255, 224);
    }
    static get lime() {
        return RGBA8(0, 255, 0);
    }
    static get limegreen() {
        return RGBA8(50, 205, 50);
    }
    static get linen() {
        return RGBA8(250, 240, 230);
    }
    static get magenta() {
        return RGBA8(255, 0, 255);
    }
    static get maroon() {
        return RGBA8(128, 0, 0);
    }
    static get mediumaquamarine() {
        return RGBA8(102, 205, 170);
    }
    static get mediumblue() {
        return RGBA8(0, 0, 205);
    }
    static get mediumorchid() {
        return RGBA8(186, 85, 211);
    }
    static get mediumpurple() {
        return RGBA8(147, 112, 219);
    }
    static get mediumseagreen() {
        return RGBA8(60, 179, 113);
    }
    static get mediumslateblue() {
        return RGBA8(123, 104, 238);
    }
    static get mediumspringgreen() {
        return RGBA8(0, 250, 154);
    }
    static get mediumturquoise() {
        return RGBA8(72, 209, 204);
    }
    static get mediumvioletred() {
        return RGBA8(199, 21, 133);
    }
    static get midnightblue() {
        return RGBA8(25, 25, 112);
    }
    static get mintcream() {
        return RGBA8(245, 255, 250);
    }
    static get mistyrose() {
        return RGBA8(255, 228, 225);
    }
    static get moccasin() {
        return RGBA8(255, 228, 181);
    }
    static get navajowhite() {
        return RGBA8(255, 222, 173);
    }
    static get navy() {
        return RGBA8(0, 0, 128);
    }
    static get oldlace() {
        return RGBA8(253, 245, 230);
    }
    static get olive() {
        return RGBA8(128, 128, 0);
    }
    static get olivedrab() {
        return RGBA8(107, 142, 35);
    }
    static get orange() {
        return RGBA8(255, 165, 0);
    }
    static get orangered() {
        return RGBA8(255, 69, 0);
    }
    static get orchid() {
        return RGBA8(218, 112, 214);
    }
    static get palegoldenrod() {
        return RGBA8(238, 232, 170);
    }
    static get palegreen() {
        return RGBA8(152, 251, 152);
    }
    static get paleturquoise() {
        return RGBA8(175, 238, 238);
    }
    static get palevioletred() {
        return RGBA8(219, 112, 147);
    }
    static get papayawhip() {
        return RGBA8(255, 239, 213);
    }
    static get peachpuff() {
        return RGBA8(255, 218, 185);
    }
    static get peru() {
        return RGBA8(205, 133, 63);
    }
    static get pink() {
        return RGBA8(255, 192, 203);
    }
    static get plum() {
        return RGBA8(221, 160, 221);
    }
    static get powderblue() {
        return RGBA8(176, 224, 230);
    }
    static get purple() {
        return RGBA8(128, 0, 128);
    }
    static get rebeccapurple() {
        return RGBA8(102, 51, 153);
    }
    static get red() {
        return RGBA8(255, 0, 0);
    }
    static get rosybrown() {
        return RGBA8(188, 143, 143);
    }
    static get royalblue() {
        return RGBA8(65, 105, 225);
    }
    static get saddlebrown() {
        return RGBA8(139, 69, 19);
    }
    static get salmon() {
        return RGBA8(250, 128, 114);
    }
    static get sandybrown() {
        return RGBA8(244, 164, 96);
    }
    static get seagreen() {
        return RGBA8(46, 139, 87);
    }
    static get seashell() {
        return RGBA8(255, 245, 238);
    }
    static get sienna() {
        return RGBA8(160, 82, 45);
    }
    static get silver() {
        return RGBA8(192, 192, 192);
    }
    static get skyblue() {
        return RGBA8(135, 206, 235);
    }
    static get slateblue() {
        return RGBA8(106, 90, 205);
    }
    static get slategray() {
        return RGBA8(112, 128, 144);
    }
    static get slategrey() {
        return RGBA8(112, 128, 144);
    }
    static get snow() {
        return RGBA8(255, 250, 250);
    }
    static get springgreen() {
        return RGBA8(0, 255, 127);
    }
    static get steelblue() {
        return RGBA8(70, 130, 180);
    }
    static get tan() {
        return RGBA8(210, 180, 140);
    }
    static get teal() {
        return RGBA8(0, 128, 128);
    }
    static get thistle() {
        return RGBA8(216, 191, 216);
    }
    static get tomato() {
        return RGBA8(255, 99, 71);
    }
    static get turquoise() {
        return RGBA8(64, 224, 208);
    }
    static get violet() {
        return RGBA8(238, 130, 238);
    }
    static get wheat() {
        return RGBA8(245, 222, 179);
    }
    static get white() {
        return RGBA8(255, 255, 255);
    }
    static get whitesmoke() {
        return RGBA8(245, 245, 245);
    }
    static get yellow() {
        return RGBA8(255, 255, 0);
    }
    static get yellowgreen() {
        return RGBA8(154, 205, 50);
    }

    static random() {
        let props = Object.entries(Object.getOwnPropertyDescriptors(SVG11))
                .filter(([key, descriptor]) => typeof descriptor.get === 'function')
                .map(([key, desc]) => key);
        return SVG11[props[Math.floor(Math.random() * props.length)]];
    }
}

function convertColourStop(stop) {
    if (typeof stop !== 'object')
        throw new TypeError("expected ColourStop object");

    const newStop = {};
    if (stop.colour instanceof Colour)
        newStop.colour = stop.colour.handle;
    else
        newStop.colour = stop.colour;
    newStop.position = stop.position;
    newStop.midpoint = stop.midpoint;
    if (newStop.midpoint == null)
        newStop.midpoint = 0.5;
    newStop.smoothness = stop.smoothness;
    return newStop;
}

class Gradient extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Gradient';
    }

    clone() {
        const gradientHandle = GradientApi.clone(this.handle);
        return new Gradient(gradientHandle);
    }

    static get default() {
        return new Gradient(GradientApi.createDefault());
    }
    
    static create(stops) {
        if (!stops)
            return new Gradient(GradientApi.createDefault());
        if (Array.isArray(stops)) {
            const newStops = [];
            for (const stop of stops) {
                newStops.push(convertColourStop(stop));
            }
            stops = newStops;
        }
        return new Gradient(GradientApi.create(stops));
    }

    get isGradient() {
        return true;
    }
    
    get stops() {
        const num = this.stopCount;
        let arr = [];
        for (let i = 0; i < num; ++i) {
            arr.push(this.getStop(i));
        }
        return arr;
    }
    
    getStop(index) {
        return GradientApi.getStop(this.handle, index);
    }
    
    get stopCount() {
        return GradientApi.getStopCount(this.handle);
    }
    
    get alpha() {
        return GradientApi.getAlpha(this.handle);
    }
    
    set alpha(value) {
        GradientApi.setAlpha(this.handle, value);
    }
        
    get hasNonFullAlpha() {
        return GradientApi.hasNonFullAlpha(this.handle);
    }
    
    get noise() {
        return GradientApi.getNoise(this.handle);
    }

    set noise(value) {
        GradientApi.setNoise(this.handle, value);
    }

    get hasNoise() {
        return GradientApi.hasNoise(this.handle);
    }
    
    get intensity() {
        return GradientApi.getIntensity(this.handle);
    }

    set intensity(value) {
        GradientApi.setIntensity(this.handle, value);
    }
    
    get tint() {
        return GradientApi.getTint(this.handle);
    }

    set tint(value) {
        GradientApi.setTint(this.handle, value);
    }
    
    get hasNonLinearMapping() {
        return GradientApi.hasNonLinearMapping(this.handle);
    }
}

class ColourProfile extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ColourProfile';
    }

    get isColourProfile() {
        return true;
    }
    
    get name() {
        return ColourProfileApi.getName(this.handle);
    }

    get isStandard() {
        return ColourProfileApi.isStandard(this.handle);
    }

    get isLinear() {
        return ColourProfileApi.isLinear(this.handle);
    }

    get colourSpace() {
        return ColourProfileApi.getColourSpace(this.handle);
    }

    get colourSpaceStr() {
        const cs = ColourProfileApi.getColourSpace(this.handle);
        if (cs >= ColourSpaceType.keys.length)
            throw new Error("Out of Range Error");
        return ColourSpaceType.keys[cs];
    }

    get version() {
        return ColourProfileApi.getVersion(this.handle);
    }

    get versionStr() {
        const ver = ColourProfileApi.getVersion(this.handle);
        const major = ver >> 8;
        const minor = (ver & 0x00f0) >> 4;
        const bugfix = ver & 0x000f;
        return major + "." + minor + "." + bugfix + ".0";
    }

    get deviceClass() {
        return ColourProfileApi.getDeviceClass(this.handle);
    }

    get deviceClassStr() {
        const deviceClass = ColourProfileApi.getDeviceClass(this.handle);
        switch (deviceClass)
        {
            case 0x73636E72:
                return "Input device";
            case 0x6D6E7472:
                return "Display device";
            case 0x70727472:
                return "Output device";
            case 0x6C696E6B:
                return "DeviceLink";
            case 0x73706163:
                return "ColorSpace";
            case 0x61627374:
                return "Abstract";
            case 0x6E6D636C:
                return "NamedColor";
            default:
                throw new Error("Unknown Device Class");
                return;
        }
    }

    canApplyTo(format) {
        return ColourProfileApi.canApplyTo(this.handle, format);
    }

    get approximateGamma() {
        return ColourProfileApi.getApproximateGamma(this.handle);
    }

    static find(name) {
        return new ColourProfile(ColourProfileApi.find(name));
    }
    
    static get profileCount() {
        return ColourProfileApi.getProfileCount();
    }
    
    static getProfile(index) {
        return new ColourProfile(ColourProfileApi.getProfile(index));
    }
    
    static getAll() {
        let profiles = [];
        ColourProfile.enumerateProfiles(profile => {
            profiles.push(profile);
            return EnumerationResult.Continue;
        });
        return profiles;
    }

    static getDefaultForColourSpace(colourSpace) {
        return new ColourProfile(ColourProfileApi.getDefaultForColourSpace(colourSpace));
    }
    
    static getDefaultForFormat(format) {
        return new ColourProfile(ColourProfileApi.getDefaultForFormat(format));
    }

    static enumerateProfiles(callback) {
        if (typeof callback === 'function') {
            function wrapped(profileHandle) {
                return callback(new ColourProfile(profileHandle));
            }
            return ColourProfileApi.enumerateProfiles(wrapped);
        }
        return ColourProfileApi.enumerateProfiles(callback);
    }
    
    static enumerateProfilesForFormat(format, callback) {
        if (typeof callback === 'function') {
            function wrapped(profileHandle) {
                return callback(new ColourProfile(profileHandle));
            }
            return ColourProfileApi.enumerateProfilesForFormat(format, wrapped);
        }
        return ColourProfileApi.enumerateProfilesForFormat(format, callback);
    }
    
    static enumerateProfilesForColourSpace(colourSpace, callback) {
        if (typeof callback === 'function') {
            function wrapped(profileHandle) {
                return callback(new ColourProfile(profileHandle));
            }
            return ColourProfileApi.enumerateProfilesForColourSpace(colourSpace, wrapped);
        }
        return ColourProfileApi.enumerateProfilesForColourSpace(colourSpace, callback);
    }

    static getProfilesForFormat(format) {
        let profiles = [];
        ColourProfile.enumerateProfilesForFormat(format, profile => {
            profiles.push(profile);
            return EnumerationResult.Continue;
        });
        return profiles;
    }

    static getProfilesForColourSpace(colourSpace) {
        let profiles = [];
        ColourProfile.enumerateProfilesForColourSpace(colourSpace, profile => {
            profiles.push(profile);
            return EnumerationResult.Continue;
        });
        return profiles;
    }
}

class ColourProfileSet extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ColourProfileSet';
    }

    get isColourProfileSet() {
        return true;
    }
    
    static get default() {
        return new ColourProfileSet(ColourProfileSetApi.createDefault());
    }
    
    static create() {
        return new ColourProfileSet(ColourProfileSetApi.createDefault());
    }

    getProfileForFormat(format) {
        return new ColourProfile(ColourProfileSetApi.getProfileForFormat(this.handle, format));
    }
    
    setProfileForFormat(format, colourProfile) {
        return ColourProfileSetApi.setProfileForFormat(this.handle, format, colourProfile.handle);
    }

    getProfileForColourSpaceType(colourSpaceType) {
        return new ColourProfile(ColourProfileSetApi.getProfileForColourSpaceType(this.handle, colourSpaceType));
    }
    
    setProfileForColourSpaceType(colourSpaceType, colourProfile) {
        return ColourProfileSetApi.setProfileForColourSpaceType(this.handle, colourSpaceType, colourProfile.handle);
    }

    get intent() {
        return ColourProfileSetApi.getIntent(this.handle);
    }
    
    set intent(value) {
        ColourProfileSetApi.setIntent(this.handle, value);
    }

    get blackPointCompensation() {
        return ColourProfileSetApi.getBlackPointCompensation(this.handle)
    }

    set blackPointCompensation(value) {
        ColourProfileSetApi.setBlackPointCompensation(this.handle, value)
    }
}

module.exports.Colour = Colour;
module.exports.Gradient = Gradient;
module.exports.ColourProfile = ColourProfile;
module.exports.ColourProfileSet = ColourProfileSet;
module.exports.ColourSpaceType = ColourSpaceType;
module.exports.RasterFormat = RasterFormat;
module.exports.RasterIntent = RasterIntent;
module.exports.SVG11 = SVG11;
module.exports.RGB8 = RGB8;
module.exports.RGBA8 = RGBA8;
module.exports.RGB16 = RGB16;
module.exports.RGBA16 = RGBA16;
module.exports.RGBAuf = RGBAuf;
module.exports.I8 = I8;
module.exports.IA8 = IA8;
module.exports.I16 = I16;
module.exports.IA16 = IA16;
module.exports.CMYK8 = CMYK8;
module.exports.CMYKA8 = CMYKA8;
module.exports.CMYKf = CMYKf;
module.exports.CMYKAf = CMYKAf;
module.exports.LAB16 = LAB16;
module.exports.LABA16 = LABA16;
module.exports.HSLf = HSLf;
module.exports.HSLAf = HSLAf;

// convenience
module.exports.RGB = RGBA8;
module.exports.IA = IA8;
module.exports.HSL = HSLAf;
