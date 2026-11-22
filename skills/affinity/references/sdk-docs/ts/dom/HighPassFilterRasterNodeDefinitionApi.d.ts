// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HighPassFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface HighPassFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: HighPassFilterParametersHandle): HighPassFilterRasterNodeDefinitionHandle;
        createDefault(): HighPassFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): HighPassFilterRasterNodeDefinitionHandle;
        getParameters(node: HighPassFilterRasterNodeDefinitionHandle): HighPassFilterParametersHandle;
        setParameters(node: HighPassFilterRasterNodeDefinitionHandle, parameters: HighPassFilterParametersHandle): void;
    }
    export const HighPassFilterRasterNodeDefinitionApi: HighPassFilterRasterNodeDefinitionApi;

}
