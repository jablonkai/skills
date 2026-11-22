// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LineFillMeshSubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface LineFillMeshSubSelectionApi extends SubSelectionApi {
        enumerateItems(self: LineFillMeshSubSelectionHandle, callback: (meshSubSelectionItem: MeshSubSelectionItem) => EnumerationResult): void;
        fromSubSelection(subSelection: SubSelectionHandle): LineFillMeshSubSelectionHandle;
        getItemCount(self: LineFillMeshSubSelectionHandle): number;
        isEmpty(self: LineFillMeshSubSelectionHandle): boolean;
    }
    export const LineFillMeshSubSelectionApi: LineFillMeshSubSelectionApi;

}
