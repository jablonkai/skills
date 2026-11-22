// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ArtboardInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle } from "affinity:geometry";

    export interface ArtboardInterfaceApi {
        fromNode(node: NodeHandle): ArtboardInterfaceHandle;
        getArtboardBaseBox(self: ArtboardInterfaceHandle): Rectangle;
        getArtboardDescription(self: ArtboardInterfaceHandle): string;
        getArtboardProperties(self: ArtboardInterfaceHandle): ArtboardPropertiesHandle;
        getArtboardSpreadBaseBox(self: ArtboardInterfaceHandle): Rectangle;
        getBaselineGridInterface(self: ArtboardInterfaceHandle): BaselineGridInterfaceHandle;
        getNode(self: ArtboardInterfaceHandle): NodeHandle;
        getPhysicalRootInterface(self: ArtboardInterfaceHandle): PhysicalRootInterfaceHandle;
        getTopOfPageMargin(self: ArtboardInterfaceHandle): number;
        isArtboardEnabled(self: ArtboardInterfaceHandle): boolean;
        isSameObject(self: ArtboardInterfaceHandle, other: ArtboardInterfaceHandle): boolean;
    }
    export const ArtboardInterfaceApi: ArtboardInterfaceApi;

}
