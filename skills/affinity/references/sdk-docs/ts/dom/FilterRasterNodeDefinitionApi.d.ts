// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", FilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface FilterRasterNodeDefinitionApi extends Omit<EnclosureRasterNodeDefinitionApi, "fromNodeDefinition"> {
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): FilterRasterNodeDefinitionHandle;
        getPreserveAlpha(self: FilterRasterNodeDefinitionHandle): boolean;
        setPreserveAlpha(self: FilterRasterNodeDefinitionHandle, preserve: boolean): void;
    }
    export const FilterRasterNodeDefinitionApi: FilterRasterNodeDefinitionApi;

}
