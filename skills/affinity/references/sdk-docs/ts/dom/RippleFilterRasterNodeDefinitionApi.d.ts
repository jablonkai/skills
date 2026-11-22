// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RippleFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RippleFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: RippleFilterParametersHandle): RippleFilterRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): RippleFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): RippleFilterRasterNodeDefinitionHandle;
        getParameters(node: RippleFilterRasterNodeDefinitionHandle): RippleFilterParametersHandle;
        setParameters(node: RippleFilterRasterNodeDefinitionHandle, parameters: RippleFilterParametersHandle): void;
    }
    export const RippleFilterRasterNodeDefinitionApi: RippleFilterRasterNodeDefinitionApi;

}
