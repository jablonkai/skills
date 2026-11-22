// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VoronoiFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VoronoiFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: VoronoiFilterParametersHandle): VoronoiFilterRasterNodeDefinitionHandle;
        createDefault(): VoronoiFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): VoronoiFilterRasterNodeDefinitionHandle;
        getParameters(node: VoronoiFilterRasterNodeDefinitionHandle): VoronoiFilterParametersHandle;
        setParameters(node: VoronoiFilterRasterNodeDefinitionHandle, parameters: VoronoiFilterParametersHandle): void;
    }
    export const VoronoiFilterRasterNodeDefinitionApi: VoronoiFilterRasterNodeDefinitionApi;

}
