// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TransformInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Transform } from "affinity:geometry";

    export interface TransformInterfaceApi {
        fromNode(node: NodeHandle): TransformInterfaceHandle;
        getDomainTransform(self: TransformInterfaceHandle): Transform;
        getFocalPoint(self: TransformInterfaceHandle): FocalPoint;
        getFrameTextScale(self: TransformInterfaceHandle): Transform;
        getNode(self: TransformInterfaceHandle): NodeHandle;
        getStoryPinPathTransform(self: TransformInterfaceHandle): Transform;
        getTextFrameScaleToDomainTransform(self: TransformInterfaceHandle): Transform;
        getTransform(self: TransformInterfaceHandle, forceConstraints: boolean): Transform;
        getUnconstrainedTransform(self: TransformInterfaceHandle): Transform;
        prefersAspectRatioLockedResize(self: TransformInterfaceHandle): boolean;
    }
    export const TransformInterfaceApi: TransformInterfaceApi;

}
