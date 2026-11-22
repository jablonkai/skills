// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MotionBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MotionBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: MotionBlurFilterParametersHandle): MotionBlurFilterRasterNodeDefinitionHandle;
        createDefault(): MotionBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): MotionBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: MotionBlurFilterRasterNodeDefinitionHandle): MotionBlurFilterParametersHandle;
        setParameters(self: MotionBlurFilterRasterNodeDefinitionHandle, parameters: MotionBlurFilterParametersHandle): void;
    }
    export const MotionBlurFilterRasterNodeDefinitionApi: MotionBlurFilterRasterNodeDefinitionApi;

}
