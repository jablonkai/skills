// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", NodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle, Transform } from "affinity:geometry";

    export interface NodeApi extends SelectableApi {
        fromSelectable(selectable: SelectableHandle): NodeHandle;
        getBaseBoxInterface(self: NodeHandle): BaseBoxInterfaceHandle;
        getBaseToSpreadTransform(self: NodeHandle): Transform;
        getBlendModeInterface(self: NodeHandle): BlendModeInterfaceHandle;
        getContentExtentsBox(self: NodeHandle, includeInvisible: boolean, includeOffCurvePoints: boolean): Rectangle;
        getContentExtentsBoxOfChildren(self: NodeHandle, includeInvisible: boolean, includeOffCurvePoints: boolean): Rectangle;
        getDescriptionInterface(self: NodeHandle): DescriptionInterfaceHandle;
        getDocument(self: NodeHandle): DocumentHandle;
        getEditabilityInterface(self: NodeHandle): EditabilityInterfaceHandle;
        getExactSpreadBaseBox(self: NodeHandle): Rectangle;
        getExactSpreadVisibleBox(self: NodeHandle, includeParentEffects: boolean, considerParentClips: boolean): Rectangle;
        getExportableInterface(self: NodeHandle): ExportableInterfaceHandle;
        getFirstChild(self: NodeHandle, nodeChildType: NodeChildType): NodeHandle;
        getLastChild(self: NodeHandle, nodeChildType: NodeChildType): NodeHandle;
        getLayerEffectsInterface(self: NodeHandle): LayerEffectsInterfaceHandle;
        getLineBox(self: NodeHandle, includeClips: boolean): Rectangle;
        getLocalBaseBox(self: NodeHandle, includeClips: boolean): Rectangle;
        getLocalLineBox(self: NodeHandle, includeClips: boolean): Rectangle;
        getLocalToSpreadTransform(self: NodeHandle): Transform;
        getLocalVisibleBox(self: NodeHandle): Rectangle;
        getNextSibling(self: NodeHandle): NodeHandle;
        getNodeId(self: NodeHandle): number;
        getParent(self: NodeHandle): NodeHandle;
        getPreviousSibling(self: NodeHandle): NodeHandle;
        getSpreadBaseBox(self: NodeHandle, includeClips: boolean): Rectangle;
        getSpreadLineBox(self: NodeHandle, includeClips: boolean): Rectangle;
        getSpreadToBaseTransform(self: NodeHandle): Transform;
        getSpreadVisibleBox(self: NodeHandle, includeParentEffects: boolean): Rectangle;
        getTagInterface(self: NodeHandle): TagInterfaceHandle;
        getTransformInterface(self: NodeHandle): TransformInterfaceHandle;
        getTransformedLineBox(self: NodeHandle, transform: Transform, scalarTransform: Transform, includeClips: boolean): Rectangle;
        getVisibilityInterface(self: NodeHandle): VisibilityInterfaceHandle;
        isSameNode(self: NodeHandle, other: NodeHandle): boolean;
        moveToFirstChild(self: NodeHandle, nodeChildType: NodeChildType): void;
        moveToLastChild(self: NodeHandle, nodeChildType: NodeChildType): void;
        moveToNextSibling(self: NodeHandle): void;
        moveToParent(self: NodeHandle): void;
        moveToPreviousSibling(self: NodeHandle): void;
    }
    export const NodeApi: NodeApi;

}
