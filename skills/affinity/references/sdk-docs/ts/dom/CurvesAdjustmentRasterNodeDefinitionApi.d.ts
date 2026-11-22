// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CurvesAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { ColourSpaceType } from "affinity:colours";

    export interface CurvesAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: CurvesAdjustmentParametersHandle, colourSpace: ColourSpaceType): CurvesAdjustmentRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): CurvesAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): CurvesAdjustmentRasterNodeDefinitionHandle;
        getColourSpace(node: CurvesAdjustmentRasterNodeDefinitionHandle): ColourSpaceType;
        getParameters(node: CurvesAdjustmentRasterNodeDefinitionHandle): CurvesAdjustmentParametersHandle;
        setColourSpace(node: CurvesAdjustmentRasterNodeDefinitionHandle, colourSpace: ColourSpaceType): void;
        setParameters(node: CurvesAdjustmentRasterNodeDefinitionHandle, parameters: CurvesAdjustmentParametersHandle): void;
    }
    export const CurvesAdjustmentRasterNodeDefinitionApi: CurvesAdjustmentRasterNodeDefinitionApi;

}
