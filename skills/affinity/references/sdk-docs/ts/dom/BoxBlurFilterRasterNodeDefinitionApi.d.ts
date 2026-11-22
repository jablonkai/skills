// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BoxBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BoxBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: BoxBlurFilterParametersHandle): BoxBlurFilterRasterNodeDefinitionHandle;
        createDefault(): BoxBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): BoxBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: BoxBlurFilterRasterNodeDefinitionHandle): BoxBlurFilterParametersHandle;
        setParameters(self: BoxBlurFilterRasterNodeDefinitionHandle, parameters: BoxBlurFilterParametersHandle): void;
    }
    export const BoxBlurFilterRasterNodeDefinitionApi: BoxBlurFilterRasterNodeDefinitionApi;

}
