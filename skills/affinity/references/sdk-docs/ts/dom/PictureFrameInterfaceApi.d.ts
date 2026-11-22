// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PictureFrameInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle } from "affinity:geometry";

    export interface PictureFrameInterfaceApi {
        calculateAnchor(self: PictureFrameInterfaceHandle, childNode: NodeHandle, hintAnchor: SpatialAnchor): SpatialAnchor;
        calculateConstraints(self: PictureFrameInterfaceHandle, childNode: NodeHandle, hintConstraintType: ConstraintType): ConstraintType;
        fromNode(node: NodeHandle): PictureFrameInterfaceHandle;
        getAnchor(self: PictureFrameInterfaceHandle): SpatialAnchor;
        getDataMergeFieldId(self: PictureFrameInterfaceHandle): string;
        getDescription(self: PictureFrameInterfaceHandle): string;
        getFrameContents(self: PictureFrameInterfaceHandle): NodeHandle;
        getNode(self: PictureFrameInterfaceHandle): NodeHandle;
        getOriginalContentRectangle(self: PictureFrameInterfaceHandle): Rectangle;
        hasFrameContents(self: PictureFrameInterfaceHandle): boolean;
        isClearFillOnPopulate(self: PictureFrameInterfaceHandle): boolean;
        isEnabled(self: PictureFrameInterfaceHandle): boolean;
    }
    export const PictureFrameInterfaceApi: PictureFrameInterfaceApi;

}
