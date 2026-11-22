// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TextNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TextNodeDefinitionApi extends Omit<PhysicalNodeDefinitionApi, "fromNodeDefinition"> {
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): TextNodeDefinitionHandle;
    }
    export const TextNodeDefinitionApi: TextNodeDefinitionApi;

}
