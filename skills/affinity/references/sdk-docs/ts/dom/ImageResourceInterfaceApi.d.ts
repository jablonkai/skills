// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ImageResourceInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Size } from "affinity:geometry";
    import { RasterFormat } from "affinity:raster";

    export interface ImageResourceInterfaceApi {
        canEditOriginalImage(self: ImageResourceInterfaceHandle): boolean;
        createFileTypeName(self: ImageResourceInterfaceHandle): string;
        fromNode(nodeHandle: NodeHandle): ImageResourceInterfaceHandle;
        getArtboard(self: ImageResourceInterfaceHandle): string;
        getColourFormat(self: ImageResourceInterfaceHandle, allowRemote: boolean): RasterFormat;
        getFileType(self: ImageResourceInterfaceHandle): FileType;
        getFileTypeName(self: ImageResourceInterfaceHandle): string;
        getICCProfile(self: ImageResourceInterfaceHandle): string;
        getImageFilePath(self: ImageResourceInterfaceHandle): string;
        getImageFileSize(self: ImageResourceInterfaceHandle, asBigInt: boolean): number;
        getImagePlacement(self: ImageResourceInterfaceHandle): ImagePlacement;
        getLargeThumbnail(self: ImageResourceInterfaceHandle, format: RasterFormat, colourProfileSet: ColourProfileSetHandle): RasterObjectHandle;
        getMasterPage(self: ImageResourceInterfaceHandle): string;
        getModifiedTime(self: ImageResourceInterfaceHandle, asBigInt: boolean): number;
        getNode(self: ImageResourceInterfaceHandle): NodeHandle;
        getOriginalDPI(self: ImageResourceInterfaceHandle): number;
        getOriginalSize(self: ImageResourceInterfaceHandle): Size;
        getPage(self: ImageResourceInterfaceHandle): number;
        getPlacedSize(self: ImageResourceInterfaceHandle): Size;
        getResourceNode(self: ImageResourceInterfaceHandle): NodeHandle;
        getSmallThumbnail(self: ImageResourceInterfaceHandle, format: RasterFormat, colourProfileSet: ColourProfileSetHandle): RasterObjectHandle;
        isOnArtboard(self: ImageResourceInterfaceHandle): boolean;
        saveOriginalFile(self: ImageResourceInterfaceHandle, path: string): string;
    }
    export const ImageResourceInterfaceApi: ImageResourceInterfaceApi;

}
