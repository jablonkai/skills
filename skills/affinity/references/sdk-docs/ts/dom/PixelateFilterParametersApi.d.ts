// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PixelateFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PixelateFilterParametersApi {
        create(): PixelateFilterParametersHandle;
        getQuantisation(self: PixelateFilterParametersHandle): number;
        setQuantisation(self: PixelateFilterParametersHandle, quantisation: number): void;
    }
    export const PixelateFilterParametersApi: PixelateFilterParametersApi;

}
