// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", EmbeddedDocumentNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";
    import { Point } from "affinity:geometry";

    export interface EmbeddedDocumentNodeApi extends Omit<PhysicalNodeApi, "fromNode"> {
        canEditEmbeddedImage(self: EmbeddedDocumentNodeHandle): boolean;
        canMakeLinked(self: EmbeddedDocumentNodeHandle): boolean;
        canSetPDFPassthrough(self: EmbeddedDocumentNodeHandle): boolean;
        embeddedDocumentHasArtboards(self: EmbeddedDocumentNodeHandle): boolean;
        embeddedDocumentHasLayers(self: EmbeddedDocumentNodeHandle): boolean;
        embeddedDocumentHasPageBoundingBoxes(self: EmbeddedDocumentNodeHandle): boolean;
        embeddedDocumentHasSpreads(self: EmbeddedDocumentNodeHandle): boolean;
        enumerateArtboards(self: EmbeddedDocumentNodeHandle, callback: (artboardDescription: string, artboardID: string) => EnumerationResult): void;
        enumerateLayerVisibilities(self: EmbeddedDocumentNodeHandle, callback: (layerName: string, isVisible: boolean) => EnumerationResult): void;
        enumeratePageBoundingBoxes(self: EmbeddedDocumentNodeHandle, callback: (pageBoundingBox: PageBoundingBoxType, pageBoundingBoxID: string) => EnumerationResult): void;
        enumerateSpreads(self: EmbeddedDocumentNodeHandle, includeMasters: boolean, callback: (spreadDescription: string, spreadID: string) => EnumerationResult): void;
        fromNode(node: NodeHandle): EmbeddedDocumentNodeHandle;
        getImageResourceInterface(self: EmbeddedDocumentNodeHandle): ImageResourceInterfaceHandle;
        getLoadDocumentOptions(self: EmbeddedDocumentNodeHandle): LoadDocumentOptionsHandle;
        getOriginalHostDPI(self: EmbeddedDocumentNodeHandle): number;
        getPDFPassthrough(self: EmbeddedDocumentNodeHandle): boolean;
        getPageBoundingBoxType(self: EmbeddedDocumentNodeHandle): PageBoundingBoxType;
        getRasterDPI(self: EmbeddedDocumentNodeHandle): number;
        getSelectedArtboardId(self: EmbeddedDocumentNodeHandle): string;
        getSelectedArtboardOffset(self: EmbeddedDocumentNodeHandle): Point;
        getSelectedSpreadId(self: EmbeddedDocumentNodeHandle): string;
        getTransparencyInterface(self: EmbeddedDocumentNodeHandle): TransparencyInterfaceHandle;
        isAffinityFile(self: EmbeddedDocumentNodeHandle): boolean;
        isArtboardDoc(self: EmbeddedDocumentNodeHandle): boolean;
        isArtboardSelected(self: EmbeddedDocumentNodeHandle): boolean;
        needsPassword(self: EmbeddedDocumentNodeHandle): boolean;
        shouldAllowSelectDocument(self: EmbeddedDocumentNodeHandle): boolean;
    }
    export const EmbeddedDocumentNodeApi: EmbeddedDocumentNodeApi;

}
