// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MinimumBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MinimumBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: MinimumBlurFilterParametersHandle): MinimumBlurFilterRasterNodeDefinitionHandle;
        createDefault(): MinimumBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): MinimumBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: MinimumBlurFilterRasterNodeDefinitionHandle): MinimumBlurFilterParametersHandle;
        setParameters(self: MinimumBlurFilterRasterNodeDefinitionHandle, parameters: MinimumBlurFilterParametersHandle): void;
    }
    export const MinimumBlurFilterRasterNodeDefinitionApi: MinimumBlurFilterRasterNodeDefinitionApi;

}
