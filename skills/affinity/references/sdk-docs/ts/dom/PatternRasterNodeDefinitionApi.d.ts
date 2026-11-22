// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PatternRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Transform } from "affinity:geometry";

    export interface PatternRasterNodeDefinitionApi extends Omit<RasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(bitmap: RasterObjectHandle, transform: Transform, mirror: boolean): PatternRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): PatternRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): PatternRasterNodeDefinitionHandle;
        getMirror(self: PatternRasterNodeDefinitionHandle): boolean;
        setMirror(self: PatternRasterNodeDefinitionHandle, mirror: boolean): void;
    }
    export const PatternRasterNodeDefinitionApi: PatternRasterNodeDefinitionApi;

}
