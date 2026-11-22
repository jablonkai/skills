// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MeasurementNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { UnitType } from "affinity:common";
    import { Endpoints } from "affinity:geometry";

    export interface MeasurementNodeApi extends Omit<VectorNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): MeasurementNodeHandle;
        getAnnotationOffset(self: MeasurementNodeHandle): number;
        getDecimalPlaces(self: MeasurementNodeHandle): number;
        getDisplayUnitType(self: MeasurementNodeHandle): UnitType;
        getFactor(self: MeasurementNodeHandle): number;
        getScaledUnitType(self: MeasurementNodeHandle): UnitType;
        getShowEndpointMarkers(self: MeasurementNodeHandle): boolean;
        getSpreadDistance(self: MeasurementNodeHandle): number;
        getSpreadEndpoints(self: MeasurementNodeHandle): Endpoints;
        getUseDocumentPrecision(self: MeasurementNodeHandle): boolean;
    }
    export const MeasurementNodeApi: MeasurementNodeApi;

}
