// Type declarations for the Affinity JavaScript SDK: module "affinity:raster".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:raster" {

    import { CMYKA8, IA16, IA8, LABA16, M16, M8, Mf, RGBA16, RGBA8, RGBAuf } from "affinity:colours";
    import { Rectangle } from "affinity:geometry";

    export enum RasterExtendType {
        Zero,
        Repeat,
        Wrap,
        Mirror,
    }

    export enum RasterFormat {
        RGBA8,
        RGBA16,
        IA8,
        IA16,
        CMYKA8,
        LABA16,
        M8,
        M16,
        EMPTY,
        RGBAUF,
        MF,
    }

    export enum RasterIntent {
        Perceptual,
        RelativeColourimetric,
        Saturation,
        AbsoluteColourimetric,
    }

    export enum RasterObjectType {
        Bitmap,
        Buffer,
        RenderingEngine,
    }

    export enum RasterResamplerType {
        Default,
        BilinearMipmap,
        NearestNeighbourMipmap,
        NearestNeighbour,
        Bilinear,
        Bicubic,
        SeparableLanczos3,
        NonseparableLanczos3,
        AntialiasedNearestNeighbourMipmap,
        Mitchell,
    }

    export interface NodeRenderingEngineOptionsApi {
        clone(self: NodeRenderingEngineOptionsHandle): NodeRenderingEngineOptionsHandle;
        cloneAsNodeRenderingEngineOptions(self: NodeRenderingEngineOptionsHandle): NodeRenderingEngineOptionsHandle;
        create(): NodeRenderingEngineOptionsHandle;
        getAllowDegradedBitmaps(self: NodeRenderingEngineOptionsHandle): boolean;
        getAntialias(self: NodeRenderingEngineOptionsHandle): boolean;
        getClipToSpread(self: NodeRenderingEngineOptionsHandle): boolean;
        getDitherGradients(self: NodeRenderingEngineOptionsHandle): boolean;
        getDownResamplerType(self: NodeRenderingEngineOptionsHandle): RasterResamplerType;
        getDrawBackground(self: NodeRenderingEngineOptionsHandle): boolean;
        getIsIsolatedRendering(self: NodeRenderingEngineOptionsHandle): boolean;
        getIsMaskRenderingMode(self: NodeRenderingEngineOptionsHandle): boolean;
        getIsPerfectClipping(self: NodeRenderingEngineOptionsHandle): boolean;
        getScale(self: NodeRenderingEngineOptionsHandle): number;
        getSourceRect(self: NodeRenderingEngineOptionsHandle): Rectangle;
        getUpResamplerType(self: NodeRenderingEngineOptionsHandle): RasterResamplerType;
        setAllowDegradedBitmaps(self: NodeRenderingEngineOptionsHandle, value: boolean): void;
        setAntialias(self: NodeRenderingEngineOptionsHandle, value: boolean): void;
        setClipToSpread(self: NodeRenderingEngineOptionsHandle, value: boolean): void;
        setDitherGradients(self: NodeRenderingEngineOptionsHandle, value: boolean): void;
        setDownResamplerType(self: NodeRenderingEngineOptionsHandle, value: RasterResamplerType): void;
        setDrawBackground(self: NodeRenderingEngineOptionsHandle, value: boolean): void;
        setIsIsolatedRendering(self: NodeRenderingEngineOptionsHandle, value: boolean): void;
        setIsMaskRenderingMode(self: NodeRenderingEngineOptionsHandle, value: boolean): void;
        setIsPerfectClipping(self: NodeRenderingEngineOptionsHandle, value: boolean): void;
        setScale(self: NodeRenderingEngineOptionsHandle, scale: number): void;
        setSourceRect(self: NodeRenderingEngineOptionsHandle, sourceRectOrNull: Rectangle | null): void;
        setUpResamplerType(self: NodeRenderingEngineOptionsHandle, value: RasterResamplerType): void;
    }
    export const NodeRenderingEngineOptionsApi: NodeRenderingEngineOptionsApi;

    export interface PixelReaderCMYKA8Api {
        create(bitmap: RasterObjectHandle): PixelReaderCMYKA8Handle;
        dispose(self: PixelReaderCMYKA8Handle): void;
        readPixel(self: PixelReaderCMYKA8Handle, x: number, y: number): CMYKA8;
    }
    export const PixelReaderCMYKA8Api: PixelReaderCMYKA8Api;

    export interface PixelReaderIA16Api {
        create(bitmap: RasterObjectHandle): PixelReaderIA16Handle;
        dispose(self: PixelReaderIA16Handle): void;
        readPixel(self: PixelReaderIA16Handle, x: number, y: number): IA16;
    }
    export const PixelReaderIA16Api: PixelReaderIA16Api;

    export interface PixelReaderIA8Api {
        create(bitmap: RasterObjectHandle): PixelReaderIA8Handle;
        dispose(self: PixelReaderIA8Handle): void;
        readPixel(self: PixelReaderIA8Handle, x: number, y: number): IA8;
    }
    export const PixelReaderIA8Api: PixelReaderIA8Api;

    export interface PixelReaderLABA16Api {
        create(bitmap: RasterObjectHandle): PixelReaderLABA16Handle;
        dispose(self: PixelReaderLABA16Handle): void;
        readPixel(self: PixelReaderLABA16Handle, x: number, y: number): LABA16;
    }
    export const PixelReaderLABA16Api: PixelReaderLABA16Api;

    export interface PixelReaderM16Api {
        create(bitmap: RasterObjectHandle): PixelReaderM16Handle;
        dispose(self: PixelReaderM16Handle): void;
        readPixel(self: PixelReaderM16Handle, x: number, y: number): M16;
    }
    export const PixelReaderM16Api: PixelReaderM16Api;

    export interface PixelReaderM8Api {
        create(bitmap: RasterObjectHandle): PixelReaderM8Handle;
        dispose(self: PixelReaderM8Handle): void;
        readPixel(self: PixelReaderM8Handle, x: number, y: number): M8;
    }
    export const PixelReaderM8Api: PixelReaderM8Api;

    export interface PixelReaderMfApi {
        create(bitmap: RasterObjectHandle): PixelReaderMfHandle;
        dispose(self: PixelReaderMfHandle): void;
        readPixel(self: PixelReaderMfHandle, x: number, y: number): Mf;
    }
    export const PixelReaderMfApi: PixelReaderMfApi;

    export interface PixelReaderRGBA16Api {
        create(bitmap: RasterObjectHandle): PixelReaderRGBA16Handle;
        dispose(self: PixelReaderRGBA16Handle): void;
        readPixel(self: PixelReaderRGBA16Handle, x: number, y: number): RGBA16;
    }
    export const PixelReaderRGBA16Api: PixelReaderRGBA16Api;

    export interface PixelReaderRGBA8Api {
        create(bitmap: RasterObjectHandle): PixelReaderRGBA8Handle;
        dispose(self: PixelReaderRGBA8Handle): void;
        readPixel(self: PixelReaderRGBA8Handle, x: number, y: number): RGBA8;
    }
    export const PixelReaderRGBA8Api: PixelReaderRGBA8Api;

    export interface PixelReaderRGBAufApi {
        create(bitmap: RasterObjectHandle): PixelReaderRGBAufHandle;
        dispose(self: PixelReaderRGBAufHandle): void;
        readPixel(self: PixelReaderRGBAufHandle, x: number, y: number): RGBAuf;
    }
    export const PixelReaderRGBAufApi: PixelReaderRGBAufApi;

    export interface PixelReaderWriterCMYKA8Api {
        create(bitmap: RasterObjectHandle): PixelReaderWriterCMYKA8Handle;
        dispose(self: PixelReaderWriterCMYKA8Handle): void;
        readPixel(self: PixelReaderWriterCMYKA8Handle, x: number, y: number): CMYKA8;
        writePixel(self: PixelReaderWriterCMYKA8Handle, x: number, y: number, pixel: CMYKA8): void;
    }
    export const PixelReaderWriterCMYKA8Api: PixelReaderWriterCMYKA8Api;

    export interface PixelReaderWriterIA16Api {
        create(bitmap: RasterObjectHandle): PixelReaderWriterIA16Handle;
        dispose(self: PixelReaderWriterIA16Handle): void;
        readPixel(self: PixelReaderWriterIA16Handle, x: number, y: number): IA16;
        writePixel(self: PixelReaderWriterIA16Handle, x: number, y: number, pixel: IA16): void;
    }
    export const PixelReaderWriterIA16Api: PixelReaderWriterIA16Api;

    export interface PixelReaderWriterIA8Api {
        create(bitmap: RasterObjectHandle): PixelReaderWriterIA8Handle;
        dispose(self: PixelReaderWriterIA8Handle): void;
        readPixel(self: PixelReaderWriterIA8Handle, x: number, y: number): IA8;
        writePixel(self: PixelReaderWriterIA8Handle, x: number, y: number, pixel: IA8): void;
    }
    export const PixelReaderWriterIA8Api: PixelReaderWriterIA8Api;

    export interface PixelReaderWriterLABA16Api {
        create(bitmap: RasterObjectHandle): PixelReaderWriterLABA16Handle;
        dispose(self: PixelReaderWriterLABA16Handle): void;
        readPixel(self: PixelReaderWriterLABA16Handle, x: number, y: number): LABA16;
        writePixel(self: PixelReaderWriterLABA16Handle, x: number, y: number, pixel: LABA16): void;
    }
    export const PixelReaderWriterLABA16Api: PixelReaderWriterLABA16Api;

    export interface PixelReaderWriterM16Api {
        create(bitmap: RasterObjectHandle): PixelReaderWriterM16Handle;
        dispose(self: PixelReaderWriterM16Handle): void;
        readPixel(self: PixelReaderWriterM16Handle, x: number, y: number): M16;
        writePixel(self: PixelReaderWriterM16Handle, x: number, y: number, pixel: M16): void;
    }
    export const PixelReaderWriterM16Api: PixelReaderWriterM16Api;

    export interface PixelReaderWriterM8Api {
        create(bitmap: RasterObjectHandle): PixelReaderWriterM8Handle;
        dispose(self: PixelReaderWriterM8Handle): void;
        readPixel(self: PixelReaderWriterM8Handle, x: number, y: number): M8;
        writePixel(self: PixelReaderWriterM8Handle, x: number, y: number, pixel: M8): void;
    }
    export const PixelReaderWriterM8Api: PixelReaderWriterM8Api;

    export interface PixelReaderWriterMfApi {
        create(bitmap: RasterObjectHandle): PixelReaderWriterMfHandle;
        dispose(self: PixelReaderWriterMfHandle): void;
        readPixel(self: PixelReaderWriterMfHandle, x: number, y: number): Mf;
        writePixel(self: PixelReaderWriterMfHandle, x: number, y: number, pixel: Mf): void;
    }
    export const PixelReaderWriterMfApi: PixelReaderWriterMfApi;

    export interface PixelReaderWriterRGBA16Api {
        create(bitmap: RasterObjectHandle): PixelReaderWriterRGBA16Handle;
        dispose(self: PixelReaderWriterRGBA16Handle): void;
        readPixel(self: PixelReaderWriterRGBA16Handle, x: number, y: number): RGBA16;
        writePixel(self: PixelReaderWriterRGBA16Handle, x: number, y: number, pixel: RGBA16): void;
    }
    export const PixelReaderWriterRGBA16Api: PixelReaderWriterRGBA16Api;

    export interface PixelReaderWriterRGBA8Api {
        create(bitmap: RasterObjectHandle): PixelReaderWriterRGBA8Handle;
        dispose(self: PixelReaderWriterRGBA8Handle): void;
        readPixel(self: PixelReaderWriterRGBA8Handle, x: number, y: number): RGBA8;
        writePixel(self: PixelReaderWriterRGBA8Handle, x: number, y: number, pixel: RGBA8): void;
    }
    export const PixelReaderWriterRGBA8Api: PixelReaderWriterRGBA8Api;

    export interface PixelReaderWriterRGBAufApi {
        create(bitmap: RasterObjectHandle): PixelReaderWriterRGBAufHandle;
        dispose(self: PixelReaderWriterRGBAufHandle): void;
        readPixel(self: PixelReaderWriterRGBAufHandle, x: number, y: number): RGBAuf;
        writePixel(self: PixelReaderWriterRGBAufHandle, x: number, y: number, pixel: RGBAuf): void;
    }
    export const PixelReaderWriterRGBAufApi: PixelReaderWriterRGBAufApi;

    export interface RasterObjectApi {
        clone(self: RasterObjectHandle): RasterObjectHandle;
        cloneEmpty(self: RasterObjectHandle): RasterObjectHandle;
        copyTo(self: RasterObjectHandle, rasterObject: RasterObjectHandle, destinationRectangle: Rectangle, sourceX: number, sourceY: number): void;
        createBitmap(width: number, height: number, format: RasterFormat): RasterObjectHandle;
        createCompatibleBitmap(self: RasterObjectHandle, copyContents: boolean): RasterObjectHandle;
        createCompatibleBuffer(self: RasterObjectHandle, copyContents: boolean): RasterObjectHandle;
        createDefaultNodeRenderingEngine(node: NodeHandle, format: RasterFormat): RasterObjectHandle;
        createNodeRenderingEngine(node: NodeHandle, format: RasterFormat, options: NodeRenderingEngineOptionsHandle): RasterObjectHandle;
        createPixelBuffer(width: number, height: number, format: RasterFormat): RasterObjectHandle;
        dispose(self: RasterObjectHandle): void;
        getArrayBuffer(self: RasterObjectHandle): ArrayBuffer;
        getDescription(self: RasterObjectHandle): string;
        getDirectAccess(self: RasterObjectHandle): ArrayBuffer;
        getFormat(self: RasterObjectHandle): RasterFormat;
        getHeight(self: RasterObjectHandle): number;
        getPixelSize(self: RasterObjectHandle): number;
        getType(self: RasterObjectHandle): RasterObjectType;
        getWidth(self: RasterObjectHandle): number;
        loadBitmapFromFile(path: string, format: RasterFormat): RasterObjectHandle;
        loadBitmapFromFileAsync(path: string, format: RasterFormat, callback: (result: Error | null, rasterObjectRef: RasterObjectHandle | null) => void): void;
        loadBitmapFromResource(resource: ResourceHandle, format: RasterFormat): RasterObjectHandle;
        loadBitmapFromResourceAsync(resource: ResourceHandle, format: RasterFormat, callback: (result: Error | null, rasterObjectRef: RasterObjectHandle | null) => void): void;
    }
    export const RasterObjectApi: RasterObjectApi;

}
