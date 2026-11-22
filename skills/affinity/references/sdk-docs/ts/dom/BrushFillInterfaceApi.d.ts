// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BrushFillInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";
    import { Transform } from "affinity:geometry";

    export interface BrushFillInterfaceApi {
        enumerateDescriptors(self: BrushFillInterfaceHandle, obeyScaleWithObject: boolean, callback: (fillDescriptorRef: FillDescriptorHandle) => EnumerationResult): void;
        fromNode(node: NodeHandle): BrushFillInterfaceHandle;
        getContentType(self: BrushFillInterfaceHandle): ContentType;
        getCurrentDescriptor(self: BrushFillInterfaceHandle, obeyScaleWithObject: boolean): FillDescriptorHandle;
        getCurrentIndex(self: BrushFillInterfaceHandle): number;
        getDescriptor(self: BrushFillInterfaceHandle, index: number, obeyScaleWithObject: boolean): FillDescriptorHandle;
        getDescriptorCount(self: BrushFillInterfaceHandle): number;
        getDomainTransform(self: BrushFillInterfaceHandle): Transform;
        getNode(self: BrushFillInterfaceHandle): NodeHandle;
        getSubSelection(self: BrushFillInterfaceHandle, index: number): SubSelectionHandle;
        getSubSelectionCount(self: BrushFillInterfaceHandle): number;
        isBrushFillVisible(self: BrushFillInterfaceHandle, minAlpha: number): boolean;
        isNoFill(self: BrushFillInterfaceHandle): boolean;
    }
    export const BrushFillInterfaceApi: BrushFillInterfaceApi;

}
