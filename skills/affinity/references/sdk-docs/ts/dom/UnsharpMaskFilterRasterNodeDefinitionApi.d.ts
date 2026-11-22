// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", UnsharpMaskFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface UnsharpMaskFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: UnsharpMaskFilterParametersHandle): UnsharpMaskFilterRasterNodeDefinitionHandle;
        createDefault(): UnsharpMaskFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): UnsharpMaskFilterRasterNodeDefinitionHandle;
        getParameters(node: UnsharpMaskFilterRasterNodeDefinitionHandle): UnsharpMaskFilterParametersHandle;
        setParameters(node: UnsharpMaskFilterRasterNodeDefinitionHandle, parameters: UnsharpMaskFilterParametersHandle): void;
    }
    export const UnsharpMaskFilterRasterNodeDefinitionApi: UnsharpMaskFilterRasterNodeDefinitionApi;

}
