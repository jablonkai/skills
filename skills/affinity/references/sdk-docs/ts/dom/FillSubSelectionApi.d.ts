// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", FillSubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface FillSubSelectionApi extends SubSelectionApi {
        clone(self: FillSubSelectionHandle): FillSubSelectionHandle;
        cloneAsFillSubSelection(self: FillSubSelectionHandle): FillSubSelectionHandle;
        fromSubSelection(subSelection: SubSelectionHandle): FillSubSelectionHandle;
        getIndex(self: FillSubSelectionHandle): number;
    }
    export const FillSubSelectionApi: FillSubSelectionApi;

}
