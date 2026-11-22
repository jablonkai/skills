// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VectorNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VectorNodeDefinitionApi extends Omit<PhysicalNodeDefinitionApi, "fromNodeDefinition"> {
        addBrushFillDescriptor(self: VectorNodeDefinitionHandle, brushFillDescriptorOrNull: FillDescriptorHandle | null): void;
        addLineDescriptors(self: VectorNodeDefinitionHandle, lineFillDescriptorOrNull: FillDescriptorHandle | null, lineStyleDescriptorOrNull: LineStyleDescriptorHandle | null): void;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): VectorNodeDefinitionHandle;
        getBrushFillDescriptor(self: VectorNodeDefinitionHandle, index: number): FillDescriptorHandle;
        getBrushFillDescriptorCount(self: VectorNodeDefinitionHandle): number;
        getCurrentBrushFillIndex(self: VectorNodeDefinitionHandle): number;
        getCurrentLineDescriptorsIndex(self: VectorNodeDefinitionHandle): number;
        getLineDescriptors(self: VectorNodeDefinitionHandle, index: number): LineDescriptors;
        getLineDescriptorsCount(self: VectorNodeDefinitionHandle): number;
        getPictureFrameEnabled(self: VectorNodeDefinitionHandle): boolean;
        getTransparencyDescriptor(self: VectorNodeDefinitionHandle): FillDescriptorHandle;
        insertBrushFillDescriptor(self: VectorNodeDefinitionHandle, index: number, brushFillDescriptorOrNull: FillDescriptorHandle | null): void;
        insertLineDescriptors(self: VectorNodeDefinitionHandle, index: number, lineFillDescriptorOrNull: FillDescriptorHandle | null, lineStyleDescriptorOrNull: LineStyleDescriptorHandle | null): void;
        removeBrushFillDescriptor(self: VectorNodeDefinitionHandle, index: number): void;
        removeLineDescriptors(self: VectorNodeDefinitionHandle, index: number): void;
        setBrushFillDescriptor(self: VectorNodeDefinitionHandle, index: number, brushFillDescriptorOrNull: FillDescriptorHandle | null): void;
        setCurrentBrushFillIndex(self: VectorNodeDefinitionHandle, index: number): void;
        setCurrentLineDescriptorsIndex(self: VectorNodeDefinitionHandle, index: number): void;
        setLineDescriptors(self: VectorNodeDefinitionHandle, index: number, lineFillDescriptorOrNull: FillDescriptorHandle | null, lineStyleDescriptorOrNull: LineStyleDescriptorHandle | null): void;
        setPictureFrameEnabled(self: VectorNodeDefinitionHandle, pictureFrameEnabled: boolean): void;
        setTransparencyDescriptor(self: VectorNodeDefinitionHandle, transparencyFillDescriptorOrNull: FillDescriptorHandle | null): void;
    }
    export const VectorNodeDefinitionApi: VectorNodeDefinitionApi;

}
