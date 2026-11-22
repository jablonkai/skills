// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VoronoiFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VoronoiFilterParametersApi {
        create(): VoronoiFilterParametersHandle;
        getCellSize(self: VoronoiFilterParametersHandle): number;
        getLineWidth(self: VoronoiFilterParametersHandle): number;
        setCellSize(self: VoronoiFilterParametersHandle, cellSize: number): void;
        setLineWidth(self: VoronoiFilterParametersHandle, lineWidth: number): void;
    }
    export const VoronoiFilterParametersApi: VoronoiFilterParametersApi;

}
