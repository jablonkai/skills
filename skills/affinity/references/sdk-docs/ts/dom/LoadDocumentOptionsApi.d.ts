// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LoadDocumentOptionsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { ColourSpaceType } from "affinity:colours";
    import { RasterFormat } from "affinity:raster";

    export interface LoadDocumentOptionsApi {
        clone(self: LoadDocumentOptionsHandle): LoadDocumentOptionsHandle;
        cloneAsLoadDocumentOptions(self: LoadDocumentOptionsHandle): LoadDocumentOptionsHandle;
        createDefault(): LoadDocumentOptionsHandle;
        getColourSpace(self: LoadDocumentOptionsHandle): ColourSpaceType;
        getDpi(self: LoadDocumentOptionsHandle): number;
        getFormat(self: LoadDocumentOptionsHandle): RasterFormat;
        getHostDpi(self: LoadDocumentOptionsHandle): number;
        getLoadMode(self: LoadDocumentOptionsHandle): DocumentLoadMode;
        setColourSpace(self: LoadDocumentOptionsHandle, colourSpace: ColourSpaceType): void;
        setDpi(self: LoadDocumentOptionsHandle, dpi: number): void;
        setFormat(self: LoadDocumentOptionsHandle, format: RasterFormat): void;
        setHostDpi(self: LoadDocumentOptionsHandle, dpi: number): void;
        setLoadMode(self: LoadDocumentOptionsHandle, loadMode: DocumentLoadMode): void;
        setPassword(self: LoadDocumentOptionsHandle, password: string): void;
    }
    export const LoadDocumentOptionsApi: LoadDocumentOptionsApi;

}
