// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BlendOptionsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BlendOptionsApi {
        getChannelSourceLayerRanges(self: BlendOptionsHandle, channel: number): SplineHandle;
        getChannelUnderlyingCompositionRanges(self: BlendOptionsHandle, channel: number): SplineHandle;
        getGamma(self: BlendOptionsHandle): number;
        getMasterSourceLayerRanges(self: BlendOptionsHandle): SplineHandle;
        getMasterUnderlyingCompositionRanges(self: BlendOptionsHandle): SplineHandle;
        setChannelSourceLayerRanges(self: BlendOptionsHandle, channel: number, spline: SplineHandle): void;
        setChannelUnderlyingCompositionRanges(self: BlendOptionsHandle, channel: number, spline: SplineHandle): void;
        setGamma(self: BlendOptionsHandle, gamma: number): void;
        setMasterSourceLayerRanges(self: BlendOptionsHandle, spline: SplineHandle): void;
        setMasterUnderlyingCompositionRanges(self: BlendOptionsHandle, spline: SplineHandle): void;
    }
    export const BlendOptionsApi: BlendOptionsApi;

}
