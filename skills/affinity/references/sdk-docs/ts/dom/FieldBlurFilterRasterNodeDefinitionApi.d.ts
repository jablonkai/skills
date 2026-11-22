// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", FieldBlurFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface FieldBlurFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: FieldBlurFilterParametersHandle): FieldBlurFilterRasterNodeDefinitionHandle;
        createDefault(document: DocumentHandle): FieldBlurFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): FieldBlurFilterRasterNodeDefinitionHandle;
        getParameters(self: FieldBlurFilterRasterNodeDefinitionHandle): FieldBlurFilterParametersHandle;
        setParameters(self: FieldBlurFilterRasterNodeDefinitionHandle, parameters: FieldBlurFilterParametersHandle): void;
    }
    export const FieldBlurFilterRasterNodeDefinitionApi: FieldBlurFilterRasterNodeDefinitionApi;

}
