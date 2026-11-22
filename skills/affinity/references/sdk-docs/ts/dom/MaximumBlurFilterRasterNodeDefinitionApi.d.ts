// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MaximumBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MaximumBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: MaximumBlurFilterParametersHandle): MaximumBlurFilterRasterNodeDefinitionHandle;
        createDefault(): MaximumBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): MaximumBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: MaximumBlurFilterRasterNodeDefinitionHandle): MaximumBlurFilterParametersHandle;
        setParameters(self: MaximumBlurFilterRasterNodeDefinitionHandle, parameters: MaximumBlurFilterParametersHandle): void;
    }
    export const MaximumBlurFilterRasterNodeDefinitionApi: MaximumBlurFilterRasterNodeDefinitionApi;

}
