// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TwirlFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TwirlFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: TwirlFilterParametersHandle): TwirlFilterRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): TwirlFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): TwirlFilterRasterNodeDefinitionHandle;
        getParameters(node: TwirlFilterRasterNodeDefinitionHandle): TwirlFilterParametersHandle;
        setParameters(node: TwirlFilterRasterNodeDefinitionHandle, parameters: TwirlFilterParametersHandle): void;
    }
    export const TwirlFilterRasterNodeDefinitionApi: TwirlFilterRasterNodeDefinitionApi;

}
