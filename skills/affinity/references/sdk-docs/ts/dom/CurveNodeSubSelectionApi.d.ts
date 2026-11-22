// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CurveNodeSubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface CurveNodeSubSelectionApi extends SubSelectionApi {
        clone(self: CurveNodeSubSelectionHandle): CurveNodeSubSelectionHandle;
        cloneAndAddItems(self: CurveNodeSubSelectionHandle, items: CurveNodeSubSelectionItem[]): CurveNodeSubSelectionHandle;
        cloneAndRemoveCurves(self: CurveNodeSubSelectionHandle, curveIDs: number[]): CurveNodeSubSelectionHandle;
        cloneAndRemoveItems(self: CurveNodeSubSelectionHandle, items: CurveNodeSubSelectionItem[]): CurveNodeSubSelectionHandle;
        cloneAsCurveNodeSubSelection(self: CurveNodeSubSelectionHandle): CurveNodeSubSelectionHandle;
        create(items: CurveNodeSubSelectionItem[]): CurveNodeSubSelectionHandle;
        enumerateItems(self: CurveNodeSubSelectionHandle, callback: (item: CurveNodeSubSelectionItem) => EnumerationResult): void;
        enumerateItemsWithCurveID(self: CurveNodeSubSelectionHandle, curveID: number, callback: (item: CurveNodeSubSelectionItem) => EnumerationResult): void;
        fromSubSelection(subSelection: SubSelectionHandle): CurveNodeSubSelectionHandle;
        getItem(self: CurveNodeSubSelectionHandle, index: number): CurveNodeSubSelectionItem;
        getItemCount(self: CurveNodeSubSelectionHandle): number;
        isEmpty(self: CurveNodeSubSelectionHandle): boolean;
    }
    export const CurveNodeSubSelectionApi: CurveNodeSubSelectionApi;

}
