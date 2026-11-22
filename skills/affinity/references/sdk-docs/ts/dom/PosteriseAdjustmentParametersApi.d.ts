// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PosteriseAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PosteriseAdjustmentParametersApi {
        create(): PosteriseAdjustmentParametersHandle;
        getLevels(self: PosteriseAdjustmentParametersHandle): number;
        setLevels(self: PosteriseAdjustmentParametersHandle, levels: number): void;
    }
    export const PosteriseAdjustmentParametersApi: PosteriseAdjustmentParametersApi;

}
