// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LayerEffectsInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface LayerEffectsInterfaceApi {
        enumerateEffects(self: LayerEffectsInterfaceHandle, callback: (layerEffect: LayerEffectHandle) => EnumerationResult): void;
        fromNode(node: NodeHandle): LayerEffectsInterfaceHandle;
        getEffect(self: LayerEffectsInterfaceHandle, index: number): LayerEffectHandle;
        getEffectCount(self: LayerEffectsInterfaceHandle): number;
        getNode(self: LayerEffectsInterfaceHandle): NodeHandle;
        hasActiveEffects(self: LayerEffectsInterfaceHandle): boolean;
        hasAnyVisibleEffects(self: LayerEffectsInterfaceHandle): boolean;
        isScaleWithObject(self: LayerEffectsInterfaceHandle): boolean;
    }
    export const LayerEffectsInterfaceApi: LayerEffectsInterfaceApi;

}
