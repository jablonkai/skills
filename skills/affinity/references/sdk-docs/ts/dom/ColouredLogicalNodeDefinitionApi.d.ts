// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ColouredLogicalNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ColouredLogicalNodeDefinitionApi extends Omit<LogicalNodeDefinitionApi, "fromNodeDefinition"> {
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ColouredLogicalNodeDefinitionHandle;
    }
    export const ColouredLogicalNodeDefinitionApi: ColouredLogicalNodeDefinitionApi;

}
