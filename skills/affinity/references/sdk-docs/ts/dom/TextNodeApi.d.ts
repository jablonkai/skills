// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TextNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TextNodeApi extends Omit<PhysicalNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): TextNodeHandle;
        getArtboardInterface(self: TextNodeHandle): ArtboardInterfaceHandle;
        getBrushFillInterface(self: TextNodeHandle): BrushFillInterfaceHandle;
        getCompoundOperationInterface(self: TextNodeHandle): CompoundOperationInterfaceHandle;
        getCurvesInterface(self: TextNodeHandle): CurvesInterfaceHandle;
        getLineStyleInterface(self: TextNodeHandle): LineStyleInterfaceHandle;
        getStoryInterface(self: TextNodeHandle): StoryInterfaceHandle;
        getTextFrameInterface(self: TextNodeHandle): TextFrameInterfaceHandle;
        getTransparencyInterface(self: TextNodeHandle): TransparencyInterfaceHandle;
    }
    export const TextNodeApi: TextNodeApi;

}
