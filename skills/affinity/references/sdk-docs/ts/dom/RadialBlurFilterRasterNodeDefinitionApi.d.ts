// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RadialBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RadialBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: RadialBlurFilterParametersHandle): RadialBlurFilterRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): RadialBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): RadialBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: RadialBlurFilterRasterNodeDefinitionHandle): RadialBlurFilterParametersHandle;
        setParameters(self: RadialBlurFilterRasterNodeDefinitionHandle, parameters: RadialBlurFilterParametersHandle): void;
    }
    export const RadialBlurFilterRasterNodeDefinitionApi: RadialBlurFilterRasterNodeDefinitionApi;

}
