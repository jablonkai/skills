// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ContainerNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ContainerNodeDefinitionApi extends Omit<ColouredLogicalNodeDefinitionApi, "fromNodeDefinition"> {
        createDefault(): ContainerNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ContainerNodeDefinitionHandle;
    }
    export const ContainerNodeDefinitionApi: ContainerNodeDefinitionApi;

}
