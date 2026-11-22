// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TransparencySubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TransparencySubSelectionApi extends SubSelectionApi {
        clone(self: TransparencySubSelectionHandle): TransparencySubSelectionHandle;
        cloneAsTransparencySubSelection(self: TransparencySubSelectionHandle): TransparencySubSelectionHandle;
        fromSubSelection(subSelection: SubSelectionHandle): TransparencySubSelectionHandle;
        getIndex(self: TransparencySubSelectionHandle): number;
    }
    export const TransparencySubSelectionApi: TransparencySubSelectionApi;

}
