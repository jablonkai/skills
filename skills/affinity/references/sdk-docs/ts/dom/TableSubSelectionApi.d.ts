// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TableSubSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";
    import { Point, Rectangle } from "affinity:geometry";
    import { TableAxis } from "affinity:story";

    export interface TableSubSelectionApi extends SubSelectionApi {
        enumerateCells(self: TableSubSelectionHandle, callback: (cell: Point) => EnumerationResult): void;
        enumerateEdges(self: TableSubSelectionHandle, tableAxis: TableAxis, tableEdgeSelector: TableEdgeSelector, callback: (edge: Point) => EnumerationResult): void;
        fromSubSelection(subSelection: SubSelectionHandle): TableSubSelectionHandle;
        getAnchor(self: TableSubSelectionHandle): Point;
        getBoundingBox(self: TableSubSelectionHandle): Rectangle;
        getCaret(self: TableSubSelectionHandle): Point;
        isEmpty(self: TableSubSelectionHandle): boolean;
        isRectangle(self: TableSubSelectionHandle): boolean;
    }
    export const TableSubSelectionApi: TableSubSelectionApi;

}
