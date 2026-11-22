// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MarginsInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MarginsInterfaceApi {
        getMarginFill(self: MarginsInterfaceHandle): FillDescriptorHandle;
        getMargins(self: MarginsInterfaceHandle): LTRB;
        getUseMargins(self: MarginsInterfaceHandle): boolean;
    }
    export const MarginsInterfaceApi: MarginsInterfaceApi;

}
