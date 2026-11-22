// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DiffuseFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DiffuseFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: DiffuseFilterParametersHandle): DiffuseFilterRasterNodeDefinitionHandle;
        createDefault(): DiffuseFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): DiffuseFilterRasterNodeDefinitionHandle;
        getParameters(node: DiffuseFilterRasterNodeDefinitionHandle): DiffuseFilterParametersHandle;
        setParameters(node: DiffuseFilterRasterNodeDefinitionHandle, parameters: DiffuseFilterParametersHandle): void;
    }
    export const DiffuseFilterRasterNodeDefinitionApi: DiffuseFilterRasterNodeDefinitionApi;

}
