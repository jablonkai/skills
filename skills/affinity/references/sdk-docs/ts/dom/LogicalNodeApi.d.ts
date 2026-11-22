// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LogicalNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface LogicalNodeApi extends NodeApi {
        fromNode(node: NodeHandle): LogicalNodeHandle;
        getBrushFillInterface(self: LogicalNodeHandle): BrushFillInterfaceHandle;
        getLineStyleInterface(self: LogicalNodeHandle): LineStyleInterfaceHandle;
        getTransparencyInterface(self: LogicalNodeHandle): TransparencyInterfaceHandle;
        hasNonMaskChildren(self: LogicalNodeHandle): boolean;
        hasNonMaskOrAdjustmentChildren(self: LogicalNodeHandle): boolean;
    }
    export const LogicalNodeApi: LogicalNodeApi;

}
