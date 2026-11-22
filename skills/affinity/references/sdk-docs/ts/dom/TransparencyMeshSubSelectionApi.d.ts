// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TransparencyMeshSubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface TransparencyMeshSubSelectionApi extends SubSelectionApi {
        enumerateItems(self: TransparencyMeshSubSelectionHandle, callback: (meshSubSelectionItem: MeshSubSelectionItem) => EnumerationResult): void;
        fromSubSelection(subSelection: SubSelectionHandle): TransparencyMeshSubSelectionHandle;
        getItemCount(self: TransparencyMeshSubSelectionHandle): number;
        isEmpty(self: TransparencyMeshSubSelectionHandle): boolean;
    }
    export const TransparencyMeshSubSelectionApi: TransparencyMeshSubSelectionApi;

}
