// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DenoiseFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DenoiseFilterParametersApi {
        create(): DenoiseFilterParametersHandle;
        getColours(self: DenoiseFilterParametersHandle): number;
        getColoursContribution(self: DenoiseFilterParametersHandle): number;
        getLuminance(self: DenoiseFilterParametersHandle): number;
        getLuminanceContribution(self: DenoiseFilterParametersHandle): number;
        getLuminanceDetail(self: DenoiseFilterParametersHandle): number;
        setColours(self: DenoiseFilterParametersHandle, colours: number): void;
        setColoursContribution(self: DenoiseFilterParametersHandle, coloursContribution: number): void;
        setLuminance(self: DenoiseFilterParametersHandle, luminance: number): void;
        setLuminanceContribution(self: DenoiseFilterParametersHandle, luminanceContribution: number): void;
        setLuminanceDetail(self: DenoiseFilterParametersHandle, luminanceDetail: number): void;
    }
    export const DenoiseFilterParametersApi: DenoiseFilterParametersApi;

}
