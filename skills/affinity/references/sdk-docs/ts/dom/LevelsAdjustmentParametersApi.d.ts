// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LevelsAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface LevelsAdjustmentParametersApi {
        create(): LevelsAdjustmentParametersHandle;
        enumerateChannelParameters(self: LevelsAdjustmentParametersHandle, callback: (channel: number, parameters: LevelsAdjustmentChannelParameters) => EnumerationResult): void;
        getChannelParameters(self: LevelsAdjustmentParametersHandle, channel: number): LevelsAdjustmentChannelParameters;
        getChannelParametersCount(self: LevelsAdjustmentParametersHandle): number;
        getMasterParameters(self: LevelsAdjustmentParametersHandle): LevelsAdjustmentChannelParameters;
        setChannelParameters(self: LevelsAdjustmentParametersHandle, channel: number, parameters: LevelsAdjustmentChannelParameters): void;
        setMasterParameters(self: LevelsAdjustmentParametersHandle, parameters: LevelsAdjustmentChannelParameters): void;
    }
    export const LevelsAdjustmentParametersApi: LevelsAdjustmentParametersApi;

}
