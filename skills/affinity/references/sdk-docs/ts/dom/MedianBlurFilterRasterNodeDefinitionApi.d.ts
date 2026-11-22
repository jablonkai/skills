// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MedianBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MedianBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: MedianBlurFilterParametersHandle): MedianBlurFilterRasterNodeDefinitionHandle;
        createDefault(): MedianBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): MedianBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: MedianBlurFilterRasterNodeDefinitionHandle): MedianBlurFilterParametersHandle;
        setParameters(self: MedianBlurFilterRasterNodeDefinitionHandle, parameters: MedianBlurFilterParametersHandle): void;
    }
    export const MedianBlurFilterRasterNodeDefinitionApi: MedianBlurFilterRasterNodeDefinitionApi;

}
