// Type declarations for the Affinity JavaScript SDK: module "affinity:common".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:common" {

    export enum BlendMode {
        Normal,
        Pigment,
        Darken,
        DarkerColour,
        Multiply,
        ColourBurn,
        LinearBurn,
        Lighten,
        LighterColour,
        Screen,
        ColourDodge,
        Add,
        Overlay,
        SoftLight,
        HardLight,
        VividLight,
        PinLight,
        LinearLight,
        HardMix,
        Difference,
        Exclusion,
        Subtract,
        Divide,
        Hue,
        Saturation,
        Luminosity,
        Colour,
        Average,
        Negation,
        Reflect,
        Glow,
        ContrastInvert,
        Erase,
    }

    export enum ConfigurationValueType {
        Object,
        Array,
        String,
        Float,
        Uint,
        Int,
        Bool,
        Null,
        Binary,
    }

    export enum EnumerationResult {
        Continue,
        Stop,
    }

    export enum ErrorCode {
        OK,
        ERROR,
        INVALID_OP,
        INVALID_HANDLE,
        DEPRECATED,
        DISPOSED,
        ABORTED,
        ALLOC_ERROR,
        CREATE_FILE_ERROR,
        FILE_ALREADY_OPEN,
        READ_ONLY,
        READ_ERROR,
        WRITE_ERROR,
        IS_LOCKED,
        IS_LOCKED_THIS_DEVICE,
        IS_LOCKED_BLOCKED,
        ASYNC_IN_PROGRESS,
        COMMAND_FAILED,
        NO_ENVIRONMENT,
        SAVE_ERROR,
        WARNINGS_ONLY,
        NOT_ALLOWED,
        CREATE_DIR_ERROR,
        EMBED_METADATA_ERROR,
        CREATE_GAIN_MAP_ERROR,
        PARSE_FILE_ERROR,
        CREATE_TEMPORARY_ARCHIVE_ERROR,
        OPEN_LINKED_ARCHIVE_ERROR,
        BAD_FILE_VERSION,
        FUTURE_FILE_VERSION,
        BAD_ARCHIVE,
        FILE_TRUNCATED,
        VALIDATION_FAILED,
        VALIDATION_FOR_EMBED_FAILED,
        MIGRATION_FAILED,
        BAD_SIGNAL_FILE,
        WRONG_PASSWORD,
        EMBED_RESTRICTED,
        COPY_FILE_ERROR,
        UNSUPPORTED_ENCRYPTION,
        NOT_DOCUMENT_ARCHIVE,
        FILE_CORRUPTED,
        UNSUPPORTED_FEATURES,
        UNSUPPORTED_VERSION,
        UNSUPPORTED_COMPRESSION,
        ARCHIVE_FILE_NOT_FOUND,
        PARSE_KNOWN_FILE_TYPE_ERROR,
        LOST_OWNERSHIP,
        OWNERSHIP_VALIDATION_ERROR,
        LOCK_LOST,
        ARCHIVE_LOST,
        ARCHIVE_LOST_DURING_STREAMLINE,
        ARCHIVE_BROKEN_DURING_STREAMLINE,
        OUT_OF_SPACE_DURING_STREAMLINE,
        ARCHIVE_LOST_DURING_MIGRATE,
        SCRATCH_LOST,
        SAVE_TO_TEMPORARY_ARCHIVE_ERROR,
        ARCHIVE_HAS_BEEN_REWOUND,
        ARCHIVE_IS_READ_ONLY,
        AUTOSAVE_REQUIRES_SCRATCH_FILE,
        ARCHIVE_INTEGRITY_VERIFICATION_ERROR,
        ARCHIVE_FILES_VERIFICATION_ERROR,
        RASTER_DATA_LOST,
        BACKING_DATA_LOST,
        BACKING_DATA_MISSING,
        DOCUMENT_IS_TEMPORARY,
        IN_EXTERNAL_UPDATE,
        INTERNAL_ERROR,
        RESTORE_FILE_NOT_FOUND,
        RESTORE_ACCESS_DENIED,
        RESTORE_PERMISSION_DENIED,
        RESTORE_READ_ONLY,
        RESTORE_OPEN_ERROR,
        RESTORE_TIMEDOUT,
        RESTORE_CONNECTION_REFUSED,
        RESTORE_MISMATCH,
        LINK_RECURSIVE,
        OPEN_IN_APP,
        OPERATION_NOT_PERMITTED,
        NO_SUCH_FILE_OR_DIRECTORY,
        NO_SUCH_PROCESS,
        INTERRUPTED_SYSTEM_CALL,
        INPUT_OUTPUT_ERROR,
        DEVICE_NOT_CONFIGURED,
        ARGUMENT_LIST_TOO_LONG,
        EXEC_FORMAT_ERROR,
        BAD_FILE_DESCRIPTOR,
        NO_CHILD_PROCESSES,
        RESOURCE_DEADLOCK_AVOIDED,
        CANNOT_ALLOCATE_MEMORY,
        PERMISSION_DENIED,
        BAD_ADDRESS,
        DEVICE_OR_RESOURCE_BUSY,
        FILE_EXISTS,
        CROSS_DEVICE_LINK,
        OPERATION_NOT_SUPPORTED_BY_DEVICE,
        NOT_A_DIRECTORY,
        IS_A_DIRECTORY,
        INVALID_ARGS,
        TOO_MANY_OPEN_FILES_IN_SYSTEM,
        TOO_MANY_OPEN_FILES,
        INAPPROPRIATE_IOCTL_FOR_DEVICE,
        TEXT_FILE_BUSY,
        FILE_TOO_LARGE,
        NO_SPACE_LEFT_ON_DEVICE,
        ILLEGAL_SEEK,
        READ_ONLY_FILE_SYSTEM,
        TOO_MANY_LINKS,
        BROKEN_PIPE,
        NUMERICAL_ARGUMENT_OUT_OF_DOMAIN,
        RESULT_TOO_LARGE,
        RESOURCE_TEMPORARILY_UNAVAILABLE,
        OPERATION_NOW_IN_PROGRESS,
        OPERATION_ALREADY_IN_PROGRESS,
        SOCKET_OPERATION_ON_NON_SOCKET,
        DESTINATION_ADDRESS_REQUIRED,
        MESSAGE_TOO_LONG,
        PROTOCOL_WRONG_TYPE_FOR_SOCKET,
        PROTOCOL_NOT_AVAILABLE,
        PROTOCOL_NOT_SUPPORTED,
        NOT_SUPPORTED,
        ADDRESS_FAMILY_NOT_SUPPORTED,
        ADDRESS_ALREADY_IN_USE,
        ADDRESS_NOT_AVAILABLE,
        NETWORK_DOWN,
        NETWORK_UNREACHABLE,
        NETWORK_RESET,
        CONNECTION_ABORTED,
        CONNECTION_RESET,
        NO_BUFFER_SPACE_AVAILABLE,
        SOCKET_ALREADY_CONNECTED,
        SOCKET_NOT_CONNECTED,
        OPERATION_TIMED_OUT,
        CONNECTION_REFUSED,
        TOO_MANY_LEVELS_OF_SYMBOLIC_LINKS,
        FILE_NAME_TOO_LONG,
        HOST_UNREACHABLE,
        DIRECTORY_NOT_EMPTY,
        NO_LOCKS_AVAILABLE,
        NOT_IMPLEMENTED,
        OVERFLOW,
        OPERATION_CANCELLED,
        IDENTIFIER_REMOVED,
        NO_MESSAGE_OF_DESIRED_TYPE,
        ILLEGAL_BYTE_SEQUENCE,
        BAD_MESSAGE,
        NO_MESSAGE_AVAILABLE_ON_STREAM,
        LINK_SEVERED,
        NO_STREAM_RESOURCES,
        NOT_A_STREAM,
        PROTOCOL_ERROR,
        STREAM_IOCTL_TIMEOUT,
        STATE_NOT_RECOVERABLE,
        OWNER_DEAD,
        BLOCK_DEVICE_REQUIRED,
        SOCKET_TYPE_NOT_SUPPORTED,
        PROTOCOL_FAMILY_NOT_SUPPORTED,
        CANNOT_SEND_AFTER_SOCKET_SHUTDOWN,
        TOO_MANY_REFERENCES,
        HOST_IS_DOWN,
        TOO_MANY_PROCESSES,
        TOO_MANY_USERS,
        DISC_QUOTA_EXCEEDED,
        STALE_NFS_FILE_HANDLE,
        TOO_MANY_LEVELS_OF_REMOTE_IN_PATH,
        RPC_STRUCT_BAD,
        RPC_VERSION_WRONG,
        RPC_PROG_NOT_AVAIL,
        PROGRAM_VERSION_WRONG,
        PROCEDURE_UNAVAILABLE,
        INAPPROPRIATE_FILE_TYPE_OR_FORMAT,
        AUTHENTICATION_ERROR,
        NEED_AUTHENTICATOR,
        DEVICE_POWER_IS_OFF,
        DEVICE_ERROR,
        BAD_EXECUTABLE,
        BAD_ARCHITECTURE,
        SHARED_LIBRARY_VERSION_MISMATCH,
        MALFORMED_MACHO_FILE,
        ATTRIBUTE_NOT_FOUND,
        MULTIHOP_ATTEMPTED,
        NO_SUCH_POLICY_REGISTERED,
        INTERFACE_OUTPUT_QUEUE_FULL,
        STRING_TRUNCATED,
    }

    export enum HorizontalAlignment {
        Left,
        Centre,
        Right,
        Fill,
    }

    export enum LogLevel {
        All,
        Trace,
        Debug,
        Info,
        Warn,
        Error,
        None,
    }

    export enum UnitCategory {
        Distance,
        Angle,
        Relative,
        Data,
        Temperature,
    }

    export enum UnitType {
        Number,
        Percentage,
        Permille,
        Degree,
        Radian,
        Pixel,
        Inch,
        Point,
        Millimetre,
        Centimetre,
        Metre,
        Foot,
        Yard,
        Cat,
        Pica,
        Kilometre,
        Mile,
        Byte,
        Kilobyte,
        Megabyte,
        Gigabyte,
        Terabyte,
        Petabyte,
        Exabyte,
        Zettabyte,
        Yottabyte,
        Kelvin,
    }

    export enum UserUnitType {
        Default,
        Text,
        Line,
    }

    export class UnitValue {
        value: number;
        units: UnitTypePower;
    }

    export interface ConfigurationItemApi {
        createFromJsonString(jsonStr: string, allowComments: boolean): ConfigurationItemHandle;
        enumerateItems(self: ConfigurationItemHandle, callback: (value: ConfigurationItemHandle) => EnumerationResult): void;
        enumerateProperties(self: ConfigurationItemHandle, callback: (name: string, value: ConfigurationItemHandle) => EnumerationResult): void;
        enumeratePropertyNames(self: ConfigurationItemHandle, callback: (name: string) => EnumerationResult): void;
        getArrayItem(self: ConfigurationItemHandle, index: number): ConfigurationItemHandle;
        getArrayLength(self: ConfigurationItemHandle): number;
        getBool(self: ConfigurationItemHandle): boolean;
        getBoolOrDefault(self: ConfigurationItemHandle, defaultValue: boolean): boolean;
        getFloat(self: ConfigurationItemHandle): number;
        getFloatOrDefault(self: ConfigurationItemHandle, defaultValue: number): number;
        getInt(self: ConfigurationItemHandle): number;
        getIntOrDefault(self: ConfigurationItemHandle, defaultValue: number): number;
        getProperty(self: ConfigurationItemHandle, propertyName: string): ConfigurationItemHandle;
        getPropertyBool(self: ConfigurationItemHandle, propertyName: string): boolean;
        getPropertyBoolOrDefault(self: ConfigurationItemHandle, propertyName: string, defaultValue: boolean): boolean;
        getPropertyCount(self: ConfigurationItemHandle): number;
        getPropertyFloat(self: ConfigurationItemHandle, propertyName: string): number;
        getPropertyFloatOrDefault(self: ConfigurationItemHandle, propertyName: string, defaultValue: number): number;
        getPropertyInt(self: ConfigurationItemHandle, propertyName: string): number;
        getPropertyIntOrDefault(self: ConfigurationItemHandle, propertyName: string, defaultValue: number): number;
        getPropertyString(self: ConfigurationItemHandle, propertyName: string): string;
        getPropertyStringOrDefault(self: ConfigurationItemHandle, propertyName: string, defaultValue: string): string;
        getPropertyUint(self: ConfigurationItemHandle, propertyName: string): number;
        getPropertyUintOrDefault(self: ConfigurationItemHandle, propertyName: string, defaultValue: number): number;
        getString(self: ConfigurationItemHandle): string;
        getStringOrDefault(self: ConfigurationItemHandle, defaultValue: string): string;
        getUint(self: ConfigurationItemHandle): number;
        getUintOrDefault(self: ConfigurationItemHandle, defaultValue: number): number;
        getValueType(self: ConfigurationItemHandle): ConfigurationValueType;
        hasProperty(self: ConfigurationItemHandle, propertyName: string): boolean;
        isArray(self: ConfigurationItemHandle): boolean;
        isBinary(self: ConfigurationItemHandle): boolean;
        isBool(self: ConfigurationItemHandle): boolean;
        isFloat(self: ConfigurationItemHandle): boolean;
        isInt(self: ConfigurationItemHandle): boolean;
        isNull(self: ConfigurationItemHandle): boolean;
        isNumber(self: ConfigurationItemHandle): boolean;
        isObject(self: ConfigurationItemHandle): boolean;
        isPrimitive(self: ConfigurationItemHandle): boolean;
        isString(self: ConfigurationItemHandle): boolean;
        isStructured(self: ConfigurationItemHandle): boolean;
        isUint(self: ConfigurationItemHandle): boolean;
    }
    export const ConfigurationItemApi: ConfigurationItemApi;

    export interface LocaleApi {
        enumerateUserPreferredLanguageIDs(callback: (languageID: string) => EnumerationResult): void;
        getCurrent(): LocaleHandle;
        getID(self: LocaleHandle): string;
        getISOCode(self: LocaleHandle): string;
    }
    export const LocaleApi: LocaleApi;

    export interface LogFileApi {
        create(path: string, logLevel: LogLevel, append: boolean): LogFileHandle;
        flush(self: LogFileHandle): void;
        getLogLevel(self: LogFileHandle): LogLevel;
        setLogLevel(self: LogFileHandle, logLevel: LogLevel): void;
        start(self: LogFileHandle): void;
        stop(self: LogFileHandle): void;
    }
    export const LogFileApi: LogFileApi;

    export interface RefControlApi {
        cancel(self: RefControlHandle): void;
        create(): RefControlHandle;
        hasRef(self: RefControlHandle): boolean;
        isCancelled(self: RefControlHandle): boolean;
        ref(self: RefControlHandle): void;
        unref(self: RefControlHandle): void;
    }
    export const RefControlApi: RefControlApi;

    export interface UnitValueApi {
        assign(dest: UnitValue, src: UnitValue): void;
        getTypeCategory(unitType: UnitType): UnitCategory;
        getValueAsDegrees(unitValue: UnitValue): number;
        getValueAsNumber(unitValue: UnitValue): number;
        getValueAsPixels(unitValue: UnitValue, unitValueConverter: UnitValueConverterHandle): number;
        getValueAsRadians(unitValue: UnitValue): number;
        getValueAsUnitType(unitValue: UnitValue, unitValueConverter: UnitValueConverterHandle, unitType: UnitType): number;
        getValueAsUnitTypePower(unitValue: UnitValue, unitValueConverter: UnitValueConverterHandle, unitTypePower: UnitTypePower): number;
        isFinite(unitValue: UnitValue): boolean;
        makeInfinity(unitValue: UnitValue): void;
        makeZero(unitValue: UnitValue): void;
    }
    export const UnitValueApi: UnitValueApi;

    export interface UnitValueConverterApi {
        clone(self: UnitValueConverterHandle): UnitValueConverterHandle;
        create(dpi: number): UnitValueConverterHandle;
        createWithViewDpi(dpi: number, viewDpi: number): UnitValueConverterHandle;
        equals(self: UnitValueConverterHandle, other: UnitValueConverterHandle): boolean;
        getConversionFactor(self: UnitValueConverterHandle, from: UnitType, to: UnitType): number;
        getDpi(self: UnitValueConverterHandle): number;
        getViewDpi(self: UnitValueConverterHandle): number;
    }
    export const UnitValueConverterApi: UnitValueConverterApi;

}
