'use strict';

const { EnumerationResult, HorizontalAlignment, UnitType, UserUnitType } = require('affinity:common');
const { SpatialAnchor } = require('affinity:dom');
const {
    DialogApi,
    DialogBoolControlApi,
    DialogButtonApi,
    DialogButtonSetApi,
    DialogCheckBoxApi,
    DialogColourPickerApi,
    DialogColumnApi,
    DialogColumnStackApi,
    DialogComboBoxApi,
    DialogControlApi,
    DialogItemType,
    DialogEnumControlApi,
    DialogFillEditorApi,
    DialogFontPickerApi,
    DialogGroupApi,
    DialogItemApi,
    DialogRadioGroupApi,
    DialogResult,
    DialogSpatialAnchorApi,
    DialogStaticTextApi,
    DialogStrokeEditorApi,
    DialogSwitchApi,
    DialogTextBoxApi,
    DialogTextControlApi,
    DialogUnitValueEditorApi
} = require('affinity:ui');
const { Collection } = require('./collection.js');
const { Colour } = require('./colours.js');
const { createTypedFill, SolidFill } = require('./fills.js');
const { Font, FontCollection, FontFamily } = require('./fonts.js');
const { HandleObject } = require('./handleobject.js');

function getCtrlId(ctrlOrCtrlID) {
    return (ctrlOrCtrlID instanceof DialogControl) ? ctrlOrCtrlID.controlID : ctrlOrCtrlID;
}

function createTypedDialogControl(ctrlHandle) {
    if (ctrlHandle == null)
        return null;
    let ctrlType = DialogItemApi.getItemType(ctrlHandle);
    switch (ctrlType) {
        case DialogItemType.Switch:
            return new DialogSwitch(DialogSwitchApi.fromControl(ctrlHandle));
        case DialogItemType.ComboBox:
            return new DialogComboBox(DialogComboBoxApi.fromControl(ctrlHandle));
        case DialogItemType.ButtonSet:
            return new DialogButtonSet(DialogButtonSetApi.fromControl(ctrlHandle));
        case DialogItemType.RadioGroup:
            return new DialogRadioGroup(DialogRadioGroupApi.fromControl(ctrlHandle));
        case DialogItemType.StaticText:
            return new DialogStaticText(DialogStaticTextApi.fromControl(ctrlHandle));
        case DialogItemType.TextBox:
            return new DialogTextBox(DialogTextBoxApi.fromControl(ctrlHandle));
        case DialogItemType.UnitValueEditor:
            return new DialogUnitValueEditor(DialogUnitValueEditorApi.fromControl(ctrlHandle));
        case DialogItemType.CheckBox:
            return new DialogCheckBox(DialogCheckBoxApi.fromControl(ctrlHandle));
        case DialogItemType.SpatialAnchor:
            return new DialogSpatialAnchor(DialogSpatialAnchorApi.fromControl(ctrlHandle));
        case DialogItemType.ColourPicker:
            return new DialogColourPicker(DialogColourPickerApi.fromControl(ctrlHandle));
        case DialogItemType.FontPicker:
            return new DialogFontPicker(DialogFontPickerApi.fromControl(ctrlHandle));
        case DialogItemType.FillEditor:
            return new DialogFillEditor(DialogFillEditorApi.fromControl(ctrlHandle));
        case DialogItemType.StrokeEditor:
            return new DialogStrokeEditor(DialogStrokeEditorApi.fromControl(ctrlHandle));
        case DialogItemType.Button:
            return new DialogButton(DialogButtonApi.fromControl(ctrlHandle));
        default:
            return new DialogControl(ctrlHandle);
    }
}


class DialogItem extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'DialogItem';
    }

    get itemID() {
        return DialogItemApi.getItemID(this.handle);
    }

    get itemType() {
        return DialogItemApi.getItemType(this.handle);
    }

    get isVisible() {
        return DialogItemApi.getIsVisible(this.handle);
    }

    set isVisible(visible) {
        DialogItemApi.setIsVisible(this.handle, visible);
    }

    setIsVisible(visible = true) {
        this.isVisible = visible;
        return this;
    }
}


class DialogControl extends DialogItem {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'DialogControl';
    }

    get controlID() {
        return this.itemID;
    }

    get controlType() {
        return this.itemType;
    }

    get isEnabled() {
        return DialogControlApi.getIsEnabled(this.handle);
    }

    set isEnabled(b) {
        DialogControlApi.setIsEnabled(this.handle, b);
    }

    setIsEnabled(enabled = true) {
        this.isEnabled = enabled;
        return this;
    }

    get label() {
        return DialogControlApi.getLabel(this.handle);
    }

    /**
    * @deprecated Reimplement using ValueChanged handler
    */
    setIsEnabledBy(ctrlOrCtrlID) {
        console.warn("Using deprecated DialogControl.setIsEnabledBy() function. This no longer does anything.");
        return this;
    }

    /**
    * @deprecated Reimplement using ValueChanged handler
    */
    setIsEnabledByWithSelectedIndex(ctrlOrCtrlID, index) {
        console.warn("Using deprecated DialogControl.setIsEnabledByWithSelectedIndex() function. This no longer does anything.");
        return this;
    }

    /**
    * @deprecated Reimplement using ValueChanged handler
    */
    setIsDisabledBy(ctrlOrCtrlID) {
        console.warn("Using deprecated DialogControl.setIsDisabledBy() function. This no longer does anything.");
        return this;
    }

    /**
    * @deprecated Reimplement using ValueChanged handler
    */
    setIsDisabledByWithSelectedIndex(ctrlOrCtrlID, index) {
        console.warn("Using deprecated DialogControl.setIsDisabledByWithSelectedIndex() function. This no longer does anything.");
        return this;
    }

    /**
    * @deprecated Reimplement using ValueChanged handler
    */
    setIsEnabledByControlID(ctrlID) {
        console.warn("Using deprecated DialogControl.setIsEnabledByControlID() function. This no longer does anything.");
        return this;
    }

    /**
    * @deprecated Reimplement using ValueChanged handler
    */
    setIsDisabledByControlID(ctrlID) {
        console.warn("Using deprecated DialogControl.setIsDisabledByControlID() function. This no longer does anything.");
        return this;
    }

    /**
    * @deprecated Reimplement using ValueChanged handler
    */
    setIsEnabledByControlIDWithSelectedIndex(ctrlID, item) {
        console.warn("Using deprecated DialogControl.setIsEnabledByControlIDWithSelectedIndex() function. This no longer does anything.");
        return this;
    }

    /**
    * @deprecated Reimplement using ValueChanged handler
    */
    setIsDisabledByControlIDWithSelectedIndex(ctrlID, item) {
        console.warn("Using deprecated DialogControl.setIsDisabledByControlIDWithSelectedIndex() function. This no longer does anything.");
        return this;
    }

    get description() {
        return DialogControlApi.getDescription(this.handle);
    }

    set description(value) {
        DialogControlApi.setDescription(this.handle, value);
    }

    setDescription(value) {
        this.description = value;
        return this;
    }

    set onValueChangedHandler(handler) {
        DialogControlApi.setOnValueChangedHandler(this.handle, handler);
    }

    setOnValueChangedHandler(handler) {
        this.onValueChangedHandler = handler;
        return this;
    }
}


class DialogBoolControl extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get value() {
        return DialogBoolControlApi.getValue(this.handle);
    }

    set value(b) {
        DialogBoolControlApi.setValue(this.handle, b);
    }

    setValue(value) {
        this.value = value;
        return this;
    }
}


class DialogEnumControl extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get selectedIndex() {
        return DialogEnumControlApi.getSelectedIndex(this.handle);
    }

    set selectedIndex(item) {
        DialogEnumControlApi.setSelectedIndex(this.handle, item);
    }

    setSelectedIndex(index) {
        this.selectedIndex = index;
        return this;
    }
}


class DialogButtonSet extends DialogEnumControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogButtonSet';
    }

    get isFullWidth() {
        return DialogButtonSetApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogButtonSetApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }
}


class DialogCheckBox extends DialogBoolControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogCheckBox';
    }

    get isFullWidth() {
        return DialogCheckBoxApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogCheckBoxApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }
}


class DialogComboBox extends DialogEnumControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogComboBox';
    }

    get isFullWidth() {
        return DialogComboBoxApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogComboBoxApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }
}


class DialogRadioGroup extends DialogEnumControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogRadioGroup';
    }

    get isFullWidth() {
        return DialogRadioGroupApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogRadioGroupApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }
}


class DialogSwitch extends DialogBoolControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogSwitch';
    }
}


class DialogButton extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogButton';
    }

    get isFullWidth() {
        return DialogButtonApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogButtonApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }

    get alignment() {
        return DialogButtonApi.getAlignment(this.handle);
    }

    set alignment(alignment) {
        DialogButtonApi.setAlignment(this.handle, alignment);
    }

    setAlignment(alignment) {
        this.alignment = alignment;
        return this;
    }

    set onClickHandler(handler) {
        super.onValueChangedHandler = handler;
    }

    setOnClickHandler(handler) {
        this.onClickHandler = handler;
        return this;
    }
}


class DialogTextControl extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogTextControl';
    }

    get isFullWidth() {
        return DialogTextControlApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogTextControlApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }

    get text() {
        return DialogTextControlApi.getText(this.handle);
    }

    set text(value) {
        DialogTextControlApi.setText(this.handle, value);
    }

    setText(text) {
        this.text = text;
        return this;
    }

    get textHorizontalAlignment() {
        return DialogTextControlApi.getTextHorizontalAlignment(this.handle);
    }

    set textHorizontalAlignment(alignment) {
        DialogTextControlApi.setTextHorizontalAlignment(this.handle, alignment);
    }

    setTextHorizontalAlignment(alignment) {
        this.textHorizontalAlignment = alignment;
        return this;
    }
}


class DialogStaticText extends DialogTextControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogStaticText';
    }
}


class DialogTextBox extends DialogTextControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogTextBox';
    }

    get isMultiLine() {
        return DialogTextBoxApi.getIsMultiLine(this.handle);
    }

    set isMultiLine(value) {
        return DialogTextBoxApi.setIsMultiLine(this.handle, value);
    }

    setIsMultiLine(value = true) {
        this.isMultiLine = value;
        return this;
    }

    get rowSpan() {
        return DialogTextBoxApi.getRowSpan(this.handle);
    }

    set rowSpan(rowSpan) {
        return DialogTextBoxApi.setRowSpan(this.handle, rowSpan);
    }

    setRowSpan(rowSpan) {
        this.rowSpan = rowSpan;
        return this;
    }
}


class DialogUnitValueEditor extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogUnitValueEditor';
    }

    get isFullWidth() {
        return DialogUnitValueEditorApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogUnitValueEditorApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }

    get value() {
        return DialogUnitValueEditorApi.getValue(this.handle);
    }

    set value(value) {
        DialogUnitValueEditorApi.setValue(this.handle, value);
    }

    setValue(value) {
        this.value = value;
        return this;
    }

    get units() {
        return DialogUnitValueEditorApi.getUnits(this.handle);
    }

    get noMinValue() {
        return DialogUnitValueEditorApi.getHasNoMinValue(this.handle);
    }

    set noMinValue(value) {
        return DialogUnitValueEditorApi.setHasNoMinValue(this.handle, value);
    }

    setNoMinValue(value = true) {
        this.noMinValue = value;
        return this;
    }

    get noMaxValue() {
        return DialogUnitValueEditorApi.getHasNoMaxValue(this.handle);
    }

    set noMaxValue(value) {
        return DialogUnitValueEditorApi.setHasNoMaxValue(this.handle, value);
    }

    setNoMaxValue(value = true) {
        this.noMaxValue = value;
        return this;
    }

    get showPopupSlider() {
        return DialogUnitValueEditorApi.getShowPopupSlider(this.handle);
    }

    set showPopupSlider(value) {
        DialogUnitValueEditorApi.setShowPopupSlider(this.handle, value);
    }

    setShowPopupSlider(value = true) {
        this.showPopupSlider = value;
        return this;
    }

    get precision() {
        return DialogUnitValueEditorApi.getPrecision(this.handle);
    }

    set precision(precision) {
        return DialogUnitValueEditorApi.setPrecision(this.handle, precision);
    }

    setPrecision(precision) {
        this.precision = precision;
        return this;
    }
}


class DialogSpatialAnchor extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogSpatialAnchor';
    }

    get value() {
        return DialogSpatialAnchorApi.getValue(this.handle);
    }

    set value(text) {
        DialogSpatialAnchorApi.setValue(this.handle, text);
    }
}


class DialogColourPicker extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogColourPicker';
    }

    get isFullWidth() {
        return DialogColourPickerApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogColourPickerApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }

    get value() {
        const clrHandle = DialogColourPickerApi.getValue(this.handle)
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set value(value) {
        DialogColourPickerApi.setValue(this.handle, value ? value.handle : null);
    }

    get allowPickNone() {
        return DialogColourPickerApi.getAllowPickNone(this.handle);
    }

    set allowPickNone(value) {
        DialogColourPickerApi.setAllowPickNone(this.handle, value);
    }

    setAllowPickNone(b = true) {
        this.allowPickNone = b;
        return this;
    }

    get allowNoise() {
        return DialogColourPickerApi.getAllowNoise(this.handle);
    }

    set allowNoise(value) {
        DialogColourPickerApi.setAllowNoise(this.handle, value);
    }

    setAllowNoise(b = true) {
        this.allowNoise = b;
        return this;
    }
}


class DialogFontPicker extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogFontPicker';
    }

    get isFullWidth() {
        return DialogFontPickerApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogFontPickerApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }

    get text() {
        return DialogFontPickerApi.getText(this.handle);
    }

    set text(name) {
        DialogFontPickerApi.setText(this.handle, name);
    }

    setText(text) {
        this.text = text;
        return this;
    }

    get font() {
        let res = DialogFontPickerApi.getFont(this.handle);
        if (res)
            res = new Font(res);
        return res;
    }

    set font(font) {
        DialogFontPickerApi.setFont(this.handle, font?.handle);
    }

    setFont(font) {
        this.font = font;
        return this;
    }

    get fontFamily() {
        let res = DialogFontPickerApi.getFontFamily(this.handle);
        if (res)
            res = new FontFamily(res);
        return res;
    }

    set fontFamily(fontFamily) {
        DialogFontPickerApi.setFontFamily(this.handle, fontFamily?.handle);
    }

    setFontFamily(fontFamily) {
        this.fontFamily = fontFamily;
        return this;
    }

    get fontCollection() {
        return new FontCollection(DialogFontPickerApi.getFontCollection(this.handle));
    }

    set fontCollection(fontCollection) {
        DialogFontPickerApi.setFontCollection(this.handle, fontCollection?.handle);
    }

    setFontCollection(fontCollection) {
        this.fontCollection = fontCollection;
        return this;
    }
}


class DialogFillEditor extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogFillEditor';
    }

    get isFullWidth() {
        return DialogFillEditorApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogFillEditorApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }

    get fill() {
        return createTypedFill(DialogFillEditorApi.getFill(this.handle));
    }

    set fill(fill) {
        DialogFillEditorApi.setFill(this.handle, fill?.handle);
    }

    setFill(fill) {
        this.fill = fill;
        return this;
    }

    get isStrokeFill() {
        return DialogFillEditorApi.getIsStrokeFill(this.handle);
    }

    set isStrokeFill(value) {
        DialogFillEditorApi.setIsStrokeFill(this.handle, value);
    }
    
    setIsStrokeFill(b = true) {
        this.isStrokeFill = b;
        return this;
    }
}


class DialogStrokeEditor extends DialogControl {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogStrokeEditor';
    }

    get isFullWidth() {
        return DialogStrokeEditorApi.getIsFullWidth(this.handle);
    }

    set isFullWidth(b) {
        DialogStrokeEditorApi.setIsFullWidth(this.handle, b);
    }

    setIsFullWidth(b = true) {
        this.isFullWidth = b;
        return this;
    }

    get stroke() {
        return DialogStrokeEditorApi.getStroke(this.handle);
    }

    set stroke(stroke) {
        DialogStrokeEditorApi.setStroke(this.handle, stroke);
    }

    setStroke(stroke) {
        this.stroke = stroke;
        return this;
    }
}


class DialogGroupControls extends Collection {
    #groupHandle;
    constructor(groupHandle) {
        const genFn = function*() {
            let index = 0;
            while (index < DialogGroupApi.getControlCount(groupHandle))
                yield createTypedDialogControl(DialogGroupApi.getControl(groupHandle, index++));
        }
        super(genFn);
        this.#groupHandle = groupHandle;
    }

    get length() {
        return DialogGroupApi.getControlCount(this.#groupHandle);
    }

    at(index) {
        return createTypedDialogControl(DialogGroupApi.getControl(this.#groupHandle, index));
    }
}


class DialogGroup extends DialogItem {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DialogGroup';
    }

    #controls;
    get controls() {
        if (!this.#controls) {
            this.#controls = new DialogGroupControls(this.handle);
        }
        return this.#controls;
    }

    get label() {
        return DialogGroupApi.getLabel(this.handle);
    }

    get column() {
        return new DialogColumn(DialogGroupApi.getColumn(this.handle));
    }

    get enableSeparator() {
        return DialogGroupApi.getEnableSeparator(this.handle);
    }

    set enableSeparator(value) {
        DialogGroupApi.setEnableSeparator(this.handle, value);
    }

    setEnableSeparator(enable = true) {
        this.enableSeparator = enable;
        return this;
    }

    addButtonSet(label, items, initialItem) {
        return new DialogButtonSet(DialogGroupApi.addButtonSet(this.handle, label, items, initialItem));
    }

    addCheckBox(label, initialValue) {
        return new DialogCheckBox(DialogGroupApi.addCheckBox(this.handle, label, initialValue));
    }

    addComboBox(label, items, initialItem) {
        return new DialogComboBox(DialogGroupApi.addComboBox(this.handle, label, items, initialItem));
    }

    addRadioGroup(label, items, initialItem) {
        return new DialogRadioGroup(DialogGroupApi.addRadioGroup(this.handle, label, items, initialItem));
    }

    addStaticText(label, text) {
        return new DialogStaticText(DialogGroupApi.addStaticText(this.handle, label, text));
    }

    addTextBox(label, text) {
        return new DialogTextBox(DialogGroupApi.addTextBox(this.handle, label, text));
    }

    addSwitch(label, initialValue) {
        return new DialogSwitch(DialogGroupApi.addSwitch(this.handle, label, initialValue));
    }

    addUnitValueEditor(label, units, displayUnits, initialValue, minValue = null, maxValue = null) {
        const unitValueEditor = new DialogUnitValueEditor(DialogGroupApi.addUnitValueEditor(this.handle, label, units, displayUnits, minValue, maxValue, initialValue));
        if (minValue == null)
            unitValueEditor.noMinValue = true;
        if (maxValue == null)
            unitValueEditor.noMaxValue = true;
        return unitValueEditor;
    }

    addUserUnitValueEditor(label, units, displayUnits, initialValue, minValue = null, maxValue = null) {
        const unitValueEditor = new DialogUnitValueEditor(DialogGroupApi.addUserUnitValueEditor(this.handle, label, units, displayUnits, minValue, maxValue, initialValue));
        if (minValue == null)
            unitValueEditor.noMinValue = true;
        if (maxValue == null)
            unitValueEditor.noMaxValue = true;
        return unitValueEditor;
    }

    addSpatialAnchor(label, initialValue = SpatialAnchor.None) {
        return new DialogSpatialAnchor(DialogGroupApi.addSpatialAnchor(this.handle, label, initialValue));
    }

    addColourPicker(label, initialValue = null) {
        return new DialogColourPicker(DialogGroupApi.addColourPicker(this.handle, label, initialValue?.handle));
    }

    addFontPicker(label) {
        return new DialogFontPicker(DialogGroupApi.addFontPicker(this.handle, label));
    }

    addFillEditor(label, initialFill = null) {
        if (initialFill instanceof Colour)
            initialFill = SolidFill.create(initialFill);
        return new DialogFillEditor(DialogGroupApi.addFillEditor(this.handle, label, initialFill?.handle));
    }

    addStrokeEditor(label, initialLineStyleDescriptor = null) {
        return new DialogStrokeEditor(DialogGroupApi.addStrokeEditor(this.handle, label, initialLineStyleDescriptor?.handle));
    }

    addColumnStack() {
        return new DialogColumnStack(DialogGroupApi.addColumnStack(this.handle));
    }

    addButton(label) {
        return new DialogButton(DialogGroupApi.addButton(this.handle, label));
    }
}

class DialogColumnGroups extends Collection {
    #columnHandle;
    constructor(columnHandle) {
        const genFn = function*() {
            let index = 0;
            while (index < DialogColumnApi.getGroupCount(columnHandle))
                yield new DialogGroup(DialogColumnApi.getGroup(columnHandle, index++));
        }
        super(genFn);
        this.#columnHandle = columnHandle;
    }

    get length() {
        return DialogColumnApi.getGroupCount(this.#columnHandle);
    }

    at(index) {
        return new DialogGroup(DialogColumnApi.getGroup(this.#columnHandle, index));
    }
}


class DialogColumn extends DialogItem {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'DialogColumn';
    }

    #groups;
    get groups() {
        if (!this.#groups) {
            this.#groups = new DialogColumnGroups(this.handle);
        }
        return this.#groups;
    }

    get widthProportion() {
        return DialogColumnApi.getWidthProportion(this.handle);
    }

    set widthProportion(value) {
        DialogColumnApi.setWidthProportion(this.handle, value);
    }

    setWidthProportion(value) {
        this.widthProportion = value;
        return this;
    }

    get paddingFactor() {
        return DialogColumnApi.getPaddingFactor(this.handle);
    }

    set paddingFactor(value) {
        DialogColumnApi.setPaddingFactor(this.handle, value);
    }

    setPaddingFactor(value) {
        this.paddingFactor = value;
        return this;
    }

    get columnIndex() {
        return DialogColumnApi.getColumnIndex(this.handle);
    }

    addGroup(name) {
        return new DialogGroup(DialogColumnApi.addGroup(this.handle, name));
    }
    
    get controls() {
        return this.groups.map(group => group.controls.toArray()).flat();
    }
}


class DialogColumns extends Collection {
    #dialogHandle;
    constructor(dialogHandle) {
        const genFn = function*() {
            let index = 0;
            while (index < DialogApi.getColumnCount(dialogHandle))
                yield new DialogColumn(DialogApi.getColumn(dialogHandle, index++));
        }
        super(genFn);
        this.#dialogHandle = dialogHandle;
    }

    get length() {
        return DialogApi.getColumnCount(this.#dialogHandle);
    }

    at(index) {
        return new DialogColumn(DialogApi.getColumn(this.#dialogHandle, index));
    }
}


class DialogColumnStackColumns extends Collection {
    #columnStackHandle;
    constructor(columnStackHandle) {
        const genFn = function*() {
            let index = 0;
            while (index < DialogColumnStackApi.getColumnCount(columnStackHandle))
                yield new DialogColumn(DialogColumnStackApi.getColumn(columnStackHandle, index++));
        }
        super(genFn);
        this.#columnStackHandle = columnStackHandle;
    }

    get length() {
        return DialogColumnStackApi.getColumnCount(this.#columnStackHandle);
    }

    at(index) {
        return new DialogColumn(DialogColumnStackApi.getColumn(this.#columnStackHandle, index));
    }
}


class DialogColumnStack extends DialogItem {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'DialogColumnStack';
    }

    #columns;
    get columns() {
        if (!this.#columns) {
            this.#columns = new DialogColumnStackColumns(this.handle);
        }
        return this.#columns;
    }

    addColumn() {
        return new DialogColumn(DialogColumnStackApi.addColumn(this.handle));
    }
}


class Dialog extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'Dialog';
    }

    #columns;
    get columns() {
        if (!this.#columns)
            this.#columns = new DialogColumns(this.handle);
        return this.#columns;
    }

    static create(text) {
        return new Dialog(DialogApi.create(text));
    }

    /**
    * @deprecated Use runModal() instead
    */
    show() {
        console.warn("Using deprecated Dialog.show() method");
        return this.runModal();
    }

    runModal() {
        return DialogApi.runModal(this.handle);
    }

    findControl(ctrlID) {
        let ctrl = DialogApi.findControl(this.handle, ctrlID);
        if (ctrl) {
            return createTypedDialogControl(ctrl);
        }
        return null;
    }

    get initialWidth() {
        return DialogApi.getInitialWidth(this.handle);
    }

    set initialWidth(value) {
        DialogApi.setInitialWidth(this.handle, value);
    }

    addColumn() {
        return new DialogColumn(DialogApi.addColumn(this.handle));
    }

    get groups() {
        return this.columns.map(column => column.groups.toArray()).flat();
    }

    get controls() {
        return this.groups.map(group => group.controls.toArray()).flat();
    }

    setIsResizable(value) {
        this.isResizable = value;
        return this;
    }

    get isResizable() {
        return DialogApi.getIsResizable(this.handle);
    }

    set isResizable(value) {
        DialogApi.setIsResizable(this.handle, value);
    }

    get isRunningModal() {
        return DialogApi.getIsRunningModal(this.handle);
    }

    setOnControlValueChangedHandler(handler) {
        this.onControlValueChangedHandler = handler;
        return this;
    }

    set onControlValueChangedHandler(handler) {
        DialogApi.setOnControlValueChangedHandler(this.handle, handler);
    }

    setItemsVisibility(showIDs, hideIDs) {
        DialogApi.setItemsVisibility(this.handle, showIDs, hideIDs);
        return this;
    }
}

module.exports.Dialog = Dialog;
module.exports.DialogItemType = DialogItemType;
module.exports.DialogButton = DialogButton;
module.exports.DialogButtonSet = DialogButtonSet;
module.exports.DialogComboBox = DialogComboBox;
module.exports.DialogColourPicker = DialogColourPicker;
module.exports.DialogColumn = DialogColumn;
module.exports.DialogColumnStack = DialogColumnStack;
module.exports.DialogControl = DialogControl;
module.exports.DialogFillEditor = DialogFillEditor;
module.exports.DialogGroup = DialogGroup;
module.exports.DialogRadioGroup = DialogRadioGroup;
module.exports.DialogResult = DialogResult;
module.exports.DialogSpatialAnchor = DialogSpatialAnchor;
module.exports.DialogSwitch = DialogSwitch;
module.exports.DialogStaticText = DialogStaticText;
module.exports.DialogTextBox = DialogTextBox;
module.exports.DialogUnitValueEditor = DialogUnitValueEditor;
module.exports.DialogSpatialAnchor = DialogSpatialAnchor;
module.exports.DialogStrokeEditor = DialogStrokeEditor;
module.exports.HorizontalAlignment = HorizontalAlignment;
module.exports.SpatialAnchor = SpatialAnchor;
module.exports.UnitType = UnitType;
module.exports.UserUnitType = UserUnitType;

// For backwards compatibility
module.exports.DialogControlType = DialogItemType;