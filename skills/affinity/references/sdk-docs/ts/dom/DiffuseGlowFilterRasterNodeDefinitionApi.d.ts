// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DiffuseGlowFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DiffuseGlowFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: DiffuseGlowFilterParametersHandle): DiffuseGlowFilterRasterNodeDefinitionHandle;
        createDefault(): DiffuseGlowFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): DiffuseGlowFilterRasterNodeDefinitionHandle;
        getParameters(self: DiffuseGlowFilterRasterNodeDefinitionHandle): DiffuseGlowFilterParametersHandle;
        setParameters(self: DiffuseGlowFilterRasterNodeDefinitionHandle, parameters: DiffuseGlowFilterParametersHandle): void;
    }
    export const DiffuseGlowFilterRasterNodeDefinitionApi: DiffuseGlowFilterRasterNodeDefinitionApi;

}
