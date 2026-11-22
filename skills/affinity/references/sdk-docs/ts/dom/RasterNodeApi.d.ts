// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RasterNodeApi extends Omit<PhysicalNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): RasterNodeHandle;
        getRasterInterface(self: RasterNodeHandle): RasterInterfaceHandle;
        isExtendEmpty(node: RasterNodeHandle): boolean;
    }
    export const RasterNodeApi: RasterNodeApi;

}
