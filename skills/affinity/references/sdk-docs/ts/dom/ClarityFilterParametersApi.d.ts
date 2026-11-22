// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ClarityFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ClarityFilterParametersApi {
        create(): ClarityFilterParametersHandle;
        getStrength(self: ClarityFilterParametersHandle): number;
        setStrength(self: ClarityFilterParametersHandle, strength: number): void;
    }
    export const ClarityFilterParametersApi: ClarityFilterParametersApi;

}
