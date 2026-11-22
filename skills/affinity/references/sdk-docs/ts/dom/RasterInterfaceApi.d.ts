// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RasterInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle, Transform } from "affinity:geometry";
    import { RasterFormat } from "affinity:raster";

    export interface RasterInterfaceApi {
        copyTo(self: RasterInterfaceHandle, rasterObject: RasterObjectHandle, destinationRectangle: Rectangle, sourceX: number, sourceY: number): void;
        createCompatibleBitmap(self: RasterInterfaceHandle, copyContents: boolean): RasterObjectHandle;
        createCompatibleBuffer(self: RasterInterfaceHandle, copyContents: boolean): RasterObjectHandle;
        fromNode(node: NodeHandle): RasterInterfaceHandle;
        getBitmap(self: RasterInterfaceHandle): RasterObjectHandle;
        getDomainTransform(self: RasterInterfaceHandle): Transform;
        getFormat(self: RasterInterfaceHandle): RasterFormat;
        getHeight(self: RasterInterfaceHandle): number;
        getInverseRasterBoundingBox(self: RasterInterfaceHandle): Rectangle;
        getNode(self: RasterInterfaceHandle): NodeHandle;
        getPixelSize(self: RasterInterfaceHandle): number;
        getRasterBoundingBox(self: RasterInterfaceHandle): Rectangle;
        getWidth(self: RasterInterfaceHandle): number;
    }
    export const RasterInterfaceApi: RasterInterfaceApi;

}
