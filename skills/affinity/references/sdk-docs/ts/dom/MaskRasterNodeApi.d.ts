// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MaskRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MaskRasterNodeApi extends Omit<EnclosureRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): MaskRasterNodeHandle;
    }
    export const MaskRasterNodeApi: MaskRasterNodeApi;

}
