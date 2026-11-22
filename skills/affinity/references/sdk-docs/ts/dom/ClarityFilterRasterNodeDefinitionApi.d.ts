// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ClarityFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ClarityFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: ClarityFilterParametersHandle): ClarityFilterRasterNodeDefinitionHandle;
        createDefault(): ClarityFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ClarityFilterRasterNodeDefinitionHandle;
        getParameters(node: ClarityFilterRasterNodeDefinitionHandle): ClarityFilterParametersHandle;
        setParameters(node: ClarityFilterRasterNodeDefinitionHandle, parameters: ClarityFilterParametersHandle): void;
    }
    export const ClarityFilterRasterNodeDefinitionApi: ClarityFilterRasterNodeDefinitionApi;

}
