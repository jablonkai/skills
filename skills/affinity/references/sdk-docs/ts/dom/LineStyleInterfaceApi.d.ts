// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LineStyleInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";
    import { Transform } from "affinity:geometry";

    export interface LineStyleInterfaceApi {
        enumerateDescriptors(self: LineStyleInterfaceHandle, obeyScaleWithObject: boolean, callback: (fillDescriptorRef: FillDescriptorHandle, lineStyleDescriptorRef: LineStyleDescriptorHandle) => EnumerationResult): void;
        enumerateFillDescriptors(self: LineStyleInterfaceHandle, obeyScaleWithObject: boolean, callback: (fillDescriptorRef: FillDescriptorHandle) => EnumerationResult): void;
        enumerateLineStyleDescriptors(self: LineStyleInterfaceHandle, callback: (lineStyleDescriptorRef: LineStyleDescriptorHandle) => EnumerationResult): void;
        fromNode(node: NodeHandle): LineStyleInterfaceHandle;
        getContentType(self: LineStyleInterfaceHandle): ContentType;
        getCurrentDescriptors(self: LineStyleInterfaceHandle, obeyScaleWithObject: boolean): LineDescriptors;
        getCurrentFillDescriptor(self: LineStyleInterfaceHandle, obeyScaleWithObject: boolean): FillDescriptorHandle;
        getCurrentIndex(self: LineStyleInterfaceHandle): number;
        getCurrentLineStyleDescriptor(self: LineStyleInterfaceHandle): LineStyleDescriptorHandle;
        getDescriptorCount(self: LineStyleInterfaceHandle): number;
        getDescriptors(self: LineStyleInterfaceHandle, index: number, obeyScaleWithObject: boolean): LineDescriptors;
        getDomainTransform(self: LineStyleInterfaceHandle): Transform;
        getFillDescriptor(self: LineStyleInterfaceHandle, index: number, obeyScaleWithObject: boolean): FillDescriptorHandle;
        getLineStyleDescriptor(self: LineStyleInterfaceHandle, index: number): LineStyleDescriptorHandle;
        getNode(self: LineStyleInterfaceHandle): NodeHandle;
        getScalarDomainTransform(self: LineStyleInterfaceHandle): Transform;
        isLineStyleVisible(self: LineStyleInterfaceHandle): boolean;
        isNoFill(self: LineStyleInterfaceHandle): boolean;
    }
    export const LineStyleInterfaceApi: LineStyleInterfaceApi;

}
