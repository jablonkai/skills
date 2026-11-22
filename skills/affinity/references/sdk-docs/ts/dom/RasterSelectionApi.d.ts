// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RasterSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RasterSelectionApi {
        isCurrentPixelSelection(self: RasterSelectionHandle): boolean;
        isSelectAllOrNone(self: RasterSelectionHandle): boolean;
        isSelectNone(self: RasterSelectionHandle): boolean;
    }
    export const RasterSelectionApi: RasterSelectionApi;

}
