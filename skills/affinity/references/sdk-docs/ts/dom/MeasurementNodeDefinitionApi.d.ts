// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MeasurementNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { UnitType } from "affinity:common";
    import { Endpoints, Point } from "affinity:geometry";

    export interface MeasurementNodeDefinitionApi extends Omit<VectorNodeDefinitionApi, "fromNodeDefinition"> {
        create(start: Point, end: Point, factor: number, unitType: UnitType): MeasurementNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): MeasurementNodeDefinitionHandle;
        getAnnotationOffset(self: MeasurementNodeDefinitionHandle): number;
        getDecimalPlaces(self: MeasurementNodeDefinitionHandle): number;
        getEndpoints(self: MeasurementNodeDefinitionHandle): Endpoints;
        getFactor(self: MeasurementNodeDefinitionHandle): number;
        getLabelGlyphAtts(self: MeasurementNodeDefinitionHandle): GlyphAttsHandle;
        getScaledUnitType(self: MeasurementNodeDefinitionHandle): UnitType;
        getShowEndpointMarkers(self: MeasurementNodeDefinitionHandle): boolean;
        getUseDocumentPrecision(self: MeasurementNodeDefinitionHandle): boolean;
        setAnnotationOffset(self: MeasurementNodeDefinitionHandle, offset: number): void;
        setDisplayPrecision(self: MeasurementNodeDefinitionHandle, useDocumentPrecision: boolean, decimalPlaces: number): void;
        setEndpoints(self: MeasurementNodeDefinitionHandle, start: Point, end: Point): void;
        setFactor(self: MeasurementNodeDefinitionHandle, factor: number): void;
        setLabelGlyphAtts(self: MeasurementNodeDefinitionHandle, glyphAttsOrNull: GlyphAttsHandle | null): void;
        setScaledUnitType(self: MeasurementNodeDefinitionHandle, unitType: UnitType): void;
        setShowEndpointMarkers(self: MeasurementNodeDefinitionHandle, show: boolean): void;
    }
    export const MeasurementNodeDefinitionApi: MeasurementNodeDefinitionApi;

}
