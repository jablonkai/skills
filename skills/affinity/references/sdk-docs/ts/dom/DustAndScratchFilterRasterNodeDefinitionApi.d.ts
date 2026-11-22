// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DustAndScratchFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DustAndScratchFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: DustAndScratchFilterParametersHandle): DustAndScratchFilterRasterNodeDefinitionHandle;
        createDefault(): DustAndScratchFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): DustAndScratchFilterRasterNodeDefinitionHandle;
        getParameters(node: DustAndScratchFilterRasterNodeDefinitionHandle): DustAndScratchFilterParametersHandle;
        setParameters(node: DustAndScratchFilterRasterNodeDefinitionHandle, parameters: DustAndScratchFilterParametersHandle): void;
    }
    export const DustAndScratchFilterRasterNodeDefinitionApi: DustAndScratchFilterRasterNodeDefinitionApi;

}
