// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SpreadNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";
    import { Point, Rectangle } from "affinity:geometry";

    export interface SpreadNodeApi extends Omit<PhysicalNodeApi, "fromNode"> {
        enumerateArtboards(self: SpreadNodeHandle, callback: (artboardRef: ArtboardInterfaceHandle) => EnumerationResult): void;
        fromNode(node: NodeHandle): SpreadNodeHandle;
        getArtboard(self: SpreadNodeHandle, index: number): ArtboardInterfaceHandle;
        getArtboardCount(self: SpreadNodeHandle): number;
        getFirstPageIndex(self: SpreadNodeHandle): number;
        getLastPageIndex(self: SpreadNodeHandle): number;
        getPageIndexOfBox(self: SpreadNodeHandle, rect: Rectangle, relativeToSpread: boolean): number;
        getPageIndexOfPoint(self: SpreadNodeHandle, point: Point, relativeToSpread: boolean): number;
        getPhysicalRootInterface(self: SpreadNodeHandle): PhysicalRootInterfaceHandle;
        getPhysicalRootPropertiesInterface(self: SpreadNodeHandle): PhysicalRootPropertiesInterfaceHandle;
        getSpreadExtents(self: SpreadNodeHandle, includeSpread: boolean, includeBleed: boolean, includeChildren: boolean): Rectangle;
        isFirstPage(self: SpreadNodeHandle): boolean;
        isLastPage(self: SpreadNodeHandle): boolean;
    }
    export const SpreadNodeApi: SpreadNodeApi;

}
