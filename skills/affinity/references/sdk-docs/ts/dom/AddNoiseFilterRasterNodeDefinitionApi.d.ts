// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", AddNoiseFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface AddNoiseFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: AddNoiseFilterParametersHandle): AddNoiseFilterRasterNodeDefinitionHandle;
        createDefault(): AddNoiseFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): AddNoiseFilterRasterNodeDefinitionHandle;
        getParameters(node: AddNoiseFilterRasterNodeDefinitionHandle): AddNoiseFilterParametersHandle;
        setParameters(node: AddNoiseFilterRasterNodeDefinitionHandle, parameters: AddNoiseFilterParametersHandle): void;
    }
    export const AddNoiseFilterRasterNodeDefinitionApi: AddNoiseFilterRasterNodeDefinitionApi;

}
