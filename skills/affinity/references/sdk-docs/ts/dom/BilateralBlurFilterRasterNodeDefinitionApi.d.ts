// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BilateralBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BilateralBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: BilateralBlurFilterParametersHandle): BilateralBlurFilterRasterNodeDefinitionHandle;
        createDefault(): BilateralBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): BilateralBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: BilateralBlurFilterRasterNodeDefinitionHandle): BilateralBlurFilterParametersHandle;
        setParameters(self: BilateralBlurFilterRasterNodeDefinitionHandle, parameters: BilateralBlurFilterParametersHandle): void;
    }
    export const BilateralBlurFilterRasterNodeDefinitionApi: BilateralBlurFilterRasterNodeDefinitionApi;

}
