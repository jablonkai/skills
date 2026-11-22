// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DiffuseFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DiffuseFilterParametersApi {
        create(): DiffuseFilterParametersHandle;
        getIntensity(self: DiffuseFilterParametersHandle): number;
        setIntensity(self: DiffuseFilterParametersHandle, intensity: number): void;
    }
    export const DiffuseFilterParametersApi: DiffuseFilterParametersApi;

}
