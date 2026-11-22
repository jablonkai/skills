// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", FillMeshSubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface FillMeshSubSelectionApi extends SubSelectionApi {
        enumerateItems(self: FillMeshSubSelectionHandle, callback: (meshSubSelectionItem: MeshSubSelectionItem) => EnumerationResult): void;
        fromSubSelection(subSelection: SubSelectionHandle): FillMeshSubSelectionHandle;
        getItemCount(self: FillMeshSubSelectionHandle): number;
        isEmpty(self: FillMeshSubSelectionHandle): boolean;
    }
    export const FillMeshSubSelectionApi: FillMeshSubSelectionApi;

}
