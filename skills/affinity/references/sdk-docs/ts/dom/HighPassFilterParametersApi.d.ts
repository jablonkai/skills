// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HighPassFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface HighPassFilterParametersApi {
        create(): HighPassFilterParametersHandle;
        getIsMonochrome(self: HighPassFilterParametersHandle): boolean;
        getRadius(self: HighPassFilterParametersHandle): number;
        setIsMonochrome(self: HighPassFilterParametersHandle, isMonochrome: boolean): void;
        setRadius(self: HighPassFilterParametersHandle, radius: number): void;
    }
    export const HighPassFilterParametersApi: HighPassFilterParametersApi;

}
