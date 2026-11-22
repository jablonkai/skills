// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LoadDwgOptionsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { UnitType } from "affinity:common";

    export interface LoadDwgOptionsApi extends Omit<LoadDocumentOptionsApi, "clone" | "createDefault"> {
        clone(self: LoadDwgOptionsHandle): LoadDwgOptionsHandle;
        cloneAsLoadDwgOptions(self: LoadDwgOptionsHandle): LoadDwgOptionsHandle;
        createDefault(): LoadDwgOptionsHandle;
        getBackgroundColour(self: LoadDwgOptionsHandle): ColourHandle;
        getLayoutSelection(self: LoadDwgOptionsHandle): LoadDwgLayoutSelection;
        getModelUnits(self: LoadDwgOptionsHandle): UnitType;
        getOverrideColour(self: LoadDwgOptionsHandle): ColourHandle;
        getOverrideLineWeights(self: LoadDwgOptionsHandle): boolean;
        getRemoveHiddenItems(self: LoadDwgOptionsHandle): boolean;
        getSelectedLayoutName(self: LoadDwgOptionsHandle): string;
        getShowHandles(self: LoadDwgOptionsHandle): boolean;
        setBackgroundColour(self: LoadDwgOptionsHandle, backgroundColour: ColourHandle): void;
        setLayoutSelectionToAllPages(self: LoadDwgOptionsHandle): void;
        setLayoutSelectionToModel(self: LoadDwgOptionsHandle): void;
        setLayoutSelectionToSingle(self: LoadDwgOptionsHandle, layoutName: string): void;
        setModelUnits(self: LoadDwgOptionsHandle, unitType: UnitType): void;
        setOverrideColour(self: LoadDwgOptionsHandle, overrideColour: ColourHandle): void;
        setOverrideLineWeights(self: LoadDwgOptionsHandle, overrideLineWeights: boolean): void;
        setRemoveHiddenItems(self: LoadDwgOptionsHandle, removeHiddenItems: boolean): void;
        setShowHandles(self: LoadDwgOptionsHandle, showHandles: boolean): void;
    }
    export const LoadDwgOptionsApi: LoadDwgOptionsApi;

}
