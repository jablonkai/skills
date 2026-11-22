// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LevelsAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { ColourSpaceType } from "affinity:colours";

    export interface LevelsAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: LevelsAdjustmentParametersHandle, colourSpace: ColourSpaceType): LevelsAdjustmentRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): LevelsAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): LevelsAdjustmentRasterNodeDefinitionHandle;
        getColourSpace(node: LevelsAdjustmentRasterNodeDefinitionHandle): ColourSpaceType;
        getParameters(node: LevelsAdjustmentRasterNodeDefinitionHandle): LevelsAdjustmentParametersHandle;
        setColourSpace(node: LevelsAdjustmentRasterNodeDefinitionHandle, colourSpace: ColourSpaceType): void;
        setParameters(node: LevelsAdjustmentRasterNodeDefinitionHandle, parameters: LevelsAdjustmentParametersHandle): void;
    }
    export const LevelsAdjustmentRasterNodeDefinitionApi: LevelsAdjustmentRasterNodeDefinitionApi;

}
