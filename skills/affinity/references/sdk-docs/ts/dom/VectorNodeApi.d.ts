// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VectorNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VectorNodeApi extends Omit<PhysicalNodeApi, "fromNode"> {
        canBeExpressedAsVectorClip(self: VectorNodeHandle): boolean;
        fromNode(node: NodeHandle): VectorNodeHandle;
        getBrushFillInterface(self: VectorNodeHandle): BrushFillInterfaceHandle;
        getCompoundOperationInterface(self: VectorNodeHandle): CompoundOperationInterfaceHandle;
        getCurvesInterface(self: VectorNodeHandle): CurvesInterfaceHandle;
        getLineStyleInterface(self: VectorNodeHandle): LineStyleInterfaceHandle;
        getPictureFrameInterface(self: VectorNodeHandle): PictureFrameInterfaceHandle;
        getTransparencyInterface(self: VectorNodeHandle): TransparencyInterfaceHandle;
    }
    export const VectorNodeApi: VectorNodeApi;

}
