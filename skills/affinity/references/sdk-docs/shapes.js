'use strict';

const {
    //apis
    QRPayloadApi,
    QRPayloadEmailApi,
    QRPayloadFaceTimeApi,
    QRPayloadLocationApi,
    QRPayloadPhoneApi,
    QRPayloadSMSApi,
    QRPayloadTextApi,
    QRPayloadURLApi,
    QRPayloadVCardApi,
    QRPayloadWhatsAppApi,
    QRPayloadWifiApi,
    ShapeArrowApi,
    ShapeApi,
    ShapeCalloutEllipseApi,
    ShapeCalloutRectangleApi,
    ShapeCatApi,
    ShapeCat2Api,
    ShapeCat3Api,
    ShapeCat4Api,
    ShapeCloudApi,
    ShapeCogApi,
    ShapeCrescentApi,
    ShapeDiamondApi,
    ShapeDoubleStarApi,
    ShapeEllipseApi,
    ShapeHeartApi,
    ShapePieApi,
    ShapePolygonApi,
    ShapeQRCodeApi,
    ShapeRectangleApi,
    ShapeSegmentApi,
    ShapeSpiralApi,
    ShapeSquareStarApi,
    ShapeStarApi,
    ShapeTearApi,
    ShapeTrapezoidApi,
    ShapeTriangleApi,
    // enums
    QRPayloadType,
    ShapeArrowEndStyle,
    ShapeBoolParam,
    ShapeCornerIndex,
    ShapeCornerType,
    ShapeEnumParam,
    ShapeFloatParam,
    ShapeIntParam,
    ShapeMajorAxis,
    ShapeSpiralStyle,
    ShapeType,
    WifiEncryptionType,
} = require('affinity:geometry');
const { HandleObject } = require("./handleobject.js");

function createTypedQRPayload(payloadHandle) {
    if (payloadHandle == null)
        return null;
    const type = QRPayloadApi.getPayloadType(payloadHandle);
    switch (type.value) {
        case QRPayloadType.Email.value:
            return new QRPayloadEmail(QRPayloadEmailApi.fromPayload(payloadHandle));
        case QRPayloadType.FaceTime.value:
            return new QRPayloadFaceTime(QRPayloadFaceTimeApi.fromPayload(payloadHandle));
        case QRPayloadType.Location.value:
            return new QRPayloadLocation(QRPayloadLocationApi.fromPayload(payloadHandle));
        case QRPayloadType.Phone.value:
            return new QRPayloadPhone(QRPayloadPhoneApi.fromPayload(payloadHandle));
        case QRPayloadType.SMS.value:
            return new QRPayloadSMS(QRPayloadSMSApi.fromPayload(payloadHandle));
        case QRPayloadType.Text.value:
            return new QRPayloadText(QRPayloadTextApi.fromPayload(payloadHandle));
        case QRPayloadType.URL.value:
            return new QRPayloadURL(QRPayloadURLApi.fromPayload(payloadHandle));
        case QRPayloadType.VCard.value:
            return new QRPayloadVCard(QRPayloadVCardApi.fromPayload(payloadHandle));
        case QRPayloadType.WhatsApp.value:
            return new QRPayloadWhatsApp(QRPayloadWhatsAppApi.fromPayload(payloadHandle));
        case QRPayloadType.Wifi.value:
            return new QRPayloadWifi(QRPayloadWifiApi.fromPayload(payloadHandle));
    }
    return new QRPayload(payloadHandle);
}

class QRPayload extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayload';
    }

    clone() {
        return new QRPayload(QRPayloadApi.clone(this.handle));
    }

    get payloadType() {
        return QRPayloadApi.getPayloadType(this.handle);
    }

    get payloadString() {
        return QRPayloadApi.getPayloadString(this.handle);
    }

    get payloadDisplayString() {
        return QRPayloadApi.getPayloadDisplayString(this.handle);
    }

    get isPayloadValid() {
        return QRPayloadApi.isPayloadValid(this.handle);
    }

    clearPayload() {
        QRPayloadApi.clearPayload(this.handle);
    }

    static create(type) {
        return new QRPayload(QRPayloadApi.create(type));
    }

    static parse(payloadString) {
        return new QRPayload(QRPayloadApi.parse(payloadString));
    }
}

class QRPayloadEmail extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadEmail';
    }

    static create() {
        return new QRPayloadEmail(QRPayloadEmailApi.create());
    }

    clone() {
        return new QRPayloadEmail(QRPayloadEmailApi.clone(this.handle));
    }

    get address() {
        return QRPayloadEmailApi.getAddress(this.handle);
    }

    get subject() {
        return QRPayloadEmailApi.getSubject(this.handle);
    }

    get body() {
        return QRPayloadEmailApi.getBody(this.handle);
    }

    get isAddressValid() {
        return QRPayloadEmailApi.isAddressValid(this.handle);
    }

    set address(value) {
        return QRPayloadEmailApi.setAddress(this.handle, value);
    }

    set subject(value) {
        return QRPayloadEmailApi.setSubject(this.handle, value);
    }

    set body(value) {
        return QRPayloadEmailApi.setBody(this.handle, value);
    }
}

class QRPayloadFaceTime extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadFaceTime';
    }

    static create() {
        return new QRPayloadFaceTime(QRPayloadFaceTimeApi.create());
    }

    clone() {
        return new QRPayloadFaceTime(QRPayloadFaceTimeApi.clone(this.handle));
    }

    get recipient() {
        return QRPayloadFaceTimeApi.getRecipient(this.handle);
    }

    set recipient(value) {
        QRPayloadFaceTimeApi.setRecipient(this.handle, value);
    }
}

class QRPayloadLocation extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadLocation';
    }

    static create() {
        return new QRPayloadLocation(QRPayloadLocationApi.create());
    }

    clone() {
        return new QRPayloadLocation(QRPayloadLocationApi.clone(this.handle));
    }

    get latitude() {
        return QRPayloadLocationApi.getLatitude(this.handle);
    }

    get longitude() {
        return QRPayloadLocationApi.getLongitude(this.handle);
    }

    get elevation() {
        return QRPayloadLocationApi.getElevation(this.handle);
    }

    get isLatitudeValid() {
        return QRPayloadLocationApi.isLatitudeValid(this.handle);
    }

    get isLongitudeValid() {
        return QRPayloadLocationApi.isLongitudeValid(this.handle);
    }

    get isElevationValid() {
        return QRPayloadLocationApi.isElevationValid(this.handle);
    }

    set latitude(value) {
        return QRPayloadLocationApi.setLatitude(this.handle, value);
    }

    set longitude(value) {
        return QRPayloadLocationApi.setLongitude(this.handle, value);
    }

    set elevation(value) {
        return QRPayloadLocationApi.setElevation(this.handle, value);
    }
}

class QRPayloadPhone extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadPhone';
    }

    static create() {
        return new QRPayloadPhone(QRPayloadPhoneApi.create());
    }

    clone() {
        return new QRPayloadPhone(QRPayloadPhoneApi.clone(this.handle));
    }

    get number() {
        return QRPayloadPhoneApi.getNumber(this.handle);
    }

    set number(value) {
        QRPayloadPhoneApi.setNumber(this.handle, value);
    }
}

class QRPayloadSMS extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadSMS';
    }

    static create() {
        return new QRPayloadSMS(QRPayloadSMSApi.create());
    }

    clone() {
        return new QRPayloadSMS(QRPayloadSMSApi.clone(this.handle));
    }

    get content() {
        return QRPayloadSMSApi.getContent(this.handle);
    }

    get number() {
        return QRPayloadSMSApi.getNumber(this.handle);
    }

    get isNumberValid() {
        return QRPayloadSMSApi.isNumberValid(this.handle);
    }

    set content(value) {
        QRPayloadSMSApi.setContent(this.handle, value);
    }

    set number(value) {
        QRPayloadSMSApi.setNumber(this.handle, value);
    }
}

class QRPayloadText extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadText';
    }

    static create() {
        return new QRPayloadText(QRPayloadTextApi.create());
    }

    clone() {
        return new QRPayloadText(QRPayloadTextApi.clone(this.handle));
    }

    get text() {
        return QRPayloadTextApi.getText(this.handle);
    }

    set text(value) {
        QRPayloadTextApi.setText(this.handle, value);
    }
}

class QRPayloadURL extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadURL';
    }

    static create() {
        return new QRPayloadURL(QRPayloadURLApi.create());
    }

    clone() {
        return new QRPayloadURL(QRPayloadURLApi.clone(this.handle));
    }

    get url() {
        return QRPayloadURLApi.getURL(this.handle);
    }

    get isURLValid() {
        return QRPayloadURLApi.isURLValid(this.handle);
    }

    set url(value) {
        QRPayloadURLApi.setURL(this.handle, value);
    }
}

class QRPayloadVCard extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadVCard';
    }

    static create() {
        return new QRPayloadVCard(QRPayloadVCardApi.create());
    }

    clone() {
        return new QRPayloadVCard(QRPayloadVCardApi.clone(this.handle));
    }

    getpPrefixes() {
        return QRPayloadVCardApi.getPrefixes(this.handle);
    }

    get firstName() {
        return QRPayloadVCardApi.getFirstName(this.handle);
    }

    get lastName() {
        return QRPayloadVCardApi.getLastName(this.handle);
    }

    get suffixes() {
        return QRPayloadVCardApi.getSuffixes(this.handle);
    }

    get phone() {
        return QRPayloadVCardApi.getPhone(this.handle);
    }

    get email() {
        return QRPayloadVCardApi.getEmail(this.handle);
    }

    get website() {
        return QRPayloadVCardApi.getWebsite(this.handle);
    }

    get company() {
        return QRPayloadVCardApi.getCompany(this.handle);
    }

    get jobTitle() {
        return QRPayloadVCardApi.getJobTitle(this.handle);
    }

    get birthday() {
        return QRPayloadVCardApi.getBirthday(this.handle);
    }

    get streetAddress() {
        return QRPayloadVCardApi.getStreetAddress(this.handle);
    }

    get city() {
        return QRPayloadVCardApi.getCity(this.handle);
    }

    get postalCode() {
        return QRPayloadVCardApi.getPostalCode(this.handle);
    }

    get region() {
        return QRPayloadVCardApi.getRegion(this.handle);
    }

    get country() {
        return QRPayloadVCardApi.getCountry(this.handle);
    }

    get notes() {
        return QRPayloadVCardApi.getNotes(this.handle);
    }

    get isFullNameValid() {
        return QRPayloadVCardApi.isFullNameValid(this.handle);
    }

    get isFirstNameValid() {
        return QRPayloadVCardApi.isFirstNameValid(this.handle);
    }

    get isLastNameValid() {
        return QRPayloadVCardApi.isLastNameValid(this.handle);
    }

    get isEmailValid() {
        return QRPayloadVCardApi.isEmailValid(this.handle);
    }

    get isWebsiteValid() {
        return QRPayloadVCardApi.isWebsiteValid(this.handle);
    }

    set prefixes(value) {
        QRPayloadVCardApi.setPrefixes(this.handle, value);
    }

    set firstName(value) {
        QRPayloadVCardApi.setFirstName(this.handle, value);
    }

    set lastName(value) {
        QRPayloadVCardApi.setLastName(this.handle, value);
    }

    set suffixes(value) {
        QRPayloadVCardApi.setSuffixes(this.handle, value);
    }

    set phone(value) {
        QRPayloadVCardApi.setPhone(this.handle, value);
    }

    set email(value) {
        QRPayloadVCardApi.setEmail(this.handle, value);
    }

    set website(value) {
        QRPayloadVCardApi.setWebsite(this.handle, value);
    }

    set company(value) {
        QRPayloadVCardApi.setCompany(this.handle, value);
    }

    set jobTitle(value) {
        QRPayloadVCardApi.setJobTitle(this.handle, value);
    }

    set birthday(value) {
        QRPayloadVCardApi.setBirthday(this.handle, value);
    }

    set streetAddress(value) {
        QRPayloadVCardApi.setStreetAddress(this.handle, value);
    }

    set city(value) {
        QRPayloadVCardApi.setCity(this.handle, value);
    }

    set postalCode(value) {
        QRPayloadVCardApi.setPostalCode(this.handle, value);
    }

    set region(value) {
        QRPayloadVCardApi.setRegion(this.handle, value);
    }

    set country(value) {
        QRPayloadVCardApi.setCountry(this.handle, value);
    }

    set notes(value) {
        QRPayloadVCardApi.setNotes(this.handle, value);
    }
}

class QRPayloadWhatsApp extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadWhatsApp';
    }

    static create() {
        return new QRPayloadWhatsApp(QRPayloadWhatsAppApi.create());
    }

    clone() {
        return new QRPayloadWhatsApp(QRPayloadWhatsAppApi.clone(this.handle));
    }

    get content() {
        return QRPayloadWhatsAppApi.getContent(this.handle);
    }

    get number() {
        return QRPayloadWhatsAppApi.getNumber(this.handle);
    }

    set content(value) {
        return QRPayloadWhatsAppApi.setContent(this.handle, value);
    }

    set number(value) {
        return QRPayloadWhatsAppApi.setNumber(this.handle, value);
    }
}

class QRPayloadWifi extends QRPayload {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'QRPayloadWifi';
    }

    static create() {
        return new QRPayloadWifi(QRPayloadWifiApi.create());
    }

    clone() {
        return new QRPayloadWifi(QRPayloadWifiApi.clone(this.handle));
    }

    get ssid() {
        return QRPayloadWifiApi.getSSID(this.handle);
    }

    get password() {
        return QRPayloadWifiApi.getPassword(this.handle);
    }

    get encryption() {
        return QRPayloadWifiApi.getEncryption(this.handle);
    }

    get hidden() {
        return QRPayloadWifiApi.getHidden(this.handle);
    }

    get isSSIDValid() {
        return QRPayloadWifiApi.isSSIDValid(this.handle);
    }

    set ssid(value) {
        return QRPayloadWifiApi.setSSID(this.handle, value);
    }

    set password(value) {
        return QRPayloadWifiApi.setPassword(this.handle, value);
    }

    set encryption(value) {
        return QRPayloadWifiApi.setEncryption(this.handle, value);
    }

    set hidden(value) {
        return QRPayloadWifiApi.setHidden(this.handle, value);
    }
}

class Shape extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Shape';
    }

    static create(shapeType) {
        return createTypedShape(ShapeApi.create(shapeType));
    }

    get shapeType() {
        return ShapeApi.getShapeType(this.handle);
    }

    get displayName() {
        return ShapeApi.getDisplayName(this.handle);
    }

    get majorAxis() {
        return ShapeApi.getMajorAxis(this.handle);
    }

    get isAffectedByScale() {
        return ShapeApi.isAffectedByScale(this.handle);
    }

    getCurves(bounds, transform = null) {
        return ShapeApi.getCurves(this.handle, bounds, transform);
    }

    get rotationOrder() {
        return ShapeApi.getRotationOrder(this.handle);
    }

    getTransformedBounds(bounds, xf) {
        return ShapeApi.getTransformedBounds(this.handle, bounds, xf);
    }

    clone() {
        return createTypedShape(ShapeApi.clone(this.handle));
    }

    static getTypeBaseType(shapeType) {
        return ShapeApi.getTypeBaseType(shapeType);
    }

    static getTypeDisplayName(shapeType) {
        return ShapeApi.getTypeDisplayName(shapeType);
    }
}


class ShapeArrowLeftEndProxy extends HandleObject {
    constructor(shapeArrowHandle) {
        super(shapeArrowHandle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeArrowLeftEndProxy';
    }

    get style() {
        return ShapeArrowApi.getLeftEndStyle(this.handle);
    }

    get length() {
        return ShapeArrowApi.getLeftLength(this.handle);
    }

    get innerOffset() {
        return ShapeArrowApi.getLeftInnerOffset(this.handle);
    }

    get isProportional() {
        return ShapeArrowApi.getLeftIsProportional(this.handle);
    }

    set style(value) {
        ShapeArrowApi.setLeftEndStyle(this.handle, value);
    }

    setLength(value, width, height) {
        ShapeArrowApi.setLeftLength(this.handle, value, width, height);
    }

    setInnerOffset(value, width, height) {
        ShapeArrowApi.setLeftInnerOffset(this.handle, value, width, height);
    }

    setIsProportional(value, width, height) {
        ShapeArrowApi.setLeftIsProportional(this.handle, value, width, height);
    }

    assign(src, width, height) {
        const style = src.style;
        const length = src.length;
        const innerOffset = src.innerOffset;
        const isProportional = src.isProportional;

        if (style != null) {
            this.style = style;
        }
        
        if (length != null) {
            this.setLength(length, width, height);
        }
        
        if (innerOffset != null) {
            this.setInnerOffset(innerOffset, width, height);
        }

        if (isProportional != null) {
            this.setIsProportional(isProportional, width, height);
        }
    }
}

class ShapeArrowRightEndProxy extends HandleObject {
    constructor(shapeArrowHandle) {
        super(shapeArrowHandle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeArrowRightEndProxy';
    }

    get style() {
        return ShapeArrowApi.getRightEndStyle(this.handle);
    }

    get length() {
        return ShapeArrowApi.getRightLength(this.handle);
    }

    get innerOffset() {
        return ShapeArrowApi.getRightInnerOffset(this.handle);
    }

    get isProportional() {
        return ShapeArrowApi.getRightIsProportional(this.handle);
    }

    set style(value) {
        ShapeArrowApi.setRightEndStyle(this.handle, value);
    }

    setLength(value, width, height) {
        ShapeArrowApi.setRightLength(this.handle, value, width, height);
    }

    setInnerOffset(value, width, height) {
        ShapeArrowApi.setRightInnerOffset(this.handle, value, width, height);
    }

    setIsProportional(value, width, height) {
        ShapeArrowApi.setRightIsProportional(this.handle, value, width, height);
    }

    assign(src, width, height) {
        const style = src.style;
        const length = src.length;
        const innerOffset = src.innerOffset;
        const isProportional = src.isProportional;

        if (style != null) {
            this.style = style;
        }
        
        if (length != null) {
            this.setLength(length, width, height);
        }
        
        if (innerOffset != null) {
            this.setInnerOffset(innerOffset, width, height);
        }

        if (isProportional != null) {
            this.setIsProportional(isProportional, width, height);
        }
    }
}


class ShapeArrow extends Shape {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeArrow';
    }

    static create() {
        return new ShapeArrow(ShapeArrowApi.create());
    }

    clone() {
        return new ShapeArrow(ShapeArrowApi.clone(this.handle));
    }

    #leftEnd
    get leftEnd() {
        if (!this.#leftEnd)
            this.#leftEnd = new ShapeArrowLeftEndProxy(this.handle);
        return this.#leftEnd;
    }

    #rightEnd
    get rightEnd() {
        if (!this.#rightEnd)
            this.#rightEnd = new ShapeArrowRightEndProxy(this.handle);
        return this.#rightEnd;
    }

    get thickness() {
        return ShapeArrowApi.getThickness(this.handle);
    }

    setLeftEnd(value, width, height) {
        this.leftEnd.assign(value, width, height);
    }

    setRightEnd(value, width, height) {
        this.rightEnd.assign(value, width, height);
    }

    set thickness(value) {
        ShapeArrowApi.setThickness(this.handle, value);
    }
}


class ShapeCalloutEllipseTail extends HandleObject {
    constructor(shapeHandle) {
        super(shapeHandle)
    }

    get angle() {
        return ShapeCalloutEllipseApi.getTailAngle(this.handle);
    }

    get endPosition() {
        return ShapeCalloutEllipseApi.getTailEndPosition(this.handle);
    }

    get height() {
        return ShapeCalloutEllipseApi.getTailHeight(this.handle);
    }

    set angle(value) {
        ShapeCalloutEllipseApi.setTailAngle(this.handle, value);
    }

    set endPosition(value) {
        ShapeCalloutEllipseApi.setTailEndPosition(this.handle, value);
    }

    set height(value) {
        ShapeCalloutEllipseApi.setTailHeight(this.handle, value);
    }

    assign(src) {
        const angle = src.angle;
        if (angle != null) {
            this.angle = angle;
        }
        const endPosition = src.endPosition;
        if (endPosition != null) {
            this.endPosition = endPosition;
        }
        const height = src.height;
        if (height != null) {
            this.height = height;
        }
    }
}


class ShapeCalloutEllipse extends Shape {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeCalloutEllipse';
    }

    static create() {
        return new ShapeCalloutEllipse(ShapeCalloutEllipseApi.create());
    }

    clone() {
        return new ShapeCalloutEllipse(ShapeCalloutEllipseApi.clone(this.handle));
    }

    get absoluteSizes() {
        return ShapeCalloutEllipseApi.getAbsoluteSizes(this.handle);
    }

    setAbsoluteSizes(value, boundsWidth, boundsHeight) {
        ShapeCalloutEllipseApi.setAbsoluteSizes(this.handle, value, boundsWidth, boundsHeight);
    }

    #tail;
    get tail() {
        if (!this.#tail)
            this.#tail = new ShapeCalloutEllipseTail(this.handle);
        return this.#tail;
    }

    set tail(value) {
        this.tail.assign(value);
    }
}


class ShapeCalloutRectangleTailProxy extends HandleObject {
    constructor(shapeCalloutRectangleHandle) {
        super(shapeCalloutRectangleHandle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeCalloutRectangleTailProxy';
    }

    get startPosition() {
        return ShapeCalloutRectangleApi.getTailPosition(this.handle)
    }

    get endPosition() {
        return ShapeCalloutRectangleApi.getTailEndPosition(this.handle)
    }

    get width() {
        return ShapeCalloutRectangleApi.getTailWidth(this.handle)
    }

    get height() {
        return ShapeCalloutRectangleApi.getTailHeight(this.handle)
    }

    set startPosition(value) {
        ShapeCalloutRectangleApi.setTailPosition(this.handle, value)
    }

    set endPosition(value) {
        ShapeCalloutRectangleApi.setTailEndPosition(this.handle, value)
    }

    set width(value) {
        ShapeCalloutRectangleApi.setTailWidth(this.handle, value)
    }

    set height(value) {
        ShapeCalloutRectangleApi.setTailHeight(this.handle, value)
    }

    assign(src) {
        const startPosition = src.startPosition;
        const endPosition = src.endPosition;
        const width = src.width;
        const height = src.height;

        if (startPosition != null) {
            this.startPosition = startPosition;
        }
        
        if (endPosition != null) {
            this.endPosition = endPosition;
        }
        
        if (width != null) {
            this.width = width;
        }
        
        if (height != null) {
            this.height = height;
        }
    }
}


class ShapeCalloutRectangle extends Shape {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeCalloutRectangle';
    }

    static create() {
        return new ShapeCalloutRectangle(ShapeCalloutRectangleApi.create());
    }

    clone() {
        return new ShapeCalloutRectangle(ShapeCalloutRectangleApi.clone(this.handle));
    }

    getCornerRadius(cornerIndex) {
        return ShapeCalloutRectangleApi.getCornerRadius(this.handle, cornerIndex);
    }

    get absoluteSizes() {
        return ShapeCalloutRectangleApi.getAbsoluteSizes(this.handle);
    }

    get useSingleRadius() {
        return ShapeCalloutRectangleApi.getUseSingleRadius(this.handle);
    }

    #tail;
    get tail() {
        if (!this.#tail)
            this.#tail = new ShapeCalloutRectangleTailProxy(this.handle);
        return this.#tail;
    }

    setCornerRadius(cornerIndex, radius, boundsWidth, boundsHeight) {
        ShapeCalloutRectangleApi.setCornerRadius(this.handle, cornerIndex, radius, boundsWidth, boundsHeight);
    }
    
    setAbsoluteSizes(value, width, height) {
        ShapeCalloutRectangleApi.setAbsoluteSizes(this.handle, value, width, height);
    }

    set tail(value) {
        this.tail.assign(value);
    }

    set useSingleRadius(value) {
        ShapeCalloutRectangleApi.setUseSingleRadius(this.handle, value);
    }
}


class ShapeCat extends Shape {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeCat';
    }

    static create() {
        return new ShapeCat(ShapeCatApi.create());
    }

    clone() {
        return new ShapeCat(ShapeCatApi.clone(this.handle));
    }
}


class ShapeCat2 extends Shape {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeCat2';
    }

    static create() {
        return new ShapeCat2(ShapeCat2Api.create());
    }

    clone() {
        return new ShapeCat2(ShapeCat2Api.clone(this.handle));
    }
}


class ShapeCat3 extends Shape {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeCat3';
    }

    static create() {
        return new ShapeCat3(ShapeCat3Api.create());
    }

    clone() {
        return new ShapeCat3(ShapeCat3Api.clone(this.handle));
    }
}


class ShapeCat4 extends Shape {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeCat4';
    }

    static create() {
        return new ShapeCat4(ShapeCat4Api.create());
    }

    clone() {
        return new ShapeCat4(ShapeCat4Api.clone(this.handle));
    }
}


class ShapeCloud extends Shape {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeCloud';
    }

    static create() {
        return new ShapeCloud(ShapeCloudApi.create());
    }

    clone() {
        return new ShapeCloud(ShapeCloudApi.clone(this.handle));
    }

    get bubbles() {
        return ShapeCloudApi.getBubbleCount(this.handle);
    }

    get innerRadius() {
        return ShapeCloudApi.getInnerRadius(this.handle);
    }

    set bubbles(value) {
        ShapeCloudApi.setBubbleCount(this.handle, value);
    }

    set innerRadius(value) {
        ShapeCloudApi.setInnerRadius(this.handle, value);
    }
}


class ShapeCog extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeCog';
    }

    static create() {
        return new ShapeCog(ShapeCogApi.create());
    }

    clone() {
        return new ShapeCog(ShapeCogApi.clone(this.handle));
    }

    get innerRadius() {
        return ShapeCogApi.getInnerRadius(this.handle);
    }

    get holeRadius() {
        return ShapeCogApi.getHoleRadius(this.handle);
    }

    get toothSize() {
        return ShapeCogApi.getToothSize(this.handle);
    }

    get notchSize() {
        return ShapeCogApi.getNotchSize(this.handle);
    }

    get curvature() {
        return ShapeCogApi.getCurvature(this.handle);
    }

    get teeth() {
        return ShapeCogApi.getToothCount(this.handle);
    }

    set innerRadius(value) {
        ShapeCogApi.setInnerRadius(this.handle, value);
    }

    set holeRadius(value) {
        ShapeCogApi.setHoleRadius(this.handle, value);
    }

    set toothSize(value) {
        ShapeCogApi.setToothSize(this.handle, value);
    }

    set notchSize(value) {
        ShapeCogApi.setNotchSize(this.handle, value);
    }

    set curvature(value) {
        ShapeCogApi.setCurvature(this.handle, value);
    }

    set teeth(value) {
        ShapeCogApi.setToothCount(this.handle, value);
    }
}


class ShapeCrescent extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeCrescent';
    }

    static create() {
        return new ShapeCrescent(ShapeCrescentApi.create());
    }

    clone() {
        return new ShapeCrescent(ShapeCrescentApi.clone(this.handle));
    }

    get leftArc() {
        return ShapeCrescentApi.getArcLeft(this.handle);
    }

    get rightArc() {
        return ShapeCrescentApi.getArcRight(this.handle);
    }

    set leftArc(value) {
        ShapeCrescentApi.setArcLeft(this.handle, value);
    }

    set rightArc(value) {
        ShapeCrescentApi.setArcRight(this.handle, value);
    }
}


class ShapeDiamond extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeDiamond';
    }

    static create() {
        return new ShapeDiamond(ShapeDiamondApi.create());
    }

    clone() {
        return new ShapeDiamond(ShapeDiamondApi.clone(this.handle));
    }

    get position() {
        return ShapeDiamondApi.getPosition(this.handle);
    }

    set position(value) {
        ShapeDiamondApi.setPosition(this.handle, value);
    }
}


class ShapeDoubleStar extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeDoubleStar';
    }

    static create() {
        return new ShapeDoubleStar(ShapeDoubleStarApi.create());
    }

    clone() {
        return new ShapeDoubleStar(ShapeDoubleStarApi.clone(this.handle));
    }

    get innerRadius() {
        return ShapeDoubleStarApi.getInnerRadius(this.handle);
    }

    get pointRadius() {
        return ShapeDoubleStarApi.getPointRadius(this.handle);
    }

    get points() {
        return ShapeDoubleStarApi.getPointCount(this.handle);
    }

    set innerRadius(value) {
        ShapeDoubleStarApi.setInnerRadius(this.handle, value);
    }

    set pointRadius(value) {
        ShapeDoubleStarApi.setPointRadius(this.handle, value);
    }

    set points(value) {
        ShapeDoubleStarApi.setPointCount(this.handle, value);
    }
}


class ShapeEllipse extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeEllipse';
    }

    static create() {
        return new ShapeEllipse(ShapeEllipseApi.create());
    }

    clone() {
        return new ShapeEllipse(ShapeEllipseApi.clone(this.handle));
    }
}


class ShapeHeart extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeHeart';
    }

    static create() {
        return new ShapeHeart(ShapeHeartApi.create());
    }

    clone() {
        return new ShapeHeart(ShapeHeartApi.clone(this.handle));
    }

    get spread() {
        return ShapeHeartApi.getSpread(this.handle);
    }

    set spread(value) {
        ShapeHeartApi.setSpread(this.handle, value);
    }
}

class ShapePie extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapePie';
    }

    static create() {
        return new ShapePie(ShapePieApi.create());
    }

    clone() {
        return new ShapePie(ShapePieApi.clone(this.handle));
    }

    get innerRadius() {
        return ShapePieApi.getInnerRadius(this.handle);
    }

    get startAngle() {
        return ShapePieApi.getStartAngle(this.handle);
    }

    get endAngle() {
        return ShapePieApi.getEndAngle(this.handle);
    }

    get sweep() {
        return ShapePieApi.getSweep(this.handle);
    }

    set innerRadius(value) {
        ShapePieApi.setInnerRadius(this.handle, value);
    }

    set startAngle(value) {
        ShapePieApi.setStartAngle(this.handle, value);
    }

    set endAngle(value) {
        ShapePieApi.setEndAngle(this.handle, value);
    }

    set sweep(value) {
        ShapePieApi.setSweep(this.handle, value);
    }

    get isClosed() {
        return ShapePieApi.getIsClosed(this.handle);
    }

    closePie() {
        ShapePieApi.closePie(this.handle);
    }
}


class ShapePolygon extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapePolygon';
    }

    static create() {
        return new ShapePolygon(ShapePolygonApi.create());
    }

    clone() {
        return new ShapePolygon(ShapePolygonApi.clone(this.handle));
    }

    get curve() {
        return ShapePolygonApi.getCurve(this.handle);
    }

    get sides() {
        return ShapePolygonApi.getSideCount(this.handle);
    }

    get smoothPoints() {
        return ShapePolygonApi.getSmoothPoints(this.handle);
    }

    get minCurve() {    // read-only
        return ShapePolygonApi.getMinCurve(this.handle);
    }

    set curve(value) {
        ShapePolygonApi.setCurve(this.handle, value);
    }

    set sides(value) {
        ShapePolygonApi.setSideCount(this.handle, value);
    }

    set smoothPoints(value) {
        ShapePolygonApi.setSmoothPoints(this.handle, value);
    }
}

class ShapeRectangleCornerProxy extends HandleObject {
    #cornerIndex;
    constructor(shapeRectangleHandle, cornerIndex) {
        super(shapeRectangleHandle);
        this.#cornerIndex = cornerIndex;
    }

    get [Symbol.toStringTag]() {
        return 'ShapeRectangleCornerProxy';
    }

    get radius() {
        return ShapeRectangleApi.getCornerRadius(this.handle, this.#cornerIndex);
    }

    get cornerType() {
        return ShapeRectangleApi.getCornerType(this.handle, this.#cornerIndex);
    }

    setRadius(value, width, height) {
        ShapeRectangleApi.setCornerRadius(this.handle, this.#cornerIndex, value, width, height);
    }

    set cornerType(value) {
        ShapeRectangleApi.setCornerType(this.handle, this.#cornerIndex, value);
    }

    assign(src, width, height) {
        const radius = src.radius;
        const cornerType = src.cornerType;

        if (radius != null) {
            this.setRadius(radius, width, height);
        }

        if (cornerType != null) {
            this.cornerType = cornerType;
        }
    }
}

class ShapeRectangle extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeRectangle';
    }

    static create() {
        return new ShapeRectangle(ShapeRectangleApi.create());
    }

    clone() {
        return new ShapeRectangle(ShapeRectangleApi.clone(this.handle));
    }

    #topLeft;
    get topLeft() {
        if (!this.#topLeft)
            this.#topLeft = new ShapeRectangleCornerProxy(this.handle, ShapeCornerIndex.TopLeft);
        return this.#topLeft;
    }

    #topRight;
    get topRight() {
        if (!this.#topRight)
            this.#topRight = new ShapeRectangleCornerProxy(this.handle, ShapeCornerIndex.TopRight);
        return this.#topRight;
    }

    #bottomLeft;
    get bottomLeft() {
        if (!this.#bottomLeft)
            this.#bottomLeft = new ShapeRectangleCornerProxy(this.handle, ShapeCornerIndex.BottomLeft);
        return this.#bottomLeft;
    }

    #bottomRight;
    get bottomRight() {
        if (!this.#bottomRight)
            this.#bottomRight = new ShapeRectangleCornerProxy(this.handle, ShapeCornerIndex.BottomRight);
        return this.#bottomRight;
    }

    get isPlainRectangle() {
        return ShapeRectangleApi.isPlainRectangle(this.handle);
    }

    get absoluteSizes() {
        return ShapeRectangleApi.getAbsoluteSizes(this.handle);
    }

    get useSingleRadius() {
        return ShapeRectangleApi.getUseSingleRadius(this.handle);
    }

    setTopLeft(value, width, height) {
        this.topLeft.assign(value, width, height);
    }

    setTopRight(value, width, height) {
        this.topRight.assign(value, width, height);
    }

    setBottomLeft(value, width, height) {
        this.bottomLeft.assign(value, width, height);
    }

    setBottomRight(value, width, height) {
        this.bottomRight.assign(value, width, height);
    }

    setAbsoluteSizes(value, width, height) {
        ShapeRectangleApi.setAbsoluteSizes(this.handle, value, width, height);
    }

    set useSingleRadius(value) {
        return ShapeRectangleApi.setUseSingleRadius(this.handle, value);
    }
}


class ShapeSegment extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeSegment';
    }

    static create() {
        return new ShapeSegment(ShapeSegmentApi.create());
    }

    clone() {
        return new ShapeSegment(ShapeSegmentApi.clone(this.handle));
    }

    get angle() {
        return ShapeSegmentApi.getAngle(this.handle);
    }

    get lowerLine() {
        return ShapeSegmentApi.getLowerLine(this.handle);
    }

    get upperLine() {
        return ShapeSegmentApi.getUpperLine(this.handle);
    }

    set angle(value) {
        ShapeSegmentApi.setAngle(this.handle, value);
    }

    set lowerLine(value) {
        ShapeSegmentApi.setLowerLine(this.handle, value);
    }

    set upperLine(value) {
        ShapeSegmentApi.setUpperLine(this.handle, value);
    }
}

class ShapeSpiral extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeSpiral';
    }

    static create() {
        return new ShapeSpiral(ShapeSpiralApi.create());
    }

    clone() {
        return new ShapeSpiral(ShapeSpiralApi.clone(this.handle));
    }

    get style() {
        return ShapeSpiralApi.getStyle(this.handle);
    }

    get flip() {
        return ShapeSpiralApi.getFlip(this.handle);
    }

    get turns() {
        return ShapeSpiralApi.getTurns(this.handle);
    }

    get partTurn() {
        return ShapeSpiralApi.getPartTurn(this.handle);
    }

    get decay() {
        return ShapeSpiralApi.getDecay(this.handle);
    }

    get segmentAngle() {
        return ShapeSpiralApi.getSegmentAngle(this.handle);
    }

    get divisions() {
        return ShapeSpiralApi.getDivisions(this.handle);
    }

    get innerRadius() {
        return ShapeSpiralApi.getInnerRadius(this.handle);
    }

    get decayPerSegment() {
        return ShapeSpiralApi.getDecayPerSegment(this.handle);
    }

    get cusped() {
        return ShapeSpiralApi.getCusped(this.handle);
    }

    get choke() {
        return ShapeSpiralApi.getChoke(this.handle);
    }

    get capChoke() {
        return ShapeSpiralApi.getCapChoke(this.handle);
    }

    get bias() {
        return ShapeSpiralApi.getBias(this.handle);
    }

    set style(value) {
        ShapeSpiralApi.setStyle(this.handle, value);
    }

    set flip(value) {
        ShapeSpiralApi.setFlip(this.handle, value);
    }

    set turns(value) {
        ShapeSpiralApi.setTurns(this.handle, value);
    }

    set partTurn(value) {
        ShapeSpiralApi.setPartTurn(this.handle, value);
    }

    set decay(value) {
        ShapeSpiralApi.setDecay(this.handle, value);
    }

    set segmentAngle(value) {
        ShapeSpiralApi.setSegmentAngle(this.handle, value);
    }

    set divisions(value) {
        ShapeSpiralApi.setDivisions(this.handle, value);
    }

    set innerRadius(value) {
        ShapeSpiralApi.setInnerRadius(this.handle, value);
    }

    set decayPerSegment(value) {
        ShapeSpiralApi.setDecayPerSegment(this.handle, value);
    }

    set cusped(value) {
        ShapeSpiralApi.setCusped(this.handle, value);
    }

    set choke(value) {
        ShapeSpiralApi.setChoke(this.handle, value);
    }

    set capChoke(value) {
        ShapeSpiralApi.setCapChoke(this.handle, value);
    }

    set bias(value) {
        ShapeSpiralApi.setBias(this.handle, value);
    }
}

class ShapeSquareStar extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeSquareStar';
    }

    static create() {
        return new ShapeSquareStar(ShapeSquareStarApi.create());
    }

    clone() {
        return new ShapeSquareStar(ShapeSquareStarApi.clone(this.handle));
    }

    get sides() {
        return ShapeSquareStarApi.getSideCount(this.handle);
    }

    get cutout() {
        return ShapeSquareStarApi.getCutout(this.handle);
    }

    set sides(value) {
        ShapeSquareStarApi.setSideCount(this.handle, value);
    }

    set cutout(value) {
        ShapeSquareStarApi.setCutout(this.handle, value);
    }
}


class ShapeStar extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeStar';
    }

    static create() {
        return new ShapeStar(ShapeStarApi.create());
    }

    clone() {
        return new ShapeStar(ShapeStarApi.clone(this.handle));
    }

    get maxInnerRadius() { // read-only
        return ShapeStarApi.getMaxCircleInnerRadius(this.handle);
    }

    get innerRadius() {
        return ShapeStarApi.getInnerRadius(this.handle);
    }

    get leftCurve() {
        return ShapeStarApi.getLeftCurve(this.handle);
    }

    get rightCurve() {
        return ShapeStarApi.getRightCurve(this.handle);
    }

    get circleInnerRadius() {
        return ShapeStarApi.getCircleInnerRadius(this.handle);
    }

    get circleOuterRadius() {
        return ShapeStarApi.getCircleOuterRadius(this.handle);
    }

    get points() {
        return ShapeStarApi.getPointCount(this.handle);
    }

    get curvedEdges() {
        return ShapeStarApi.getCurvedEdges(this.handle);
    }

    set innerRadius(value) {
        return ShapeStarApi.setInnerRadius(this.handle, value);
    }

    set leftCurve(value) {
        return ShapeStarApi.setLeftCurve(this.handle, value);
    }

    set rightCurve(value) {
        return ShapeStarApi.setRightCurve(this.handle, value);
    }

    set circleInnerRadius(value) {
        return ShapeStarApi.setCircleInnerRadius(this.handle, value);
    }

    set circleOuterRadius(value) {
        return ShapeStarApi.setCircleOuterRadius(this.handle, value);
    }

    set points(value) {
        return ShapeStarApi.setPointCount(this.handle, value);
    }

    set curvedEdges(value) {
        return ShapeStarApi.setCurvedEdges(this.handle, value);
    }
}



class ShapeTearBallProxy extends HandleObject {
    constructor(shapeTearHandle) {
        super(shapeTearHandle);
    }

    get size() {
        return ShapeTearApi.getBallSize(this.handle);
    }

    get fixedSize() {
        return ShapeTearApi.getFixedBallSize(this.handle);
    }

    set size(value) {
        ShapeTearApi.setBallSize(this.handle, value);
    }

    set fixedSize(value) {
        ShapeTearApi.setFixedBallSize(this.handle, value);
    }

    assign(src) {
        const size = src.size;
        const fixedSize = src.fixedSize;

        if (size != null) {
            this.size = size;
        }

        if (fixedSize != null) {
            this.fixedSize = fixedSize;
        }
    }
}


class ShapeTear extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeTear';
    }

    static create() {
        return new ShapeTear(ShapeTearApi.create());
    }

    clone() {
        return new ShapeTear(ShapeTearApi.clone(this.handle));
    }

    #ball;
    get ball() {
        if (!this.#ball)
            this.#ball = new ShapeTearBallProxy(this.handle);
        return this.#ball;
    }

    get curve() {
        return ShapeTearApi.getCurve(this.handle);
    }

    get bend() {
        return ShapeTearApi.getBend(this.handle);
    }

    get tailPosition() {
        return ShapeTearApi.getTailPosition(this.handle);
    }

    set curve(value) {
        ShapeTearApi.setCurve(this.handle, value);
    }

    set bend(value) {
        ShapeTearApi.setBend(this.handle, value);
    }

    set tailPosition(value) {
        ShapeTearApi.setTailPosition(this.handle, value);
    }

    set ball(value) {
        this.ball.assign(value);
    }
}


class ShapeTrapezoid extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeTrapezoid';
    }

    static create() {
        return new ShapeTrapezoid(ShapeTrapezoidApi.create());
    }

    clone() {
        return new ShapeTrapezoid(ShapeTrapezoidApi.clone(this.handle));
    }

    get left() {
        return ShapeTrapezoidApi.getLeftPosition(this.handle);
    }

    get right() {
        return ShapeTrapezoidApi.getRightPosition(this.handle);
    }

    set left(value) {
        ShapeTrapezoidApi.setLeftPosition(this.handle, value);
    }

    set right(value) {
        ShapeTrapezoidApi.setRightPosition(this.handle, value);
    }

    setPositions(left, right) {
        ShapeTrapezoidApi.setPositions(this.handle, left, right);
    }
}


class ShapeTriangle extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeTriangle';
    }

    static create() {
        return new ShapeTriangle(ShapeTriangleApi.create());
    }

    clone() {
        return new ShapeTriangle(ShapeTriangleApi.clone(this.handle));
    }

    get position() {
        return ShapeTriangleApi.getPosition(this.handle);
    }

    set position(value) {
        ShapeTriangleApi.setPosition(this.handle, value);
    }
}

class ShapeQRCode extends Shape {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeQRCode';
    }

    static create() {
        return new ShapeQRCode(ShapeQRCodeApi.create());
    }

    clone() {
        return new ShapeQRCode(ShapeQRCodeApi.clone(this.handle));
    }

    get payload() {
        return createTypedQRPayload(ShapeQRCodeApi.getPayload(this.handle));
    }

    set payload(value) {
        ShapeQRCodeApi.setPayload(this.handle, value.handle);
    }
}

function createTypedShape(shapeHandle) {
    const type = ShapeApi.getShapeType(shapeHandle);
    switch (type.value) {
        case ShapeType.Arrow.value:
            return new ShapeArrow(ShapeArrowApi.fromShape(shapeHandle));
        case ShapeType.CalloutEllipse.value:
            return new ShapeCalloutEllipse(ShapeCalloutEllipseApi.fromShape(shapeHandle));
        case ShapeType.CalloutRectangle.value:
            return new ShapeCalloutRectangle(ShapeCalloutRectangleApi.fromShape(shapeHandle));
        case ShapeType.Cat.value:
            return new ShapeCat(ShapeCatApi.fromShape(shapeHandle));
        case ShapeType.Cat2.value:
            return new ShapeCat2(ShapeCat2Api.fromShape(shapeHandle));
        case ShapeType.Cat3.value:
            return new ShapeCat3(ShapeCat3Api.fromShape(shapeHandle));
        case ShapeType.Cat4.value:
            return new ShapeCat4(ShapeCat4Api.fromShape(shapeHandle));
        case ShapeType.Cloud.value:
            return new ShapeCloud(ShapeCloudApi.fromShape(shapeHandle));
        case ShapeType.Cog.value:
            return new ShapeCog(ShapeCogApi.fromShape(shapeHandle));
        case ShapeType.Crescent.value:
            return new ShapeCrescent(ShapeCrescentApi.fromShape(shapeHandle));
        case ShapeType.Diamond.value:
            return new ShapeDiamond(ShapeDiamondApi.fromShape(shapeHandle));
        case ShapeType.DoubleStar.value:
            return new ShapeDoubleStar(ShapeDoubleStarApi.fromShape(shapeHandle));
        case ShapeType.Ellipse.value:
            return new ShapeEllipse(ShapeEllipseApi.fromShape(shapeHandle));
        case ShapeType.Heart.value:
            return new ShapeHeart(ShapeHeartApi.fromShape(shapeHandle));
        case ShapeType.Pie.value:
            return new ShapePie(ShapePieApi.fromShape(shapeHandle));
        case ShapeType.Polygon.value:
            return new ShapePolygon(ShapePolygonApi.fromShape(shapeHandle));
        case ShapeType.Rectangle.value:
            return new ShapeRectangle(ShapeRectangleApi.fromShape(shapeHandle));
        case ShapeType.Segment.value:
            return new ShapeSegment(ShapeSegmentApi.fromShape(shapeHandle));
        case ShapeType.Spiral.value:
            return new ShapeSpiral(ShapeSpiralApi.fromShape(shapeHandle));
        case ShapeType.SquareStar.value:
            return new ShapeSquareStar(ShapeSquareStarApi.fromShape(shapeHandle));
        case ShapeType.Star.value:
            return new ShapeStar(ShapeStarApi.fromShape(shapeHandle));
        case ShapeType.Tear.value:
            return new ShapeTear(ShapeTearApi.fromShape(shapeHandle));
        case ShapeType.Trapezoid.value:
            return new ShapeTrapezoid(ShapeTrapezoidApi.fromShape(shapeHandle));
        case ShapeType.Triangle.value:
            return new ShapeTriangle(ShapeTriangleApi.fromShape(shapeHandle));
        case ShapeType.QRCode.value:
            return new ShapeQRCode(ShapeQRCodeApi.fromShape(shapeHandle));
    }
    return new Shape(shapeHandle);
}

module.exports.createTypedQRPayload = createTypedQRPayload;
module.exports.createTypedShape = createTypedShape;
module.exports.QRPayload = QRPayload;
module.exports.QRPayloadEmail = QRPayloadEmail;
module.exports.QRPayloadFaceTime = QRPayloadFaceTime;
module.exports.QRPayloadLocation = QRPayloadLocation;
module.exports.QRPayloadPhone = QRPayloadPhone;
module.exports.QRPayloadSMS = QRPayloadSMS;
module.exports.QRPayloadText = QRPayloadText;
module.exports.QRPayloadURL = QRPayloadURL;
module.exports.QRPayloadVCard = QRPayloadVCard;
module.exports.QRPayloadWhatsApp = QRPayloadWhatsApp;
module.exports.QRPayloadWifi = QRPayloadWifi;
module.exports.Shape = Shape;
module.exports.ShapeArrow = ShapeArrow;
module.exports.ShapeCalloutEllipse = ShapeCalloutEllipse;
module.exports.ShapeCalloutRectangle = ShapeCalloutRectangle;
module.exports.ShapeCat = ShapeCat;
module.exports.ShapeCat2 = ShapeCat2;
module.exports.ShapeCat3 = ShapeCat3;
module.exports.ShapeCat4 = ShapeCat4;
module.exports.ShapeCloud = ShapeCloud;
module.exports.ShapeCog = ShapeCog;
module.exports.ShapeCrescent = ShapeCrescent;
module.exports.ShapeDiamond = ShapeDiamond;
module.exports.ShapeDoubleStar = ShapeDoubleStar;
module.exports.ShapeEllipse = ShapeEllipse;
module.exports.ShapeHeart = ShapeHeart;
module.exports.ShapePie = ShapePie;
module.exports.ShapePolygon = ShapePolygon;
module.exports.ShapeQRCode = ShapeQRCode;
module.exports.ShapeRectangle = ShapeRectangle;
module.exports.ShapeSegment = ShapeSegment;
module.exports.ShapeSpiral = ShapeSpiral
module.exports.ShapeSquareStar = ShapeSquareStar;
module.exports.ShapeStar = ShapeStar;
module.exports.ShapeTear = ShapeTear;
module.exports.ShapeTrapezoid = ShapeTrapezoid;
module.exports.ShapeTriangle = ShapeTriangle;
module.exports.QRPayloadType = QRPayloadType;
module.exports.ShapeArrowEndStyle = ShapeArrowEndStyle;
module.exports.ShapeBoolParam = ShapeBoolParam;
module.exports.ShapeCornerIndex = ShapeCornerIndex;
module.exports.ShapeCornerType = ShapeCornerType;
module.exports.ShapeEnumParam = ShapeEnumParam;
module.exports.ShapeFloatParam = ShapeFloatParam;
module.exports.ShapeIntParam = ShapeIntParam;
module.exports.ShapeMajorAxis = ShapeMajorAxis;
module.exports.ShapeSpiralStyle = ShapeSpiralStyle;
module.exports.ShapeType = ShapeType;
module.exports.WifiEncryptionType = WifiEncryptionType;
