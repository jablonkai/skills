// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ArtboardPropertiesApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ArtboardPropertiesApi {
        getMarginsInterface(self: ArtboardPropertiesHandle): MarginsInterfaceHandle;
        getNode(self: ArtboardPropertiesHandle): NodeHandle;
        getPhysicalRootPropertiesInterface(self: ArtboardPropertiesHandle): PhysicalRootPropertiesInterfaceHandle;
    }
    export const ArtboardPropertiesApi: ArtboardPropertiesApi;

}
