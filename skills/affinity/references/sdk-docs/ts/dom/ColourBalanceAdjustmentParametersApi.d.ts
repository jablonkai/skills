// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ColourBalanceAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface ColourBalanceAdjustmentParametersApi {
        create(): ColourBalanceAdjustmentParametersHandle;
        enumerateValues(self: ColourBalanceAdjustmentParametersHandle, callback: (tonalRange: TonalRangeType, values: ColourBalanceValues) => EnumerationResult): void;
        getPreserveLuminosity(self: ColourBalanceAdjustmentParametersHandle): boolean;
        getValues(self: ColourBalanceAdjustmentParametersHandle, tonalRange: TonalRangeType): ColourBalanceValues;
        getValuesCount(self: ColourBalanceAdjustmentParametersHandle): number;
        setPreserveLuminosity(self: ColourBalanceAdjustmentParametersHandle, preserveLuminosity: boolean): void;
        setValues(self: ColourBalanceAdjustmentParametersHandle, tonalRange: TonalRangeType, values: ColourBalanceValues): void;
    }
    export const ColourBalanceAdjustmentParametersApi: ColourBalanceAdjustmentParametersApi;

}
