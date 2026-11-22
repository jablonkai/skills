// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", NormalsAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface NormalsAdjustmentParametersApi {
        create(): NormalsAdjustmentParametersHandle;
        getFlipX(self: NormalsAdjustmentParametersHandle): boolean;
        getFlipY(self: NormalsAdjustmentParametersHandle): boolean;
        getRotation(self: NormalsAdjustmentParametersHandle): number;
        getScale(self: NormalsAdjustmentParametersHandle): number;
        setFlipX(self: NormalsAdjustmentParametersHandle, flipX: boolean): void;
        setFlipY(self: NormalsAdjustmentParametersHandle, flipY: boolean): void;
        setRotation(self: NormalsAdjustmentParametersHandle, rotation: number): void;
        setScale(self: NormalsAdjustmentParametersHandle, scale: number): void;
    }
    export const NormalsAdjustmentParametersApi: NormalsAdjustmentParametersApi;

}
