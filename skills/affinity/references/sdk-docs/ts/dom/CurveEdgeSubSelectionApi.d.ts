// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CurveEdgeSubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface CurveEdgeSubSelectionApi extends SubSelectionApi {
        clone(self: CurveEdgeSubSelectionHandle): CurveEdgeSubSelectionHandle;
        cloneAndAddItems(self: CurveEdgeSubSelectionHandle, items: CurveEdgeSubSelectionItem[]): CurveEdgeSubSelectionHandle;
        cloneAndRemoveCurves(self: CurveEdgeSubSelectionHandle, curveIDs: number[]): CurveEdgeSubSelectionHandle;
        cloneAndRemoveItems(self: CurveEdgeSubSelectionHandle, items: CurveEdgeSubSelectionItem[]): CurveEdgeSubSelectionHandle;
        cloneAsCurveEdgeSubSelection(self: CurveEdgeSubSelectionHandle): CurveEdgeSubSelectionHandle;
        create(items: CurveEdgeSubSelectionItem[]): CurveEdgeSubSelectionHandle;
        enumerateItems(self: CurveEdgeSubSelectionHandle, callback: (item: CurveEdgeSubSelectionItem) => EnumerationResult): void;
        enumerateItemsWithCurveID(self: CurveEdgeSubSelectionHandle, curveID: number, callback: (item: CurveEdgeSubSelectionItem) => EnumerationResult): void;
        fromSubSelection(subSelection: SubSelectionHandle): CurveEdgeSubSelectionHandle;
        getItem(self: CurveEdgeSubSelectionHandle, index: number): CurveEdgeSubSelectionItem;
        getItemCount(self: CurveEdgeSubSelectionHandle): number;
        isEmpty(self: CurveEdgeSubSelectionHandle): boolean;
    }
    export const CurveEdgeSubSelectionApi: CurveEdgeSubSelectionApi;

}
