// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DrawingScaleApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult, UnitType, UnitValue } from "affinity:common";

    export interface DrawingScaleApi {
        create(left: UnitValue, right: UnitValue): DrawingScaleHandle;
        createFromIntegers(left: number, right: number, simplifyFaction: boolean): DrawingScaleHandle;
        createFromString(scaleString: string, simplifyFaction: boolean, simplifyDecimalPlaces: number, allowOneToOne: boolean): DrawingScaleHandle;
        enumerateDefaults(unitType: UnitType, callback: (drawingScale: DrawingScaleHandle) => EnumerationResult): void;
        getAsString(self: DrawingScaleHandle, useTightFormat: boolean, showUnits: boolean, indicateApproximations: boolean): string;
        getLeftValue(self: DrawingScaleHandle): UnitValue;
        getRightValue(self: DrawingScaleHandle): UnitValue;
    }
    export const DrawingScaleApi: DrawingScaleApi;

}
