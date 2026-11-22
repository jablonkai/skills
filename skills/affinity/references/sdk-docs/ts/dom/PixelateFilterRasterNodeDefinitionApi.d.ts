// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PixelateFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PixelateFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: PixelateFilterParametersHandle): PixelateFilterRasterNodeDefinitionHandle;
        createDefault(): PixelateFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): PixelateFilterRasterNodeDefinitionHandle;
        getParameters(self: PixelateFilterRasterNodeDefinitionHandle): PixelateFilterParametersHandle;
        setParameters(self: PixelateFilterRasterNodeDefinitionHandle, parameters: PixelateFilterParametersHandle): void;
    }
    export const PixelateFilterRasterNodeDefinitionApi: PixelateFilterRasterNodeDefinitionApi;

}
