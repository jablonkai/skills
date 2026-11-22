// Type declarations for the Affinity JavaScript SDK: module "affinity:timers".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:timers" {

    export interface TimerApi {
        cancel(self: TimerHandle): void;
        cancelAll(): void;
        create(): TimerHandle;
        dispose(self: TimerHandle): void;
        getExpiry(self: TimerHandle, asBigInt: boolean): number;
        getExpiryFromNow(self: TimerHandle, asBigInt: boolean): number;
        getNow(asBigInt: boolean): number;
        moveExpiry(self: TimerHandle, durationMs: number): void;
        setExpiry(self: TimerHandle, expiryTimeMs: number): void;
        setExpiryFromNow(self: TimerHandle, durationMs: number): void;
        waitAsync(self: TimerHandle, callback: (error: Error | null) => void): void;
    }
    export const TimerApi: TimerApi;

}
