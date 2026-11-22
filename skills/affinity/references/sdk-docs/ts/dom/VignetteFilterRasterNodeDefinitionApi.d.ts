// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VignetteFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VignetteFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: VignetteFilterParametersHandle): VignetteFilterRasterNodeDefinitionHandle;
        createDefault(): VignetteFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): VignetteFilterRasterNodeDefinitionHandle;
        getParameters(node: VignetteFilterRasterNodeDefinitionHandle): VignetteFilterParametersHandle;
        setParameters(node: VignetteFilterRasterNodeDefinitionHandle, parameters: VignetteFilterParametersHandle): void;
    }
    export const VignetteFilterRasterNodeDefinitionApi: VignetteFilterRasterNodeDefinitionApi;

}
