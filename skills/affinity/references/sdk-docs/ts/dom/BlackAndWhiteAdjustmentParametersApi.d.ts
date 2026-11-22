// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BlackAndWhiteAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BlackAndWhiteAdjustmentParametersApi {
        create(): BlackAndWhiteAdjustmentParametersHandle;
        getBlue(self: BlackAndWhiteAdjustmentParametersHandle): number;
        getCyan(self: BlackAndWhiteAdjustmentParametersHandle): number;
        getGreen(self: BlackAndWhiteAdjustmentParametersHandle): number;
        getMagenta(self: BlackAndWhiteAdjustmentParametersHandle): number;
        getRed(self: BlackAndWhiteAdjustmentParametersHandle): number;
        getYellow(self: BlackAndWhiteAdjustmentParametersHandle): number;
        setBlue(self: BlackAndWhiteAdjustmentParametersHandle, blue: number): void;
        setCyan(self: BlackAndWhiteAdjustmentParametersHandle, cyan: number): void;
        setGreen(self: BlackAndWhiteAdjustmentParametersHandle, green: number): void;
        setMagenta(self: BlackAndWhiteAdjustmentParametersHandle, magenta: number): void;
        setRed(self: BlackAndWhiteAdjustmentParametersHandle, red: number): void;
        setYellow(self: BlackAndWhiteAdjustmentParametersHandle, yellow: number): void;
    }
    export const BlackAndWhiteAdjustmentParametersApi: BlackAndWhiteAdjustmentParametersApi;

}
