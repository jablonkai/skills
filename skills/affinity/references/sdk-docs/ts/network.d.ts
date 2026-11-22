// Type declarations for the Affinity JavaScript SDK: module "affinity:network".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:network" {

    export enum HttpStatusCode {
        Continue,
        SwitchingProtocols,
        Processing,
        EarlyHints,
        Ok,
        Created,
        Accepted,
        NonAuthoritativeInformation,
        NoContent,
        ResetContent,
        PartialContent,
        MultiStatus,
        AlreadyReported,
        IMUsed,
        MultipleChoices,
        MovedPermanently,
        Found,
        SeeOther,
        NotModified,
        UseProxy,
        SwitchProxy,
        TemporaryRedirect,
        PermanentRedirect,
        Invalid,
        Unauthorized,
        PaymentRequired,
        Forbidden,
        NotFound,
        MethodNotAllowed,
        NotAcceptable,
        ProxyAuthenticationRequired,
        RequestTimeout,
        Conflict,
        Gone,
        ContentTooLarge,
        Throttled,
        UnknownError,
        NotImplemented,
        BadGateway,
        ServiceUnavailable,
        GatewayTimeout,
        HTTPVersionNotSupported,
        VariantAlsoNegotiates,
        InsufficientStorage,
        LoopDetected,
        NotExtended,
        NetworkAuthenticationRequired,
    }

    export enum RequestMethod {
        Get,
        Post,
    }

    export class HttpRequestResult {
        response: HttpResponseHandle;
        failureReason: string;
    }

    export interface HttpRequestApi {
        create(url: string, method: RequestMethod): HttpRequestHandle;
        do(self: HttpRequestHandle): HttpRequestResult;
        doAsync(self: HttpRequestHandle, callback: (err: Error | null, result: HttpRequestResult | null) => void): void;
        getHeaderValue(self: HttpRequestHandle, headerKey: string): string;
        setAvoidChunkedTransferEncoding(self: HttpRequestHandle, isAvoidChunkedTransfer: boolean): void;
        setEncodeHeaderValuesAsRfc2047(self: HttpRequestHandle, isEncodeAsRfc: boolean): void;
        setHeaderValue(self: HttpRequestHandle, headerKey: string, headerValue: string): void;
        setSuppressUserAgentHeader(self: HttpRequestHandle, suppress: boolean): void;
        setTimeoutInSec(self: HttpRequestHandle, timeout: number): void;
        setUseConstrainedNetwork(self: HttpRequestHandle, useConstrainedNetwork: boolean): void;
        setUseExpensiveNetwork(self: HttpRequestHandle, useExpensiveNetwork: boolean): void;
    }
    export const HttpRequestApi: HttpRequestApi;

    export interface HttpResponseApi {
        getContent(self: HttpResponseHandle): string;
        getHeaderValue(self: HttpResponseHandle, headerKey: string): string;
        getIsSuccess(self: HttpResponseHandle): boolean;
        getStatusCode(self: HttpResponseHandle): HttpStatusCode;
    }
    export const HttpResponseApi: HttpResponseApi;

}
