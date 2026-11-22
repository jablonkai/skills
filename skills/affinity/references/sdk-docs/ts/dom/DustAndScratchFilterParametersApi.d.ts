// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DustAndScratchFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DustAndScratchFilterParametersApi {
        create(): DustAndScratchFilterParametersHandle;
        getIsChannelTolerance(self: DustAndScratchFilterParametersHandle): boolean;
        getRadius(self: DustAndScratchFilterParametersHandle): number;
        getTolerance(self: DustAndScratchFilterParametersHandle): number;
        setIsChannelTolerance(self: DustAndScratchFilterParametersHandle, isChannelTolerance: boolean): void;
        setRadius(self: DustAndScratchFilterParametersHandle, radius: number): void;
        setTolerance(self: DustAndScratchFilterParametersHandle, tolerance: number): void;
    }
    export const DustAndScratchFilterParametersApi: DustAndScratchFilterParametersApi;

}
