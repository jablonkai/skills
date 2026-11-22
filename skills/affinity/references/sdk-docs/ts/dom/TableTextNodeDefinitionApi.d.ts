// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TableTextNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle, Size } from "affinity:geometry";

    export interface TableTextNodeDefinitionApi extends Omit<TextNodeDefinitionApi, "fromNodeDefinition"> {
        create(box: Rectangle, size: Size): TableTextNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): TableTextNodeDefinitionHandle;
    }
    export const TableTextNodeDefinitionApi: TableTextNodeDefinitionApi;

}
