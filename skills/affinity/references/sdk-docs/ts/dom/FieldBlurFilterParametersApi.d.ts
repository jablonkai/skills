// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", FieldBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface FieldBlurFilterParametersApi {
        addBlurItem(self: FieldBlurFilterParametersHandle, blurItemParameters: FieldBlurItemParameters): number;
        create(): FieldBlurFilterParametersHandle;
        deleteBlurItem(self: FieldBlurFilterParametersHandle, index: number): void;
        enumerateBlurItems(self: FieldBlurFilterParametersHandle, callback: (index: number, blurItemParameters: FieldBlurItemParameters) => EnumerationResult): void;
        getBlurItem(self: FieldBlurFilterParametersHandle, index: number): FieldBlurItemParameters;
        getBlurItemCount(self: FieldBlurFilterParametersHandle): number;
        getGlobalRadius(self: FieldBlurFilterParametersHandle): number;
        setGlobalRadius(self: FieldBlurFilterParametersHandle, radius: number): void;
    }
    export const FieldBlurFilterParametersApi: FieldBlurFilterParametersApi;

}
