// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SelectiveColourAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface SelectiveColourAdjustmentParametersApi {
        create(): SelectiveColourAdjustmentParametersHandle;
        enumerateWeights(self: SelectiveColourAdjustmentParametersHandle, callback: (colour: SelectiveColour, weights: SelectiveColourWeights) => EnumerationResult): void;
        getIsRelative(self: SelectiveColourAdjustmentParametersHandle): boolean;
        getWeights(self: SelectiveColourAdjustmentParametersHandle, colour: SelectiveColour): SelectiveColourWeights;
        getWeightsCount(self: SelectiveColourAdjustmentParametersHandle): number;
        setIsRelative(self: SelectiveColourAdjustmentParametersHandle, isRelative: boolean): void;
        setWeights(self: SelectiveColourAdjustmentParametersHandle, colour: SelectiveColour, weights: SelectiveColourWeights): void;
    }
    export const SelectiveColourAdjustmentParametersApi: SelectiveColourAdjustmentParametersApi;

}
