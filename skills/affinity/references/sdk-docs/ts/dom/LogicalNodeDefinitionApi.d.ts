// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LogicalNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface LogicalNodeDefinitionApi extends NodeDefinitionApi {
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): LogicalNodeDefinitionHandle;
    }
    export const LogicalNodeDefinitionApi: LogicalNodeDefinitionApi;

}
