// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CurvesInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Transform, WindingOrder } from "affinity:geometry";

    export interface CurvesInterfaceApi {
        fromNode(node: NodeHandle): CurvesInterfaceHandle;
        getCorneredCurves(self: CurvesInterfaceHandle): PolyCurveHandle;
        getCurves(self: CurvesInterfaceHandle): PolyCurveHandle;
        getDomainTransform(self: CurvesInterfaceHandle): Transform;
        getNode(self: CurvesInterfaceHandle): NodeHandle;
        getPolyPolyCurves(self: CurvesInterfaceHandle): PolyPolyCurveHandle;
        getSubSelection(self: CurvesInterfaceHandle, subSelectionType: SubSelectionType, index: number): SubSelectionHandle;
        getSubSelectionCount(self: CurvesInterfaceHandle, subSelectionType: SubSelectionType): number;
        getWindingOrder(self: CurvesInterfaceHandle): WindingOrder;
        isMutable(self: CurvesInterfaceHandle): boolean;
    }
    export const CurvesInterfaceApi: CurvesInterfaceApi;

}
