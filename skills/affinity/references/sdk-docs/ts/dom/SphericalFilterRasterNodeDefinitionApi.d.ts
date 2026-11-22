// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SphericalFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface SphericalFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: SphericalFilterParametersHandle): SphericalFilterRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): SphericalFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): SphericalFilterRasterNodeDefinitionHandle;
        getParameters(node: SphericalFilterRasterNodeDefinitionHandle): SphericalFilterParametersHandle;
        setParameters(node: SphericalFilterRasterNodeDefinitionHandle, parameters: SphericalFilterParametersHandle): void;
    }
    export const SphericalFilterRasterNodeDefinitionApi: SphericalFilterRasterNodeDefinitionApi;

}
