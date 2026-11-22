// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", WhiteBalanceAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface WhiteBalanceAdjustmentParametersApi {
        create(): WhiteBalanceAdjustmentParametersHandle;
        getTint(self: WhiteBalanceAdjustmentParametersHandle): number;
        getWhiteBalance(self: WhiteBalanceAdjustmentParametersHandle): number;
        setTint(self: WhiteBalanceAdjustmentParametersHandle, tint: number): void;
        setWhiteBalance(self: WhiteBalanceAdjustmentParametersHandle, whiteBalance: number): void;
    }
    export const WhiteBalanceAdjustmentParametersApi: WhiteBalanceAdjustmentParametersApi;

}
