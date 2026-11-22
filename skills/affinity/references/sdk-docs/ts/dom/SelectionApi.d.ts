// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface SelectionApi {
        addItem(self: SelectionHandle, selectionItem: SelectionItemHandle): void;
        addNode(self: SelectionHandle, node: NodeHandle): boolean;
        addSelectable(self: SelectionHandle, selectable: SelectableHandle): boolean;
        addSubSelectionForNode(self: SelectionHandle, node: NodeHandle, subSelection: SubSelectionHandle): boolean;
        clear(self: SelectionHandle): void;
        containsItem(self: SelectionHandle, itemOrNull: SelectionItemHandle | null): boolean;
        containsNode(self: SelectionHandle, nodeOrNull: NodeHandle | null): boolean;
        createEmpty(document: DocumentHandle): SelectionHandle;
        getCount(self: SelectionHandle): number;
        getFirstSubSelectionOfType(self: SelectionHandle, type: SubSelectionType): SubSelectionHandle;
        getHasKeyObject(self: SelectionHandle): boolean;
        getItem(self: SelectionHandle, index: number): SelectionItemHandle;
        removeNested(self: SelectionHandle): void;
        setHasKeyObject(self: SelectionHandle, hasKeyObject: boolean): void;
    }
    export const SelectionApi: SelectionApi;

}
