// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ColourBalanceAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ColourBalanceAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: ColourBalanceAdjustmentParametersHandle): ColourBalanceAdjustmentRasterNodeDefinitionHandle;
        createDefault(): ColourBalanceAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ColourBalanceAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: ColourBalanceAdjustmentRasterNodeDefinitionHandle): ColourBalanceAdjustmentParametersHandle;
        setParameters(node: ColourBalanceAdjustmentRasterNodeDefinitionHandle, parameters: ColourBalanceAdjustmentParametersHandle): void;
    }
    export const ColourBalanceAdjustmentRasterNodeDefinitionApi: ColourBalanceAdjustmentRasterNodeDefinitionApi;

}
