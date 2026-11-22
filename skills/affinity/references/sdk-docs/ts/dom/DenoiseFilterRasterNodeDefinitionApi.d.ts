// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DenoiseFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DenoiseFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: DenoiseFilterParametersHandle): DenoiseFilterRasterNodeDefinitionHandle;
        createDefault(): DenoiseFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): DenoiseFilterRasterNodeDefinitionHandle;
        getParameters(node: DenoiseFilterRasterNodeDefinitionHandle): DenoiseFilterParametersHandle;
        setParameters(node: DenoiseFilterRasterNodeDefinitionHandle, parameters: DenoiseFilterParametersHandle): void;
    }
    export const DenoiseFilterRasterNodeDefinitionApi: DenoiseFilterRasterNodeDefinitionApi;

}
