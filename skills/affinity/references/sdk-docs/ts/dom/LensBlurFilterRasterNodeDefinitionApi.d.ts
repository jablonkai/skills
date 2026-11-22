// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LensBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface LensBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: LensBlurFilterParametersHandle): LensBlurFilterRasterNodeDefinitionHandle;
        createDefault(): LensBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): LensBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: LensBlurFilterRasterNodeDefinitionHandle): LensBlurFilterParametersHandle;
        setParameters(self: LensBlurFilterRasterNodeDefinitionHandle, parameters: LensBlurFilterParametersHandle): void;
    }
    export const LensBlurFilterRasterNodeDefinitionApi: LensBlurFilterRasterNodeDefinitionApi;

}
