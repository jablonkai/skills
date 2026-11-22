// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ExposureAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ExposureAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: ExposureAdjustmentParametersHandle): ExposureAdjustmentRasterNodeDefinitionHandle;
        createDefault(): ExposureAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ExposureAdjustmentRasterNodeDefinitionHandle;
        getParameters(self: ExposureAdjustmentRasterNodeDefinitionHandle): ExposureAdjustmentParametersHandle;
        setParameters(self: ExposureAdjustmentRasterNodeDefinitionHandle, parameters: ExposureAdjustmentParametersHandle): void;
    }
    export const ExposureAdjustmentRasterNodeDefinitionApi: ExposureAdjustmentRasterNodeDefinitionApi;

}
