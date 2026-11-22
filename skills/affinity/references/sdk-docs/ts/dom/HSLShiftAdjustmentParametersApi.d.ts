// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HSLShiftAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface HSLShiftAdjustmentParametersApi {
        create(): HSLShiftAdjustmentParametersHandle;
        enumerateChannelColourRanges(self: HSLShiftAdjustmentParametersHandle, callback: (channel: number, colourRange: HSLShiftAdjustmentColourRange) => EnumerationResult): void;
        enumerateChannelParameters(self: HSLShiftAdjustmentParametersHandle, callback: (channel: number, parameters: HSLShiftAdjustmentChannelParameters) => EnumerationResult): void;
        getChannelColourRange(self: HSLShiftAdjustmentParametersHandle, channel: number): HSLShiftAdjustmentColourRange;
        getChannelCount(self: HSLShiftAdjustmentParametersHandle): number;
        getChannelParameters(self: HSLShiftAdjustmentParametersHandle, channel: number): HSLShiftAdjustmentChannelParameters;
        getMasterParameters(self: HSLShiftAdjustmentParametersHandle): HSLShiftAdjustmentChannelParameters;
        getUseHSV(self: HSLShiftAdjustmentParametersHandle): boolean;
        setChannelColourRange(self: HSLShiftAdjustmentParametersHandle, channel: number, colourRange: HSLShiftAdjustmentColourRange): void;
        setChannelParameters(self: HSLShiftAdjustmentParametersHandle, channel: number, parameters: HSLShiftAdjustmentChannelParameters): void;
        setMasterParameters(self: HSLShiftAdjustmentParametersHandle, parameters: HSLShiftAdjustmentChannelParameters): void;
        setUseHSV(self: HSLShiftAdjustmentParametersHandle, useHSV: boolean): void;
    }
    export const HSLShiftAdjustmentParametersApi: HSLShiftAdjustmentParametersApi;

}
