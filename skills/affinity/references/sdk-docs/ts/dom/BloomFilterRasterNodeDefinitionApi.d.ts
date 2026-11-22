// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BloomFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BloomFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: BloomFilterParametersHandle): BloomFilterRasterNodeDefinitionHandle;
        createDefault(): BloomFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): BloomFilterRasterNodeDefinitionHandle;
        getParameters(self: BloomFilterRasterNodeDefinitionHandle): BloomFilterParametersHandle;
        setParameters(self: BloomFilterRasterNodeDefinitionHandle, parameters: BloomFilterParametersHandle): void;
    }
    export const BloomFilterRasterNodeDefinitionApi: BloomFilterRasterNodeDefinitionApi;

}
