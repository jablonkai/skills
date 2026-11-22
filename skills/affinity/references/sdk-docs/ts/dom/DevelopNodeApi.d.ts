// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DevelopNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Size } from "affinity:geometry";

    export interface DevelopNodeApi extends Omit<PhysicalNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): DevelopNodeHandle;
        getImageResourceInterface(self: DevelopNodeHandle): ImageResourceInterfaceHandle;
        getImageSize(self: DevelopNodeHandle): Size;
        getParameters(self: DevelopNodeHandle): DevelopParametersHandle;
        getRasterInterface(self: DevelopNodeHandle): RasterInterfaceHandle;
        getSourceIsRaw(self: DevelopNodeHandle): boolean;
    }
    export const DevelopNodeApi: DevelopNodeApi;

}
