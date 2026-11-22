// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DepthOfFieldFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DepthOfFieldFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: DepthOfFieldFilterParametersHandle): DepthOfFieldFilterRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): DepthOfFieldFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): DepthOfFieldFilterRasterNodeDefinitionHandle;
        getParameters(self: DepthOfFieldFilterRasterNodeDefinitionHandle): DepthOfFieldFilterParametersHandle;
        setParameters(self: DepthOfFieldFilterRasterNodeDefinitionHandle, parameters: DepthOfFieldFilterParametersHandle): void;
    }
    export const DepthOfFieldFilterRasterNodeDefinitionApi: DepthOfFieldFilterRasterNodeDefinitionApi;

}
