// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PinchPunchFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PinchPunchFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: PinchPunchFilterParametersHandle): PinchPunchFilterRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): PinchPunchFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): PinchPunchFilterRasterNodeDefinitionHandle;
        getParameters(node: PinchPunchFilterRasterNodeDefinitionHandle): PinchPunchFilterParametersHandle;
        setParameters(node: PinchPunchFilterRasterNodeDefinitionHandle, parameters: PinchPunchFilterParametersHandle): void;
    }
    export const PinchPunchFilterRasterNodeDefinitionApi: PinchPunchFilterRasterNodeDefinitionApi;

}
