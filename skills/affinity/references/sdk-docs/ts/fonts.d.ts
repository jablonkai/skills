// Type declarations for the Affinity JavaScript SDK: module "affinity:fonts".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:fonts" {

    import { EnumerationResult } from "affinity:common";

    export enum FontField {
        PostscriptName,
        FamilyName,
        Weight,
        IsItalic,
        Width,
        Panose,
        VarParams,
        RibbiFamily,
        WwsFamily,
    }

    export enum FontMatch {
        Any,
        Family,
        Exact,
    }

    export enum FontWeight {
        Thin,
        ExtraLight,
        Light,
        Normal,
        Medium,
        SemiBold,
        Bold,
        ExtraBold,
        Black,
    }

    export enum FontWidth {
        UltraCondensed,
        ExtraCondensed,
        Condensed,
        SemiCondensed,
        Normal,
        SemiExpanded,
        Expanded,
        ExtraExpanded,
        UltraExpanded,
    }

    export enum PanoseType {
        Unknown,
        Unmatched,
        Body,
        Script,
        Decorative,
        Symbol,
    }

    export class VariableFontBold {
        regular: number;
        bold: number;
    }

    export class VariableFontItalic {
        regular: number;
        italic: number;
    }

    export interface FontApi {
        clone(self: FontHandle): FontHandle;
        cloneAsFont(self: FontHandle): FontHandle;
        create(family: string, weight: number, isItalic: boolean, width: FontWidth): FontHandle;
        createDefault(): FontHandle;
        createDefaultMonospaced(): FontHandle;
        createDefaultSymbol(): FontHandle;
        createEmpty(): FontHandle;
        enumerate(callback: (font: FontHandle) => EnumerationResult): void;
        getDistance(self: FontHandle, other: FontHandle): number;
        getFamilyName(self: FontHandle): string;
        getNormalizedWeight(self: FontHandle): number;
        getNormalizedWidth(self: FontHandle): number;
        getPanose(self: FontHandle): PanoseHandle;
        getPostscriptName(self: FontHandle): string;
        getPostscriptPrefix(self: FontHandle): string;
        getRibbiFamily(self: FontHandle): string;
        getTraitsName(self: FontHandle): string;
        getVariableBold(self: FontHandle): VariableFontBold;
        getVariableItalic(self: FontHandle): VariableFontItalic;
        getWeight(self: FontHandle): number;
        getWidth(self: FontHandle): FontWidth;
        getWwsFamily(self: FontHandle): string;
        isBold(self: FontHandle): boolean;
        isBoldAvailable(self: FontHandle): boolean;
        isCondensed(self: FontHandle): boolean;
        isExpanded(self: FontHandle): boolean;
        isItalic(self: FontHandle): boolean;
        isItalicAvailable(self: FontHandle): boolean;
        isNormal(self: FontHandle): boolean;
        isValid(self: FontHandle): boolean;
        isVariableBold(self: FontHandle): boolean;
        isVariableItalic(self: FontHandle): boolean;
        toString(self: FontHandle): string;
    }
    export const FontApi: FontApi;

    export interface FontCollectionApi {
        clone(self: FontCollectionHandle): FontCollectionHandle;
        cloneAsFontCollection(self: FontCollectionHandle): FontCollectionHandle;
        enumerateCollections(callback: (fontCollection: FontCollectionHandle) => EnumerationResult): void;
        getDefault(): FontCollectionHandle;
        getDisplayName(self: FontCollectionHandle): string;
    }
    export const FontCollectionApi: FontCollectionApi;

    export interface FontFamilyApi {
        clone(self: FontFamilyHandle): FontFamilyHandle;
        cloneAsFontFamily(self: FontFamilyHandle): FontFamilyHandle;
        enumerate(callback: (fontFamily: FontFamilyHandle) => EnumerationResult): void;
        enumerateFonts(self: FontFamilyHandle, callback: (font: FontHandle) => EnumerationResult): void;
        getFont(self: FontFamilyHandle, index: number): FontHandle;
        getFontCount(self: FontFamilyHandle): number;
        getName(self: FontFamilyHandle): string;
        hasFixed(self: FontFamilyHandle): boolean;
        hasVariations(self: FontFamilyHandle): boolean;
    }
    export const FontFamilyApi: FontFamilyApi;

    export interface PanoseApi {
        clone(self: PanoseHandle): PanoseHandle;
        cloneAsPanose(self: PanoseHandle): PanoseHandle;
        getDistance(self: PanoseHandle, other: PanoseHandle): number;
        is(self: PanoseHandle, panoseType: PanoseType): boolean;
        isEmpty(self: PanoseHandle): boolean;
        isMonospaced(self: PanoseHandle): boolean;
        isSansSerif(self: PanoseHandle): boolean;
        isSerif(self: PanoseHandle): boolean;
        toString(self: PanoseHandle): string;
    }
    export const PanoseApi: PanoseApi;

}
