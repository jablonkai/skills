// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BaselineGridOptionsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BaselineGridOptionsApi {
        create(): BaselineGridOptionsHandle;
        getColour(self: BaselineGridOptionsHandle): ColourHandle;
        getRelativeTo(self: BaselineGridOptionsHandle): BaselineGridRelativeTo;
        getSpacing(self: BaselineGridOptionsHandle): number;
        getStart(self: BaselineGridOptionsHandle): number;
        getUseBaselineGrid(self: BaselineGridOptionsHandle): boolean;
        setColour(self: BaselineGridOptionsHandle, colour: ColourHandle): void;
        setRelativeTo(self: BaselineGridOptionsHandle, relativeTo: BaselineGridRelativeTo): void;
        setSpacing(self: BaselineGridOptionsHandle, spacing: number): void;
        setStart(self: BaselineGridOptionsHandle, start: number): void;
        setUseBaselineGrid(self: BaselineGridOptionsHandle, useBaselineGrid: boolean): void;
    }
    export const BaselineGridOptionsApi: BaselineGridOptionsApi;

}
