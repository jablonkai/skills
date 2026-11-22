// Type declarations for the Affinity JavaScript SDK: module "affinity:os".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:os" {

    export interface OSApi {
        getArchitecture(): string;
        getEol(): string;
        getMachine(): string;
        getOSName(): string;
        getOSVersion(): string;
        getPlatform(): string;
        getRelease(): string;
    }
    export const OSApi: OSApi;

}
