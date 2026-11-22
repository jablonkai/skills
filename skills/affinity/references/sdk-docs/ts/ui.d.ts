// Type declarations for the Affinity JavaScript SDK: module "affinity:ui".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:ui" {

    import { EnumerationResult, HorizontalAlignment, UnitType, UserUnitType } from "affinity:common";
    import { SpatialAnchor } from "affinity:dom";
    import { Size } from "affinity:geometry";

    export enum DialogItemType {
        Unknown,
        Separator,
        Switch,
        ComboBox,
        ButtonSet,
        RadioGroup,
        StaticText,
        UnitValueEditor,
        CheckBox,
        SpatialAnchor,
        ColourPicker,
        TextBox,
        FontPicker,
        FillEditor,
        StrokeEditor,
        Group,
        Column,
        ColumnStack,
        Button,
    }

    export enum DialogResult {
        Cancel,
        Ok,
    }

    export interface DialogApi {
        addColumn(self: DialogHandle): DialogColumnHandle;
        create(title: string, sizeOrNull: Size | null): DialogHandle;
        enumerateColumns(self: DialogHandle, callback: (column: DialogColumnHandle) => EnumerationResult): void;
        findControl(self: DialogHandle, controlID: number): DialogControlHandle;
        getColumn(self: DialogHandle, index: number): DialogColumnHandle;
        getColumnCount(self: DialogHandle): number;
        getInitialWidth(self: DialogHandle): number;
        getIsResizable(self: DialogHandle): boolean;
        getIsRunningModal(self: DialogHandle): boolean;
        runModal(self: DialogHandle): DialogResult;
        setInitialWidth(self: DialogHandle, width: number): void;
        setIsResizable(self: DialogHandle, isResizable: boolean): void;
        setItemsVisibility(self: DialogHandle, showIDs: number[], hideIDs: number[]): void;
        setOnControlValueChangedHandler(self: DialogHandle, callback: (transient: boolean, controlID: number) => void): void;
    }
    export const DialogApi: DialogApi;

    export interface DialogBoolControlApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogBoolControlHandle;
        getValue(self: DialogBoolControlHandle): boolean;
        setValue(self: DialogBoolControlHandle, value: boolean): void;
    }
    export const DialogBoolControlApi: DialogBoolControlApi;

    export interface DialogButtonApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogButtonHandle;
        getAlignment(self: DialogButtonHandle): HorizontalAlignment;
        getIsFullWidth(self: DialogButtonHandle): boolean;
        setAlignment(self: DialogButtonHandle, alignment: HorizontalAlignment): void;
        setIsFullWidth(self: DialogButtonHandle, isFullWidth: boolean): void;
    }
    export const DialogButtonApi: DialogButtonApi;

    export interface DialogButtonSetApi extends Omit<DialogEnumControlApi, "fromControl"> {
        fromControl(ctrl: DialogControlHandle): DialogButtonSetHandle;
        getIsFullWidth(self: DialogButtonSetHandle): boolean;
        setIsFullWidth(self: DialogButtonSetHandle, isFullWidth: boolean): void;
    }
    export const DialogButtonSetApi: DialogButtonSetApi;

    export interface DialogCheckBoxApi extends Omit<DialogBoolControlApi, "fromControl"> {
        fromControl(ctrl: DialogControlHandle): DialogCheckBoxHandle;
        getIsFullWidth(self: DialogCheckBoxHandle): boolean;
        setIsFullWidth(self: DialogCheckBoxHandle, isFullWidth: boolean): void;
    }
    export const DialogCheckBoxApi: DialogCheckBoxApi;

    export interface DialogColourPickerApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogColourPickerHandle;
        getAllowNoise(self: DialogColourPickerHandle): boolean;
        getAllowPickNone(self: DialogColourPickerHandle): boolean;
        getIsFullWidth(self: DialogColourPickerHandle): boolean;
        getValue(self: DialogColourPickerHandle): ColourHandle;
        setAllowNoise(self: DialogColourPickerHandle, value: boolean): void;
        setAllowPickNone(self: DialogColourPickerHandle, value: boolean): void;
        setIsFullWidth(self: DialogColourPickerHandle, isFullWidth: boolean): void;
        setValue(self: DialogColourPickerHandle, valueOrNull: ColourHandle | null): void;
    }
    export const DialogColourPickerApi: DialogColourPickerApi;

    export interface DialogColumnApi extends DialogItemApi {
        addGroup(self: DialogColumnHandle, text: string): DialogGroupHandle;
        enumerateGroups(self: DialogColumnHandle, callback: (group: DialogGroupHandle) => EnumerationResult): void;
        getColumnIndex(self: DialogColumnHandle): number;
        getGroup(self: DialogColumnHandle, index: number): DialogGroupHandle;
        getGroupCount(self: DialogColumnHandle): number;
        getPaddingFactor(self: DialogColumnHandle): number;
        getWidthProportion(self: DialogColumnHandle): number;
        setPaddingFactor(self: DialogColumnHandle, paddingFactor: number): void;
        setWidthProportion(self: DialogColumnHandle, widthProportion: number): void;
    }
    export const DialogColumnApi: DialogColumnApi;

    export interface DialogColumnStackApi extends DialogItemApi {
        addColumn(self: DialogColumnStackHandle): DialogColumnHandle;
        enumerateColumns(self: DialogColumnStackHandle, callback: (column: DialogColumnHandle) => EnumerationResult): void;
        getColumn(self: DialogColumnStackHandle, index: number): DialogColumnHandle;
        getColumnCount(self: DialogColumnStackHandle): number;
    }
    export const DialogColumnStackApi: DialogColumnStackApi;

    export interface DialogComboBoxApi extends Omit<DialogEnumControlApi, "fromControl"> {
        fromControl(ctrl: DialogControlHandle): DialogComboBoxHandle;
        getIsFullWidth(self: DialogComboBoxHandle): boolean;
        setIsFullWidth(self: DialogComboBoxHandle, isFullWidth: boolean): void;
    }
    export const DialogComboBoxApi: DialogComboBoxApi;

    export interface DialogControlApi extends DialogItemApi {
        getDescription(self: DialogControlHandle): string;
        getIsEnabled(self: DialogControlHandle): boolean;
        getLabel(self: DialogControlHandle): string;
        setDescription(self: DialogControlHandle, description: string): void;
        setIsEnabled(self: DialogControlHandle, isEnabled: boolean): void;
        setOnValueChangedHandler(self: DialogControlHandle, callback: (transient: boolean) => void): void;
    }
    export const DialogControlApi: DialogControlApi;

    export interface DialogEnumControlApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogEnumControlHandle;
        getSelectedIndex(self: DialogEnumControlHandle): number;
        setSelectedIndex(self: DialogEnumControlHandle, index: number): void;
    }
    export const DialogEnumControlApi: DialogEnumControlApi;

    export interface DialogFillEditorApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogFillEditorHandle;
        getFill(self: DialogFillEditorHandle): FillHandle;
        getIsFullWidth(self: DialogFillEditorHandle): boolean;
        getIsStrokeFill(self: DialogFillEditorHandle): boolean;
        setFill(self: DialogFillEditorHandle, fillOrNull: FillHandle | null): void;
        setIsFullWidth(self: DialogFillEditorHandle, isFullWidth: boolean): void;
        setIsStrokeFill(self: DialogFillEditorHandle, isStrokeFill: boolean): void;
    }
    export const DialogFillEditorApi: DialogFillEditorApi;

    export interface DialogFontPickerApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogFontPickerHandle;
        getFont(self: DialogFontPickerHandle): FontHandle;
        getFontCollection(self: DialogFontPickerHandle): FontCollectionHandle;
        getFontFamily(self: DialogFontPickerHandle): FontFamilyHandle;
        getIsFullWidth(self: DialogFontPickerHandle): boolean;
        getText(self: DialogFontPickerHandle): string;
        setFont(self: DialogFontPickerHandle, fontOrNull: FontHandle | null): void;
        setFontCollection(self: DialogFontPickerHandle, fontCollectionOrNull: FontCollectionHandle | null): void;
        setFontFamily(self: DialogFontPickerHandle, fontFamilyOrNull: FontFamilyHandle | null): void;
        setIsFullWidth(self: DialogFontPickerHandle, isFullWidth: boolean): void;
        setText(self: DialogFontPickerHandle, text: string): void;
    }
    export const DialogFontPickerApi: DialogFontPickerApi;

    export interface DialogGroupApi extends DialogItemApi {
        addButton(self: DialogGroupHandle, label: string): DialogButtonHandle;
        addButtonGetID(self: DialogGroupHandle, label: string): number;
        addButtonSet(self: DialogGroupHandle, label: string, items: string[], initialValue: number): DialogButtonSetHandle;
        addButtonSetGetID(self: DialogGroupHandle, label: string, items: string[], initialValue: number): number;
        addCheckBox(self: DialogGroupHandle, label: string, initialValue: boolean): DialogCheckBoxHandle;
        addCheckBoxGetID(self: DialogGroupHandle, label: string, initialValue: boolean): number;
        addColourPicker(self: DialogGroupHandle, label: string, initialValueOrNull: ColourHandle | null): DialogColourPickerHandle;
        addColourPickerGetID(self: DialogGroupHandle, label: string, initialValueOrNull: ColourHandle | null): number;
        addColumnStack(self: DialogGroupHandle): DialogColumnStackHandle;
        addColumnStackGetID(self: DialogGroupHandle): number;
        addComboBox(self: DialogGroupHandle, label: string, items: string[], initialValue: number): DialogComboBoxHandle;
        addComboBoxGetID(self: DialogGroupHandle, label: string, items: string[], initialValue: number): number;
        addFillEditor(self: DialogGroupHandle, label: string, initialValueOrNull: FillHandle | null): DialogFillEditorHandle;
        addFillEditorGetID(self: DialogGroupHandle, label: string, initialValueOrNull: FillHandle | null): number;
        addFontPicker(self: DialogGroupHandle, label: string): DialogFontPickerHandle;
        addFontPickerGetID(self: DialogGroupHandle, label: string): number;
        addRadioGroup(self: DialogGroupHandle, label: string, items: string[], initialValue: number): DialogRadioGroupHandle;
        addRadioGroupGetID(self: DialogGroupHandle, label: string, items: string[], initialValue: number): number;
        addSpatialAnchor(self: DialogGroupHandle, label: string, initialValue: SpatialAnchor): DialogSpatialAnchorHandle;
        addSpatialAnchorGetID(self: DialogGroupHandle, label: string, initialValue: SpatialAnchor): number;
        addStaticText(self: DialogGroupHandle, label: string, text: string): DialogStaticTextHandle;
        addStaticTextGetID(self: DialogGroupHandle, label: string, text: string): number;
        addStrokeEditor(self: DialogGroupHandle, label: string, initialValueOrNull: LineStyleDescriptorHandle | null): DialogStrokeEditorHandle;
        addStrokeEditorGetID(self: DialogGroupHandle, label: string, initialValueOrNull: LineStyleDescriptorHandle | null): number;
        addSwitch(self: DialogGroupHandle, label: string, initialValue: boolean): DialogSwitchHandle;
        addSwitchGetID(self: DialogGroupHandle, label: string, initialValue: boolean): number;
        addTextBox(self: DialogGroupHandle, label: string, text: string): DialogTextBoxHandle;
        addTextBoxGetID(self: DialogGroupHandle, label: string, text: string): number;
        addUnitValueEditor(self: DialogGroupHandle, label: string, units: UnitType, displayUnits: UnitType, minValue: number, maxValue: number, initialValue: number): DialogUnitValueEditorHandle;
        addUnitValueEditorGetID(self: DialogGroupHandle, label: string, units: UnitType, displayUnits: UnitType, minValue: number, maxValue: number, initialValue: number): number;
        addUserUnitValueEditor(self: DialogGroupHandle, label: string, units: UnitType, displayUnits: UserUnitType, minValue: number, maxValue: number, initialValue: number): DialogUnitValueEditorHandle;
        addUserUnitValueEditorGetID(self: DialogGroupHandle, label: string, units: UnitType, displayUnits: UserUnitType, minValue: number, maxValue: number, initialValue: number): number;
        enumerateControls(self: DialogGroupHandle, callback: (control: DialogControlHandle) => EnumerationResult): void;
        getColumn(self: DialogGroupHandle): DialogColumnHandle;
        getControl(self: DialogGroupHandle, index: number): DialogControlHandle;
        getControlCount(self: DialogGroupHandle): number;
        getEnableSeparator(self: DialogGroupHandle): boolean;
        getLabel(self: DialogGroupHandle): string;
        setEnableSeparator(self: DialogGroupHandle, enableSeparator: boolean): void;
    }
    export const DialogGroupApi: DialogGroupApi;

    export interface DialogItemApi {
        getIsVisible(self: DialogItemHandle): boolean;
        getItemID(self: DialogItemHandle): number;
        getItemType(self: DialogItemHandle): DialogItemType;
        setIsVisible(self: DialogItemHandle, visible: boolean): void;
    }
    export const DialogItemApi: DialogItemApi;

    export interface DialogRadioGroupApi extends Omit<DialogEnumControlApi, "fromControl"> {
        fromControl(ctrl: DialogControlHandle): DialogRadioGroupHandle;
        getIsFullWidth(self: DialogRadioGroupHandle): boolean;
        setIsFullWidth(self: DialogRadioGroupHandle, isFullWidth: boolean): void;
    }
    export const DialogRadioGroupApi: DialogRadioGroupApi;

    export interface DialogSpatialAnchorApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogSpatialAnchorHandle;
        getValue(self: DialogSpatialAnchorHandle): SpatialAnchor;
        setValue(self: DialogSpatialAnchorHandle, value: SpatialAnchor): void;
    }
    export const DialogSpatialAnchorApi: DialogSpatialAnchorApi;

    export interface DialogStaticTextApi extends Omit<DialogTextControlApi, "fromControl"> {
        fromControl(ctrl: DialogControlHandle): DialogStaticTextHandle;
    }
    export const DialogStaticTextApi: DialogStaticTextApi;

    export interface DialogStrokeEditorApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogStrokeEditorHandle;
        getIsFullWidth(self: DialogStrokeEditorHandle): boolean;
        getStroke(self: DialogStrokeEditorHandle): LineStyleDescriptorHandle;
        setIsFullWidth(self: DialogStrokeEditorHandle, isFullWidth: boolean): void;
        setStroke(self: DialogStrokeEditorHandle, lineStyleDescriptorOrNull: LineStyleDescriptorHandle | null): void;
    }
    export const DialogStrokeEditorApi: DialogStrokeEditorApi;

    export interface DialogSwitchApi extends Omit<DialogBoolControlApi, "fromControl"> {
        fromControl(ctrl: DialogControlHandle): DialogSwitchHandle;
    }
    export const DialogSwitchApi: DialogSwitchApi;

    export interface DialogTextBoxApi extends Omit<DialogTextControlApi, "fromControl"> {
        fromControl(ctrl: DialogControlHandle): DialogTextBoxHandle;
        getIsMultiLine(self: DialogTextBoxHandle): boolean;
        getRowSpan(self: DialogTextBoxHandle): number;
        setIsMultiLine(self: DialogTextBoxHandle, value: boolean): void;
        setRowSpan(self: DialogTextBoxHandle, rowSpan: number): void;
    }
    export const DialogTextBoxApi: DialogTextBoxApi;

    export interface DialogTextControlApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogTextControlHandle;
        getIsFullWidth(self: DialogTextControlHandle): boolean;
        getText(self: DialogTextControlHandle): string;
        getTextHorizontalAlignment(self: DialogTextControlHandle): HorizontalAlignment;
        setIsFullWidth(self: DialogTextControlHandle, isFullWidth: boolean): void;
        setText(self: DialogTextControlHandle, text: string): void;
        setTextHorizontalAlignment(self: DialogTextControlHandle, alignment: HorizontalAlignment): void;
    }
    export const DialogTextControlApi: DialogTextControlApi;

    export interface DialogUnitValueEditorApi extends DialogControlApi {
        fromControl(ctrl: DialogControlHandle): DialogUnitValueEditorHandle;
        getHasNoMaxValue(self: DialogUnitValueEditorHandle): boolean;
        getHasNoMinValue(self: DialogUnitValueEditorHandle): boolean;
        getIsFullWidth(self: DialogUnitValueEditorHandle): boolean;
        getPrecision(self: DialogUnitValueEditorHandle): number;
        getShowPopupSlider(self: DialogUnitValueEditorHandle): boolean;
        getUnits(self: DialogUnitValueEditorHandle): UnitType;
        getValue(self: DialogUnitValueEditorHandle): number;
        setHasNoMaxValue(self: DialogUnitValueEditorHandle, hasNoMaxValue: boolean): void;
        setHasNoMinValue(self: DialogUnitValueEditorHandle, hasNoMinValue: boolean): void;
        setIsFullWidth(self: DialogUnitValueEditorHandle, isFullWidth: boolean): void;
        setPrecision(self: DialogUnitValueEditorHandle, precision: number): void;
        setShowPopupSlider(self: DialogUnitValueEditorHandle, hasSlider: boolean): void;
        setValue(self: DialogUnitValueEditorHandle, value: number): void;
    }
    export const DialogUnitValueEditorApi: DialogUnitValueEditorApi;

    export interface UiApi {
        alert(message: string, title: string): void;
        alertAsync(message: string, title: string, callback: (errorCode: Error | null) => void): void;
        chooseFile(): string;
        chooseFileAsync(callback: (errorCode: Error | null, path: string) => void): void;
        confirm(message: string, title: string): boolean;
        confirmAsync(message: string, title: string, callback: (errorCode: Error | null, isOK: boolean) => void): void;
        prompt(message: string, title: string, initialText: string): string;
        promptAsync(message: string, title: string, initialText: string, callback: (errorCode: Error | null, result: string) => void): void;
    }
    export const UiApi: UiApi;

}
