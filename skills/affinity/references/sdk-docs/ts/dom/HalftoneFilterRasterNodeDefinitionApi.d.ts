// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HalftoneFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface HalftoneFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: HalftoneFilterParametersHandle): HalftoneFilterRasterNodeDefinitionHandle;
        createDefault(): HalftoneFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): HalftoneFilterRasterNodeDefinitionHandle;
        getParameters(self: HalftoneFilterRasterNodeDefinitionHandle): HalftoneFilterParametersHandle;
        setParameters(self: HalftoneFilterRasterNodeDefinitionHandle, parameters: HalftoneFilterParametersHandle): void;
    }
    export const HalftoneFilterRasterNodeDefinitionApi: HalftoneFilterRasterNodeDefinitionApi;

}
