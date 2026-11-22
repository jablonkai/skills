// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BrightnessContrastAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BrightnessContrastAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: BrightnessContrastAdjustmentParametersHandle): BrightnessContrastAdjustmentRasterNodeDefinitionHandle;
        createDefault(): BrightnessContrastAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): BrightnessContrastAdjustmentRasterNodeDefinitionHandle;
        getParameters(self: BrightnessContrastAdjustmentRasterNodeDefinitionHandle): BrightnessContrastAdjustmentParametersHandle;
        setParameters(self: BrightnessContrastAdjustmentRasterNodeDefinitionHandle, parameters: BrightnessContrastAdjustmentParametersHandle): void;
    }
    export const BrightnessContrastAdjustmentRasterNodeDefinitionApi: BrightnessContrastAdjustmentRasterNodeDefinitionApi;

}
