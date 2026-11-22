// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", GaussianBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface GaussianBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: GaussianBlurFilterParametersHandle): GaussianBlurFilterRasterNodeDefinitionHandle;
        createDefault(): GaussianBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): GaussianBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: GaussianBlurFilterRasterNodeDefinitionHandle): GaussianBlurFilterParametersHandle;
        setParameters(self: GaussianBlurFilterRasterNodeDefinitionHandle, parameters: GaussianBlurFilterParametersHandle): void;
    }
    export const GaussianBlurFilterRasterNodeDefinitionApi: GaussianBlurFilterRasterNodeDefinitionApi;

}
