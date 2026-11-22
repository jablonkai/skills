// Type declarations for the Affinity JavaScript SDK: module "affinity:colours".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:colours" {

    import { EnumerationResult } from "affinity:common";
    import { RasterFormat, RasterIntent } from "affinity:raster";

    export enum ColourSpaceType {
        Unknown,
        Grey,
        RGB,
        CMYK,
        LAB,
        RGBU,
    }

    export enum ColourType {
        RGB,
        CMYK,
        HSL,
        Grey,
        LAB,
        Named,
        Registration,
    }

    export class CMYKA8 {
        c: number;
        m: number;
        y: number;
        k: number;
        alpha: number;
    }

    export class CMYKAf {
        c: number;
        m: number;
        y: number;
        k: number;
        alpha: number;
    }

    export class ColourStop {
        colour: ColourHandle;
        position: number;
        midpoint: number;
        smoothness: number;
    }

    export class HSLAf {
        h: number;
        s: number;
        l: number;
        alpha: number;
    }

    export class IA16 {
        i: number;
        alpha: number;
    }

    export class IA8 {
        i: number;
        alpha: number;
    }

    export class LABA16 {
        l: number;
        a: number;
        b: number;
        alpha: number;
    }

    export class M16 {
        alpha: number;
    }

    export class M8 {
        alpha: number;
    }

    export class Mf {
        alpha: number;
    }

    export class RGBA16 {
        r: number;
        g: number;
        b: number;
        alpha: number;
    }

    export class RGBA8 {
        r: number;
        g: number;
        b: number;
        alpha: number;
    }

    export class RGBAuf {
        r: number;
        g: number;
        b: number;
        alpha: number;
    }

    export interface ColourApi {
        clone(self: ColourHandle): ColourHandle;
        convertProfile(self: ColourHandle, fromProfile: ColourProfileHandle, toProfile: ColourProfileHandle, intent: RasterIntent, isBlackPointCompensation: boolean): void;
        createCMYKA8(cMYKA8: CMYKA8): ColourHandle;
        createCMYKAf(cMYKAf: CMYKAf): ColourHandle;
        createDefault(): ColourHandle;
        createHSLAf(hSLAf: HSLAf): ColourHandle;
        createIA16(iA16: IA16): ColourHandle;
        createIA8(iA8: IA8): ColourHandle;
        createLABA16(lABA16: LABA16): ColourHandle;
        createRGBA16(rGBA16: RGBA16): ColourHandle;
        createRGBA8(rGB8: RGBA8): ColourHandle;
        createRGBAuf(rGBAuf: RGBAuf): ColourHandle;
        getAlpha(self: ColourHandle): number;
        getCMYKA8(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): CMYKA8;
        getCMYKAf(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): CMYKAf;
        getColourSpace(self: ColourHandle): ColourSpaceType;
        getHSLAf(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): HSLAf;
        getIA16(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): IA16;
        getIA8(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): IA8;
        getIntensity(self: ColourHandle): number;
        getLABA16(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): LABA16;
        getNoise(self: ColourHandle): number;
        getOverprint(self: ColourHandle): boolean;
        getRGBA16(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): RGBA16;
        getRGBA8(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): RGBA8;
        getRGBAuf(self: ColourHandle, applyTint: boolean, profilesOrNull: ColourProfileSetHandle | null): RGBAuf;
        getTint(self: ColourHandle): number;
        getType(self: ColourHandle): ColourType;
        setAlpha(self: ColourHandle, alpha: number): void;
        setIntensity(self: ColourHandle, intensity: number): void;
        setNoise(self: ColourHandle, noise: number): void;
        setOverprint(self: ColourHandle, overprint: boolean): void;
        setTint(self: ColourHandle, tint: number): void;
    }
    export const ColourApi: ColourApi;

    export interface ColourProfileApi {
        canApplyTo(self: ColourProfileHandle, format: RasterFormat): boolean;
        enumerateProfiles(callback: (colourProfile: ColourProfileHandle) => EnumerationResult): void;
        enumerateProfilesForColourSpace(colourSpaceType: ColourSpaceType, callback: (colourProfile: ColourProfileHandle) => EnumerationResult): void;
        enumerateProfilesForFormat(format: RasterFormat, callback: (colourProfile: ColourProfileHandle) => EnumerationResult): void;
        find(name: string): ColourProfileHandle;
        getApproximateGamma(self: ColourProfileHandle): number;
        getColourSpace(self: ColourProfileHandle): ColourSpaceType;
        getDefaultForColourSpace(colourSpaceType: ColourSpaceType): ColourProfileHandle;
        getDefaultForFormat(format: RasterFormat): ColourProfileHandle;
        getDeviceClass(self: ColourProfileHandle): number;
        getName(self: ColourProfileHandle): string;
        getProfile(index: number): ColourProfileHandle;
        getProfileCount(): number;
        getVersion(self: ColourProfileHandle): number;
        isLinear(self: ColourProfileHandle): boolean;
        isStandard(self: ColourProfileHandle): boolean;
    }
    export const ColourProfileApi: ColourProfileApi;

    export interface ColourProfileSetApi {
        createDefault(): ColourProfileSetHandle;
        getBlackPointCompensation(self: ColourProfileSetHandle): boolean;
        getIntent(self: ColourProfileSetHandle): RasterIntent;
        getProfileForColourSpaceType(self: ColourProfileSetHandle, colourSpaceType: ColourSpaceType): ColourProfileHandle;
        getProfileForFormat(self: ColourProfileSetHandle, format: RasterFormat): ColourProfileHandle;
        setBlackPointCompensation(self: ColourProfileSetHandle, isBlackPointCompensation: boolean): void;
        setIntent(self: ColourProfileSetHandle, intent: RasterIntent): void;
        setProfileForColourSpaceType(self: ColourProfileSetHandle, colourSpaceType: ColourSpaceType, colourProfile: ColourProfileHandle): void;
        setProfileForFormat(self: ColourProfileSetHandle, format: RasterFormat, colourProfile: ColourProfileHandle): void;
    }
    export const ColourProfileSetApi: ColourProfileSetApi;

    export interface GradientApi {
        clone(self: GradientHandle): GradientHandle;
        create(stops: ColourStop[]): GradientHandle;
        createDefault(): GradientHandle;
        getAlpha(self: GradientHandle): number;
        getIntensity(self: GradientHandle): number;
        getNoise(self: GradientHandle): number;
        getStop(self: GradientHandle, index: number): ColourStop;
        getStopCount(self: GradientHandle): number;
        getTint(self: GradientHandle): number;
        hasNoise(self: GradientHandle): boolean;
        hasNonFullAlpha(self: GradientHandle): boolean;
        hasNonLinearMapping(self: GradientHandle): boolean;
        setAlpha(self: GradientHandle, alpha: number): void;
        setIntensity(self: GradientHandle, intensity: number): void;
        setNoise(self: GradientHandle, noise: number): void;
        setTint(self: GradientHandle, tint: number): void;
    }
    export const GradientApi: GradientApi;

}
