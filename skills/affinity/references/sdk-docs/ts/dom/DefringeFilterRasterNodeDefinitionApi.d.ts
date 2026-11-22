// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DefringeFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DefringeFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: DefringeFilterParametersHandle): DefringeFilterRasterNodeDefinitionHandle;
        createDefault(): DefringeFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): DefringeFilterRasterNodeDefinitionHandle;
        getParameters(node: DefringeFilterRasterNodeDefinitionHandle): DefringeFilterParametersHandle;
        setParameters(node: DefringeFilterRasterNodeDefinitionHandle, parameters: DefringeFilterParametersHandle): void;
    }
    export const DefringeFilterRasterNodeDefinitionApi: DefringeFilterRasterNodeDefinitionApi;

}
