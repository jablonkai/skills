// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LineFillSubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface LineFillSubSelectionApi extends SubSelectionApi {
        clone(self: LineFillSubSelectionHandle): LineFillSubSelectionHandle;
        cloneAsLineFillSubSelection(self: LineFillSubSelectionHandle): LineFillSubSelectionHandle;
        fromSubSelection(subSelection: SubSelectionHandle): LineFillSubSelectionHandle;
        getIndex(self: LineFillSubSelectionHandle): number;
    }
    export const LineFillSubSelectionApi: LineFillSubSelectionApi;

}
