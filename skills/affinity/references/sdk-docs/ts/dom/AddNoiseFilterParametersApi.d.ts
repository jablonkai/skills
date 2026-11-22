// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", AddNoiseFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface AddNoiseFilterParametersApi {
        create(): AddNoiseFilterParametersHandle;
        getIntensity(self: AddNoiseFilterParametersHandle): number;
        getIsMonochromatic(self: AddNoiseFilterParametersHandle): boolean;
        getNoiseType(self: AddNoiseFilterParametersHandle): AddNoiseType;
        setIntensity(self: AddNoiseFilterParametersHandle, intensity: number): void;
        setIsMonochromatic(self: AddNoiseFilterParametersHandle, isMonochromatic: boolean): void;
        setNoiseType(self: AddNoiseFilterParametersHandle, noiseType: AddNoiseType): void;
    }
    export const AddNoiseFilterParametersApi: AddNoiseFilterParametersApi;

}
