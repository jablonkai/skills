// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PolyCurveNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PolyCurveNodeDefinitionApi extends Omit<VectorNodeDefinitionApi, "fromNodeDefinition"> {
        create(polyCurve: PolyCurveHandle, brushFillDescriptorOrNull: FillDescriptorHandle | null, lineFillDescriptorOrNull: FillDescriptorHandle | null, lineStyleDescriptorOrNull: LineStyleDescriptorHandle | null, transparencyFillDescriptorOrNull: FillDescriptorHandle | null): PolyCurveNodeDefinitionHandle;
        createDefault(): PolyCurveNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): PolyCurveNodeDefinitionHandle;
        getCurves(self: PolyCurveNodeDefinitionHandle): PolyCurveHandle;
        setCurves(self: PolyCurveNodeDefinitionHandle, polyCurve: PolyCurveHandle): void;
    }
    export const PolyCurveNodeDefinitionApi: PolyCurveNodeDefinitionApi;

}
