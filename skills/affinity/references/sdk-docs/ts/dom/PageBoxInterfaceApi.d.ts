// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PageBoxInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle } from "affinity:geometry";

    export interface PageBoxInterfaceApi {
        getPageBoundingBox(self: PageBoxInterfaceHandle, pageBoundingBoxType: PageBoundingBoxType): Rectangle;
    }
    export const PageBoxInterfaceApi: PageBoxInterfaceApi;

}
