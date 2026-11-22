// Type declarations for the Affinity JavaScript SDK: module "affinity:buffer".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:buffer" {

    export interface BufferApi {
        clone(self: BufferHandle): BufferHandle;
        cloneAsBuffer(self: BufferHandle): BufferHandle;
        compare(self: BufferHandle, other: BufferHandle): number;
        compareSome(self: BufferHandle, offset: number, length: number, other: BufferHandle, otherOffset: number, otherLength: number): number;
        create(size: number): BufferHandle;
        createSlice(self: BufferHandle, offset: number, length: number): BufferHandle;
        createSpan(self: BufferHandle, offset: number, length: number): BufferHandle;
        equals(self: BufferHandle, other: BufferHandle): boolean;
        getArrayBuffer(self: BufferHandle): ArrayBuffer;
        getSize(self: BufferHandle): number;
        toString(buffer: BufferHandle | ArrayBuffer | SharedArrayBuffer | ArrayBufferView, encoding: string, start: number, end: number): string;
    }
    export const BufferApi: BufferApi;

}
