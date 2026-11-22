// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SelectionItemApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface SelectionItemApi {
        enumerateSubSelections(self: SelectionItemHandle, callback: (subSelectionRef: SubSelectionHandle) => EnumerationResult): void;
        getNode(self: SelectionItemHandle): NodeHandle;
        getSubSelection(self: SelectionItemHandle, index: number): SubSelectionHandle;
        getSubSelectionCount(self: SelectionItemHandle): number;
        getSubSelectionOfType(self: SelectionItemHandle, type: SubSelectionType): SubSelectionHandle;
    }
    export const SelectionItemApi: SelectionItemApi;

}
