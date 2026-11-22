// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", NodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Transform } from "affinity:geometry";

    export interface NodeDefinitionApi {
        getTransform(self: NodeDefinitionHandle): Transform;
        getUserDescription(self: NodeDefinitionHandle): string;
        setTransform(self: NodeDefinitionHandle, transform: Transform): void;
        setUserDescription(self: NodeDefinitionHandle, description: string): void;
    }
    export const NodeDefinitionApi: NodeDefinitionApi;

}
