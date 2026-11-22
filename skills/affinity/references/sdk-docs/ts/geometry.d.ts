// Type declarations for the Affinity JavaScript SDK: module "affinity:geometry".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:geometry" {

    import { EnumerationResult } from "affinity:common";

    export enum CurveCornerType {
        None,
        Round,
        Inverse,
        Straight,
        CutOut,
    }

    export enum CurveNodeStyle {
        None,
        Cusp,
        Smooth,
        Smart,
    }

    export enum CurveNodeType {
        OnCurve,
        Cubic1,
        Cubic2,
    }

    export enum MeshDirection {
        Left,
        Right,
        Up,
        Down,
    }

    export enum QRPayloadType {
        Text,
        URL,
        Phone,
        SMS,
        Email,
        WhatsApp,
        FaceTime,
        Location,
        Wifi,
        VEvent,
        VCard,
        DataMerge,
    }

    export enum ShapeArrowEndStyle {
        None,
        Arrow,
        TailTriangular,
        TailSquare,
        Circle,
        HalfCircleInner,
        HalfCircleOuter,
        Diamond,
        Box,
        Barb,
        Chevron,
    }

    export enum ShapeBoolParam {
        Arrow_LeftIsProportional,
        Arrow_RightIsProportional,
        CalloutEllipse_AbsoluteSizes,
        CalloutRectangle_SingleRadius,
        CalloutRectangle_AbsoluteSizes,
        Polygon_SmoothPoints,
        Rectangle_SingleRadius,
        Tear_FixedBallSize,
    }

    export enum ShapeCornerIndex {
        TopLeft,
        TopRight,
        BottomRight,
        BottomLeft,
    }

    export enum ShapeCornerType {
        Round,
        Straight,
        RoundInverse,
        Cutout,
        None,
    }

    export enum ShapeEnumParam {
        Rectangle_BottomLeftCornerType,
        Rectangle_BottomRightCornerType,
        Rectangle_TopLeftCornerType,
        Rectangle_TopRightCornerType,
        Arrow_LeftEndStyle,
        Arrow_RightEndStyle,
    }

    export enum ShapeFloatParam {
        Arrow_LeftLength,
        Arrow_LeftInnerOffset,
        Arrow_RightLength,
        Arrow_RightInnerOffset,
        Arrow_Thickness,
        CalloutEllipse_TailAngle,
        CalloutEllipse_TailEndPosition,
        CalloutEllipse_TailHeight,
        CalloutRectangle_BottomLeftRadius,
        CalloutRectangle_BottomRightRadius,
        CalloutRectangle_TopLeftRadius,
        CalloutRectangle_TopRightRadius,
        CalloutRectangle_TailEndPosition,
        CalloutRectangle_TailHeight,
        CalloutRectangle_TailPosition,
        CalloutRectangle_TailWidth,
        Cloud_InnerRadius,
        Cog_Curve,
        Cog_HoleRadius,
        Cog_InnerRadius,
        Cog_NotchSize,
        Cog_ToothSize,
        Crescent_ArcLeft,
        Crescent_ArcRight,
        Diamond_Position,
        DoubleStar_InnerRadius,
        DoubleStar_PointRadius,
        Heart_Spread,
        Pie_InnerRadius,
        Pie_StartAngle,
        Pie_EndAngle,
        Pie_Sweep,
        Polygon_Curve,
        Rectangle_BottomLeftRadius,
        Rectangle_BottomRightRadius,
        Rectangle_TopLeftRadius,
        Rectangle_TopRightRadius,
        Segment_Angle,
        Segment_LowerLine,
        Segment_UpperLine,
        SquareStar_Cutout,
        Star_CircleOuterRadius,
        Star_CircleInnerRadius,
        Star_InnerRadius,
        Star_LeftCurve,
        Star_RightCurve,
        Trapezoid_LeftPosition,
        Trapezoid_RightPosition,
        Triangle_Position,
        Tear_BallSize,
        Tear_Curve,
        Tear_Bend,
        Tear_TailPosition,
    }

    export enum ShapeIntParam {
        Cloud_BubbleCount,
        Cog_ToothCount,
        DoubleStar_PointCount,
        Polygon_SideCount,
        SquareStar_SideCount,
        Star_PointCount,
    }

    export enum ShapeMajorAxis {
        Y,
        X,
    }

    export enum ShapeSpiralStyle {
        SemiCircle,
        CounterSemiCircle,
        Fibonacci,
        SegmentedLogarithmic,
        SegmentedLinear,
        Plotted,
    }

    export enum ShapeType {
        Rectangle,
        Ellipse,
        Triangle,
        Diamond,
        Trapezoid,
        Polygon,
        Star,
        DoubleStar,
        Arrow,
        Pie,
        Cog,
        Cloud,
        CalloutRectangle,
        CalloutEllipse,
        Crescent,
        Segment,
        SquareStar,
        Tear,
        Heart,
        Cat,
        Cat2,
        Cat3,
        Cat4,
        QRCode,
        Spiral,
        Style,
    }

    export enum SplineProfile {
        Linear,
        SCurve,
        SmoothIn,
        SmoothOut,
        Squared,
        SquareRoot,
    }

    export enum WifiEncryptionType {
        None,
        WEP,
        WPA_WPA2,
    }

    export enum WindingOrder {
        OddEven,
        NonZero,
    }

    export class BoundingBox {
        bounds: Rectangle;
        isSet: boolean;
    }

    export class CubicBezier {
        #private;
        start: Point;
        c1: Point;
        c2: Point;
        end: Point;
    }

    export class CubicBezierPair {
        left: CubicBezier;
        right: CubicBezier;
    }

    export class CurveCornerData {
        type: CurveCornerType;
        radius: number;
    }

    export class CurveNode {
        position: Point;
        type: CurveNodeType;
        style: CurveNodeStyle;
        assign(source: CurveNode): void;
    }

    export class CurvePair {
        curveA: CurveHandle;
        curveB: CurveHandle;
    }

    export class Endpoints {
        start: Point;
        end: Point;
    }

    export class MeshSize {
        xSize: number;
        ySize: number;
    }

    export class Point {
        x: number;
        y: number;
    }

    export class PointMinMax {
        minPoint: Point;
        maxPoint: Point;
    }

    export class Rectangle {
        x: number;
        y: number;
        width: number;
        height: number;
        clone(): Rectangle;
    }

    export class ShapeTrapezoidPositions {
        left: number;
        right: number;
    }

    export class Size {
        width: number;
        height: number;
        clone(): Size;
    }

    export class SplineFindPointResult {
        index: number;
        isValid: boolean;
    }

    export class Transform {
        #private;
        data: number[];
    }

    export class TransformData {
        scaleX: number;
        scaleY: number;
        shear: number;
        rotation: number;
        translateX: number;
        translateY: number;
    }

    export class Vector {
        x: number;
        y: number;
    }

    export interface CubicBezierApi {
        assign(self: CubicBezier, other: CubicBezier): void;
        evaluate(self: CubicBezier, t: number): Point;
        getAcceleration(self: CubicBezier, t: number): Vector;
        getBoundingBox(self: CubicBezier): Rectangle;
        getClosestPoint(self: CubicBezier, pt: Point): Point;
        getControlBox(self: CubicBezier): Rectangle;
        getCurvature(self: CubicBezier, t: number): number;
        getLength(self: CubicBezier): number;
        getNormal(self: CubicBezier, t: number): Vector;
        getParamAtLength(self: CubicBezier, length: number): number;
        getTangent(self: CubicBezier, t: number): Vector;
        getVelocity(self: CubicBezier, t: number): Vector;
        makeLine(self: CubicBezier, start: Point, end: Point): void;
        reverse(self: CubicBezier): void;
        split(self: CubicBezier, t: number): CubicBezierPair;
        splitLeft(self: CubicBezier, t: number): CubicBezier;
        splitRight(self: CubicBezier, t: number): CubicBezier;
        transform(self: CubicBezier, transform: Transform): void;
    }
    export const CubicBezierApi: CubicBezierApi;

    export interface CurveApi {
        appendNode(self: CurveHandle, curveNode: CurveNode, cornerDataOrNull: CurveCornerData | null): void;
        clear(self: CurveHandle): void;
        clone(self: CurveHandle): CurveHandle;
        create(): CurveHandle;
        createDiamond(rectangle: Rectangle): CurveHandle;
        createEllipse(rectangle: Rectangle): CurveHandle;
        createLine(point1: Point, point2: Point): CurveHandle;
        createLozenge(point0: Point, point1: Point, radius: number): CurveHandle;
        createPrecisionEllipse(rectangle: Rectangle): CurveHandle;
        createPrecisionUnitCircle(): CurveHandle;
        createRectangle(rectangle: Rectangle): CurveHandle;
        cut(self: CurveHandle, isParametric: boolean, distance: number): CurvePair;
        enumerateNodes(self: CurveHandle, callback: (node: CurveNode, corner: CurveCornerData) => EnumerationResult): void;
        generatePolygon(self: CurveHandle, tolerance: number): PolygonHandle;
        getApproxBoundingBox(self: CurveHandle, transformOrNull: Transform | null): BoundingBox;
        getCorner(self: CurveHandle, pointIndex: number): CurveCornerData;
        getCubicBezier(self: CurveHandle, pointIndex: number): CubicBezier;
        getExactBoundingBox(self: CurveHandle, transformOrNull: Transform | null): BoundingBox;
        getFirstOnCurvePointIndex(self: CurveHandle): number;
        getLastOnCurvePointIndex(self: CurveHandle): number;
        getLength(self: CurveHandle): number;
        getNextOnCurvePointIndex(self: CurveHandle, pointIndex: number, allowWrapIfClosed: boolean): number;
        getNode(self: CurveHandle, index: number): CurveNode;
        getNodeCount(self: CurveHandle): number;
        getPath(self: CurveHandle): Point[];
        getPoint(self: CurveHandle, index: number): Point;
        getPointCount(self: CurveHandle): number;
        getPreviousOnCurvePointIndex(self: CurveHandle, pointIndex: number, allowWrapIfClosed: boolean): number;
        getSubPath(self: CurveHandle, start: number, count: number): Point[];
        isClockwise(self: CurveHandle): boolean;
        isClosed(self: CurveHandle): boolean;
        isEllipse(self: CurveHandle): boolean;
        isEllipseTolerance(self: CurveHandle, tolerance: number): boolean;
        isEmpty(self: CurveHandle): boolean;
        isPolyline(self: CurveHandle): boolean;
        isPolylineTolerance(self: CurveHandle, tolerance: number): boolean;
        isRectangle(self: CurveHandle): boolean;
        isRectangleTolerance(self: CurveHandle, tolerance: number): boolean;
        isStraightLine(self: CurveHandle): boolean;
        isStraightLineTolerance(self: CurveHandle, tolerance: number): boolean;
        makeClosed(self: CurveHandle): void;
        reverse(self: CurveHandle): void;
        setCorner(self: CurveHandle, pointIndex: number, curveCornerData: CurveCornerData, forceCorner: boolean): void;
        setPath(self: CurveHandle, points: Point[]): void;
        setPoint(self: CurveHandle, index: number, point: Point): void;
        transform(self: CurveHandle, transform: Transform): void;
    }
    export const CurveApi: CurveApi;

    export interface CurveBuilderApi {
        addArc(self: CurveBuilderHandle, startAngle: number, endAngle: number, radius: number, reverse: boolean): void;
        addBezier(self: CurveBuilderHandle, c0: Point, c1: Point, end: Point): void;
        addEllipse(self: CurveBuilderHandle, startAngle: number, endAngle: number, majorRadius: number, minorRadius: number, rotation: number, reverse: boolean): void;
        begin(self: CurveBuilderHandle, point: Point): void;
        bulgeRelative(self: CurveBuilderHandle, vector: Vector, bulge: number): void;
        bulgeTo(self: CurveBuilderHandle, point: Point, bulge: number): void;
        clone(self: CurveBuilderHandle): CurveBuilderHandle;
        close(self: CurveBuilderHandle): void;
        create(): CurveBuilderHandle;
        createCurve(self: CurveBuilderHandle): CurveHandle;
        lineRelative(self: CurveBuilderHandle, vector: Vector): void;
        lineTo(self: CurveBuilderHandle, point: Point): void;
        setCorner(self: CurveBuilderHandle, pointIndex: number, curveCornerData: CurveCornerData, forceCorner: boolean): void;
        transform(self: CurveBuilderHandle, transform: Transform): void;
        versineRelative(self: CurveBuilderHandle, vector: Vector, versine: number): void;
        versineTo(self: CurveBuilderHandle, point: Point, versine: number): void;
    }
    export const CurveBuilderApi: CurveBuilderApi;

    export interface MeshApi {
        clone(self: MeshHandle): MeshHandle;
        cloneAsMesh(self: MeshHandle): MeshHandle;
        deleteSpline(self: MeshHandle, isVertical: boolean, index: number): void;
        getCurveNodePosition(self: MeshHandle, xIndex: number, yIndex: number, direction: MeshDirection): Point;
        getNodePosition(self: MeshHandle, xIndex: number, yIndex: number): Point;
        getNodeStyle(self: MeshHandle, xIndex: number, yIndex: number): CurveNodeStyle;
        getSize(self: MeshHandle): MeshSize;
        insertSpline(self: MeshHandle, isVertical: boolean, index: number, param: number): void;
        setCurveNodePosition(self: MeshHandle, xIndex: number, yIndex: number, direction: MeshDirection, position: Point): void;
        setNodePosition(self: MeshHandle, xIndex: number, yIndex: number, position: Point): void;
        setNodeStyle(self: MeshHandle, xIndex: number, yIndex: number, style: CurveNodeStyle): void;
    }
    export const MeshApi: MeshApi;

    export interface PointApi {
        absEq(self: Point): void;
        assign(self: Point, other: Point): void;
        distance(point: Point, other: Point): number;
        distanceSquared(point: Point, other: Point): number;
        getAbs(point: Point): Point;
        getNeg(point: Point): Point;
        interpolate(point: Point, other: Point, t: number): Point;
        makeZero(self: Point): void;
        negEq(self: Point): void;
        scale(point: Point, s: number): Point;
        transform(point: Point, transform: Transform): Point;
        translate(point: Point, translation: Vector): Point;
        vectorTo(startPoint: Point, endPoint: Point): Vector;
    }
    export const PointApi: PointApi;

    export interface PolyCurveApi {
        addCurve(self: PolyCurveHandle, curve: CurveHandle, moveContents: boolean): void;
        clear(self: PolyCurveHandle): void;
        clone(self: PolyCurveHandle): PolyCurveHandle;
        create(): PolyCurveHandle;
        getApproxBoundingBox(self: PolyCurveHandle, transformOrNull: Transform | null): BoundingBox;
        getControlBoundingBox(self: PolyCurveHandle, transformOrNull: Transform | null): BoundingBox;
        getCurve(self: PolyCurveHandle, index: number, clone: boolean): CurveHandle;
        getCurveCount(self: PolyCurveHandle): number;
        getExactBoundingBox(self: PolyCurveHandle, transformOrNull: Transform | null): BoundingBox;
        removeEmptyCurves(self: PolyCurveHandle): void;
        transform(self: PolyCurveHandle, transform: Transform): void;
    }
    export const PolyCurveApi: PolyCurveApi;

    export interface PolyPolyCurveApi {
        addPolyCurve(self: PolyPolyCurveHandle, polyCurve: PolyCurveHandle, transformOrNull: Transform | null): void;
        addPolyPolyCurve(self: PolyPolyCurveHandle, polyPolyCurve: PolyPolyCurveHandle, transformOrNull: Transform | null): void;
        addRectangle(self: PolyPolyCurveHandle, rectangle: Rectangle, transformOrNull: Transform | null): void;
        clone(self: PolyPolyCurveHandle): PolyPolyCurveHandle;
        containsPoint(self: PolyPolyCurveHandle, point: Point, allowUnclosed: boolean, windingOrder: WindingOrder, performBoundsCheck: boolean): boolean;
        getApproxBoundingBox(self: PolyPolyCurveHandle, transformOrNull: Transform | null): BoundingBox;
        getExactBoundingBox(self: PolyPolyCurveHandle, transformOrNull: Transform | null): BoundingBox;
        getPolyCurve(self: PolyPolyCurveHandle, index: number): PolyCurveHandle;
        getPolyCurveCount(self: PolyPolyCurveHandle): number;
        getPolyCurveTransform(self: PolyPolyCurveHandle, index: number): Transform;
        getTransformedPolyCurve(self: PolyPolyCurveHandle, index: number): PolyCurveHandle;
        hasCorners(self: PolyPolyCurveHandle): boolean;
        hasCurves(self: PolyPolyCurveHandle): boolean;
        hasJoins(self: PolyPolyCurveHandle): boolean;
        intersectsRectangle(self: PolyPolyCurveHandle, transform: Transform, rectangle: Rectangle, closeCurves: boolean): boolean;
        isNearPoint(self: PolyPolyCurveHandle, point: Point, xTolerance: number, yTolerance: number, tolerance: number): boolean;
        isNearRectangle(self: PolyPolyCurveHandle, rectangle: Rectangle, tolerance: number): boolean;
        transform(self: PolyPolyCurveHandle, transformOrNull: Transform | null): void;
    }
    export const PolyPolyCurveApi: PolyPolyCurveApi;

    export interface PolygonApi {
        addPoint(self: PolygonHandle, point: Point): void;
        clear(self: PolygonHandle): void;
        clone(self: PolygonHandle): PolygonHandle;
        close(self: PolygonHandle): void;
        create(): PolygonHandle;
        createLine(point1: Point, point2: Point): PolygonHandle;
        createRectangle(rectangle: Rectangle): PolygonHandle;
        createTriangle(point1: Point, point2: Point, point3: Point): PolygonHandle;
        enumeratePoints(self: PolygonHandle, callback: (point: Point) => EnumerationResult): void;
        getBoundingBox(self: PolygonHandle, transformOrNull: Transform | null): BoundingBox;
        getPoint(self: PolygonHandle, index: number): Point;
        getPointCount(self: PolygonHandle): number;
        insertPoint(self: PolygonHandle, index: number, point: Point): void;
        isClockwise(self: PolygonHandle): boolean;
        isClosed(self: PolygonHandle): boolean;
        isEmpty(self: PolygonHandle): boolean;
        isRectangle(self: PolygonHandle): boolean;
        reverse(self: PolygonHandle): void;
    }
    export const PolygonApi: PolygonApi;

    export interface QRPayloadApi {
        clearPayload(self: QRPayloadHandle): void;
        clone(self: QRPayloadHandle): QRPayloadHandle;
        cloneAsQRPayload(self: QRPayloadHandle): QRPayloadHandle;
        create(type: QRPayloadType): QRPayloadHandle;
        getPayloadDisplayString(self: QRPayloadHandle): string;
        getPayloadString(self: QRPayloadHandle): string;
        getPayloadType(self: QRPayloadHandle): QRPayloadType;
        isPayloadValid(self: QRPayloadHandle): boolean;
        parse(text: string): QRPayloadHandle;
    }
    export const QRPayloadApi: QRPayloadApi;

    export interface QRPayloadDataMergeApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadDataMergeHandle): QRPayloadDataMergeHandle;
        cloneAsQRPayloadDataMerge(self: QRPayloadDataMergeHandle): QRPayloadDataMergeHandle;
        create(): QRPayloadDataMergeHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadDataMergeHandle;
        getDataMergeField(self: QRPayloadDataMergeHandle): string;
        hasPreviewValue(self: QRPayloadDataMergeHandle): boolean;
        setDataMergeField(self: QRPayloadDataMergeHandle, text: string): void;
        setPreviewValue(self: QRPayloadDataMergeHandle, text: string): void;
    }
    export const QRPayloadDataMergeApi: QRPayloadDataMergeApi;

    export interface QRPayloadEmailApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadEmailHandle): QRPayloadEmailHandle;
        cloneAsQRPayloadEmail(self: QRPayloadEmailHandle): QRPayloadEmailHandle;
        create(): QRPayloadEmailHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadEmailHandle;
        getAddress(self: QRPayloadEmailHandle): string;
        getBody(self: QRPayloadEmailHandle): string;
        getSubject(self: QRPayloadEmailHandle): string;
        isAddressValid(self: QRPayloadEmailHandle): boolean;
        setAddress(self: QRPayloadEmailHandle, text: string): void;
        setBody(self: QRPayloadEmailHandle, text: string): void;
        setSubject(self: QRPayloadEmailHandle, text: string): void;
    }
    export const QRPayloadEmailApi: QRPayloadEmailApi;

    export interface QRPayloadFaceTimeApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadFaceTimeHandle): QRPayloadFaceTimeHandle;
        cloneAsQRPayloadFaceTime(self: QRPayloadFaceTimeHandle): QRPayloadFaceTimeHandle;
        create(): QRPayloadFaceTimeHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadFaceTimeHandle;
        getRecipient(self: QRPayloadFaceTimeHandle): string;
        setRecipient(self: QRPayloadFaceTimeHandle, text: string): void;
    }
    export const QRPayloadFaceTimeApi: QRPayloadFaceTimeApi;

    export interface QRPayloadLocationApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadLocationHandle): QRPayloadLocationHandle;
        cloneAsQRPayloadLocation(self: QRPayloadLocationHandle): QRPayloadLocationHandle;
        create(): QRPayloadLocationHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadLocationHandle;
        getElevation(self: QRPayloadLocationHandle): string;
        getLatitude(self: QRPayloadLocationHandle): string;
        getLongitude(self: QRPayloadLocationHandle): string;
        isElevationValid(self: QRPayloadLocationHandle): boolean;
        isLatitudeValid(self: QRPayloadLocationHandle): boolean;
        isLongitudeValid(self: QRPayloadLocationHandle): boolean;
        setElevation(self: QRPayloadLocationHandle, text: string): void;
        setLatitude(self: QRPayloadLocationHandle, text: string): void;
        setLongitude(self: QRPayloadLocationHandle, text: string): void;
    }
    export const QRPayloadLocationApi: QRPayloadLocationApi;

    export interface QRPayloadPhoneApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadPhoneHandle): QRPayloadPhoneHandle;
        cloneAsQRPayloadPhone(self: QRPayloadPhoneHandle): QRPayloadPhoneHandle;
        create(): QRPayloadPhoneHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadPhoneHandle;
        getNumber(self: QRPayloadPhoneHandle): string;
        setNumber(self: QRPayloadPhoneHandle, text: string): void;
    }
    export const QRPayloadPhoneApi: QRPayloadPhoneApi;

    export interface QRPayloadSMSApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadSMSHandle): QRPayloadSMSHandle;
        cloneAsQRPayloadSMS(self: QRPayloadSMSHandle): QRPayloadSMSHandle;
        create(): QRPayloadSMSHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadSMSHandle;
        getContent(self: QRPayloadSMSHandle): string;
        getNumber(self: QRPayloadSMSHandle): string;
        isNumberValid(self: QRPayloadSMSHandle): boolean;
        setContent(self: QRPayloadSMSHandle, content: string): void;
        setNumber(self: QRPayloadSMSHandle, number: string): void;
    }
    export const QRPayloadSMSApi: QRPayloadSMSApi;

    export interface QRPayloadTextApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadTextHandle): QRPayloadTextHandle;
        cloneAsQRPayloadText(self: QRPayloadTextHandle): QRPayloadTextHandle;
        create(): QRPayloadTextHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadTextHandle;
        getText(self: QRPayloadTextHandle): string;
        setText(self: QRPayloadTextHandle, text: string): void;
    }
    export const QRPayloadTextApi: QRPayloadTextApi;

    export interface QRPayloadURLApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadURLHandle): QRPayloadURLHandle;
        cloneAsQRPayloadURL(self: QRPayloadURLHandle): QRPayloadURLHandle;
        create(): QRPayloadURLHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadURLHandle;
        getURL(self: QRPayloadURLHandle): string;
        isURLValid(self: QRPayloadURLHandle): boolean;
        setURL(self: QRPayloadURLHandle, text: string): void;
    }
    export const QRPayloadURLApi: QRPayloadURLApi;

    export interface QRPayloadVCardApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadVCardHandle): QRPayloadVCardHandle;
        cloneAsQRPayloadVCard(self: QRPayloadVCardHandle): QRPayloadVCardHandle;
        create(): QRPayloadVCardHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadVCardHandle;
        getBirthday(self: QRPayloadVCardHandle): string;
        getCity(self: QRPayloadVCardHandle): string;
        getCompany(self: QRPayloadVCardHandle): string;
        getCountry(self: QRPayloadVCardHandle): string;
        getEmail(self: QRPayloadVCardHandle): string;
        getFirstName(self: QRPayloadVCardHandle): string;
        getJobTitle(self: QRPayloadVCardHandle): string;
        getLastName(self: QRPayloadVCardHandle): string;
        getNotes(self: QRPayloadVCardHandle): string;
        getPhone(self: QRPayloadVCardHandle): string;
        getPostalCode(self: QRPayloadVCardHandle): string;
        getPrefixes(self: QRPayloadVCardHandle): string;
        getRegion(self: QRPayloadVCardHandle): string;
        getStreetAddress(self: QRPayloadVCardHandle): string;
        getSuffixes(self: QRPayloadVCardHandle): string;
        getWebsite(self: QRPayloadVCardHandle): string;
        isEmailValid(self: QRPayloadVCardHandle): boolean;
        isFirstNameValid(self: QRPayloadVCardHandle): boolean;
        isFullNameValid(self: QRPayloadVCardHandle): boolean;
        isLastNameValid(self: QRPayloadVCardHandle): boolean;
        isWebsiteValid(self: QRPayloadVCardHandle): boolean;
        setBirthday(self: QRPayloadVCardHandle, birthday: string): void;
        setCity(self: QRPayloadVCardHandle, city: string): void;
        setCompany(self: QRPayloadVCardHandle, company: string): void;
        setCountry(self: QRPayloadVCardHandle, country: string): void;
        setEmail(self: QRPayloadVCardHandle, email: string): void;
        setFirstName(self: QRPayloadVCardHandle, firstName: string): void;
        setJobTitle(self: QRPayloadVCardHandle, jobTitle: string): void;
        setLastName(self: QRPayloadVCardHandle, lastName: string): void;
        setNotes(self: QRPayloadVCardHandle, notes: string): void;
        setPhone(self: QRPayloadVCardHandle, phone: string): void;
        setPostalCode(self: QRPayloadVCardHandle, postalCode: string): void;
        setPrefixes(self: QRPayloadVCardHandle, prefixes: string): void;
        setRegion(self: QRPayloadVCardHandle, region: string): void;
        setStreetAddress(self: QRPayloadVCardHandle, streetAddress: string): void;
        setSuffixes(self: QRPayloadVCardHandle, suffixes: string): void;
        setWebsite(self: QRPayloadVCardHandle, website: string): void;
    }
    export const QRPayloadVCardApi: QRPayloadVCardApi;

    export interface QRPayloadWhatsAppApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadWhatsAppHandle): QRPayloadWhatsAppHandle;
        cloneAsQRPayloadWhatsApp(self: QRPayloadWhatsAppHandle): QRPayloadWhatsAppHandle;
        create(): QRPayloadWhatsAppHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadWhatsAppHandle;
        getContent(self: QRPayloadWhatsAppHandle): string;
        getNumber(self: QRPayloadWhatsAppHandle): string;
        setContent(self: QRPayloadWhatsAppHandle, content: string): void;
        setNumber(self: QRPayloadWhatsAppHandle, number: string): void;
    }
    export const QRPayloadWhatsAppApi: QRPayloadWhatsAppApi;

    export interface QRPayloadWifiApi extends Omit<QRPayloadApi, "clone" | "create"> {
        clone(self: QRPayloadWifiHandle): QRPayloadWifiHandle;
        cloneAsQRPayloadWifi(self: QRPayloadWifiHandle): QRPayloadWifiHandle;
        create(): QRPayloadWifiHandle;
        fromPayload(payload: QRPayloadHandle): QRPayloadWifiHandle;
        getEncryption(self: QRPayloadWifiHandle): WifiEncryptionType;
        getHidden(self: QRPayloadWifiHandle): boolean;
        getPassword(self: QRPayloadWifiHandle): string;
        getSSID(self: QRPayloadWifiHandle): string;
        isSSIDValid(self: QRPayloadWifiHandle): boolean;
        setEncryption(self: QRPayloadWifiHandle, encryption: WifiEncryptionType): void;
        setHidden(self: QRPayloadWifiHandle, hidden: boolean): void;
        setPassword(self: QRPayloadWifiHandle, password: string): void;
        setSSID(self: QRPayloadWifiHandle, ssid: string): void;
    }
    export const QRPayloadWifiApi: QRPayloadWifiApi;

    export interface RectangleApi {
        assign(dest: Rectangle, src: Rectangle): void;
        assignMinMax(dest: Rectangle, minPt: Point, maxPt: Point): void;
        centreOn(rect: Rectangle, pt: Point): void;
        getArea(rect: Rectangle): number;
        getBottomCentre(rect: Rectangle): Point;
        getBottomLeft(rect: Rectangle): Point;
        getBottomRight(rect: Rectangle): Point;
        getCentre(rect: Rectangle): Point;
        getCentreLeft(rect: Rectangle): Point;
        getCentreRight(rect: Rectangle): Point;
        getMaxPoint(rect: Rectangle): Point;
        getMinMaxPoints(rect: Rectangle): PointMinMax;
        getMinPoint(rect: Rectangle): Point;
        getTopCentre(rect: Rectangle): Point;
        getTopLeft(rect: Rectangle): Point;
        getTopRight(rect: Rectangle): Point;
        isFinite(rect: Rectangle): boolean;
        isValid(rect: Rectangle): boolean;
        makeNormalised(rect: Rectangle): void;
        makeZero(rect: Rectangle): void;
        moveTo(rect: Rectangle, pt: Point): void;
        offset(rect: Rectangle, vector: Vector): void;
    }
    export const RectangleApi: RectangleApi;

    export interface ShapeApi {
        clone(self: ShapeHandle): ShapeHandle;
        cloneAsShape(self: ShapeHandle): ShapeHandle;
        create(type: ShapeType): ShapeHandle;
        getCurves(self: ShapeHandle, rectangle: Rectangle, transform: Transform): PolyCurveHandle;
        getDefaultMinorAxisSize(self: ShapeHandle): number;
        getDisplayName(self: ShapeHandle): string;
        getMajorAxis(self: ShapeHandle): ShapeMajorAxis;
        getRotationOrder(self: ShapeHandle): number;
        getShapeType(self: ShapeHandle): ShapeType;
        getTransformedBounds(self: ShapeHandle, rectangle: Rectangle, transform: Transform): Rectangle;
        getTypeBaseType(type: ShapeType): ShapeType;
        getTypeDisplayName(type: ShapeType): string;
        isAffectedByScale(self: ShapeHandle): boolean;
    }
    export const ShapeApi: ShapeApi;

    export interface ShapeArrowApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeArrowHandle): ShapeArrowHandle;
        cloneAsShapeArrow(self: ShapeArrowHandle): ShapeArrowHandle;
        create(): ShapeArrowHandle;
        fromShape(shape: ShapeHandle): ShapeArrowHandle;
        getLeftEndStyle(self: ShapeArrowHandle): ShapeArrowEndStyle;
        getLeftInnerOffset(self: ShapeArrowHandle): number;
        getLeftIsProportional(self: ShapeArrowHandle): boolean;
        getLeftLength(self: ShapeArrowHandle): number;
        getRightEndStyle(self: ShapeArrowHandle): ShapeArrowEndStyle;
        getRightInnerOffset(self: ShapeArrowHandle): number;
        getRightIsProportional(self: ShapeArrowHandle): boolean;
        getRightLength(self: ShapeArrowHandle): number;
        getThickness(self: ShapeArrowHandle): number;
        setLeftEndStyle(self: ShapeArrowHandle, endStyle: ShapeArrowEndStyle): void;
        setLeftInnerOffset(self: ShapeArrowHandle, innerOffset: number, width: number, height: number): void;
        setLeftIsProportional(self: ShapeArrowHandle, proportional: boolean, width: number, height: number): void;
        setLeftLength(self: ShapeArrowHandle, length: number, width: number, height: number): void;
        setRightEndStyle(self: ShapeArrowHandle, endStyle: ShapeArrowEndStyle): void;
        setRightInnerOffset(self: ShapeArrowHandle, innerOffset: number, width: number, height: number): void;
        setRightIsProportional(self: ShapeArrowHandle, proportional: boolean, width: number, height: number): void;
        setRightLength(self: ShapeArrowHandle, length: number, width: number, height: number): void;
        setThickness(self: ShapeArrowHandle, thickness: number): void;
    }
    export const ShapeArrowApi: ShapeArrowApi;

    export interface ShapeCalloutEllipseApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCalloutEllipseHandle): ShapeCalloutEllipseHandle;
        cloneAsShapeCalloutEllipse(self: ShapeCalloutEllipseHandle): ShapeCalloutEllipseHandle;
        create(): ShapeCalloutEllipseHandle;
        fromShape(shape: ShapeHandle): ShapeCalloutEllipseHandle;
        getAbsoluteSizes(self: ShapeCalloutEllipseHandle): boolean;
        getTailAngle(self: ShapeCalloutEllipseHandle): number;
        getTailEndPosition(self: ShapeCalloutEllipseHandle): number;
        getTailHeight(self: ShapeCalloutEllipseHandle): number;
        setAbsoluteSizes(self: ShapeCalloutEllipseHandle, absoluteSizes: boolean, width: number, height: number): void;
        setTailAngle(self: ShapeCalloutEllipseHandle, tailAngle: number): void;
        setTailEndPosition(self: ShapeCalloutEllipseHandle, tailEndPosition: number): void;
        setTailHeight(self: ShapeCalloutEllipseHandle, tailHeight: number): void;
    }
    export const ShapeCalloutEllipseApi: ShapeCalloutEllipseApi;

    export interface ShapeCalloutRectangleApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCalloutRectangleHandle): ShapeCalloutRectangleHandle;
        cloneAsShapeCalloutRectangle(self: ShapeCalloutRectangleHandle): ShapeCalloutRectangleHandle;
        create(): ShapeCalloutRectangleHandle;
        fromShape(shape: ShapeHandle): ShapeCalloutRectangleHandle;
        getAbsoluteSizes(self: ShapeCalloutRectangleHandle): boolean;
        getCornerRadius(self: ShapeCalloutRectangleHandle, index: ShapeCornerIndex): number;
        getTailEndPosition(self: ShapeCalloutRectangleHandle): number;
        getTailHeight(self: ShapeCalloutRectangleHandle): number;
        getTailPosition(self: ShapeCalloutRectangleHandle): number;
        getTailWidth(self: ShapeCalloutRectangleHandle): number;
        getUseSingleRadius(self: ShapeCalloutRectangleHandle): boolean;
        setAbsoluteSizes(self: ShapeCalloutRectangleHandle, absoluteSizes: boolean, width: number, height: number): void;
        setCornerRadius(self: ShapeCalloutRectangleHandle, index: ShapeCornerIndex, cornerRadius: number, width: number, height: number): void;
        setTailEndPosition(self: ShapeCalloutRectangleHandle, tailEndPosition: number): void;
        setTailHeight(self: ShapeCalloutRectangleHandle, tailHeight: number): void;
        setTailPosition(self: ShapeCalloutRectangleHandle, tailPosition: number): void;
        setTailWidth(self: ShapeCalloutRectangleHandle, tailWidth: number): void;
        setUseSingleRadius(self: ShapeCalloutRectangleHandle, useSingleRadius: boolean): void;
    }
    export const ShapeCalloutRectangleApi: ShapeCalloutRectangleApi;

    export interface ShapeCat2Api extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCat2Handle): ShapeCat2Handle;
        cloneAsShapeCat2(self: ShapeCat2Handle): ShapeCat2Handle;
        create(): ShapeCat2Handle;
        fromShape(shape: ShapeHandle): ShapeCat2Handle;
    }
    export const ShapeCat2Api: ShapeCat2Api;

    export interface ShapeCat3Api extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCat3Handle): ShapeCat3Handle;
        cloneAsShapeCat3(self: ShapeCat3Handle): ShapeCat3Handle;
        create(): ShapeCat3Handle;
        fromShape(shape: ShapeHandle): ShapeCat3Handle;
    }
    export const ShapeCat3Api: ShapeCat3Api;

    export interface ShapeCat4Api extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCat4Handle): ShapeCat4Handle;
        cloneAsShapeCat4(self: ShapeCat4Handle): ShapeCat4Handle;
        create(): ShapeCat4Handle;
        fromShape(shape: ShapeHandle): ShapeCat4Handle;
    }
    export const ShapeCat4Api: ShapeCat4Api;

    export interface ShapeCatApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCatHandle): ShapeCatHandle;
        cloneAsShapeCat(self: ShapeCatHandle): ShapeCatHandle;
        create(): ShapeCatHandle;
        fromShape(shape: ShapeHandle): ShapeCatHandle;
    }
    export const ShapeCatApi: ShapeCatApi;

    export interface ShapeCloudApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCloudHandle): ShapeCloudHandle;
        cloneAsShapeCloud(self: ShapeCloudHandle): ShapeCloudHandle;
        create(): ShapeCloudHandle;
        fromShape(shape: ShapeHandle): ShapeCloudHandle;
        getBubbleCount(self: ShapeCloudHandle): number;
        getInnerRadius(self: ShapeCloudHandle): number;
        setBubbleCount(self: ShapeCloudHandle, bubbleCount: number): void;
        setInnerRadius(self: ShapeCloudHandle, innerRadius: number): void;
    }
    export const ShapeCloudApi: ShapeCloudApi;

    export interface ShapeCogApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCogHandle): ShapeCogHandle;
        cloneAsShapeCog(self: ShapeCogHandle): ShapeCogHandle;
        create(): ShapeCogHandle;
        fromShape(shape: ShapeHandle): ShapeCogHandle;
        getCurvature(self: ShapeCogHandle): number;
        getHoleRadius(self: ShapeCogHandle): number;
        getInnerRadius(self: ShapeCogHandle): number;
        getNotchSize(self: ShapeCogHandle): number;
        getToothCount(self: ShapeCogHandle): number;
        getToothSize(self: ShapeCogHandle): number;
        setCurvature(self: ShapeCogHandle, curvature: number): void;
        setHoleRadius(self: ShapeCogHandle, holeRadius: number): void;
        setInnerRadius(self: ShapeCogHandle, innerRadius: number): void;
        setNotchSize(self: ShapeCogHandle, notchSize: number): void;
        setToothCount(self: ShapeCogHandle, toothCount: number): void;
        setToothSize(self: ShapeCogHandle, toothSize: number): void;
    }
    export const ShapeCogApi: ShapeCogApi;

    export interface ShapeCrescentApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeCrescentHandle): ShapeCrescentHandle;
        cloneAsShapeCrescent(self: ShapeCrescentHandle): ShapeCrescentHandle;
        create(): ShapeCrescentHandle;
        fromShape(shape: ShapeHandle): ShapeCrescentHandle;
        getArcLeft(self: ShapeCrescentHandle): number;
        getArcRight(self: ShapeCrescentHandle): number;
        setArcLeft(self: ShapeCrescentHandle, arcLeft: number): void;
        setArcRight(self: ShapeCrescentHandle, arcRight: number): void;
    }
    export const ShapeCrescentApi: ShapeCrescentApi;

    export interface ShapeDiamondApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeDiamondHandle): ShapeDiamondHandle;
        cloneAsShapeDiamond(self: ShapeDiamondHandle): ShapeDiamondHandle;
        create(): ShapeDiamondHandle;
        fromShape(shape: ShapeHandle): ShapeDiamondHandle;
        getPosition(self: ShapeDiamondHandle): number;
        setPosition(self: ShapeDiamondHandle, position: number): void;
    }
    export const ShapeDiamondApi: ShapeDiamondApi;

    export interface ShapeDoubleStarApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeDoubleStarHandle): ShapeDoubleStarHandle;
        cloneAsShapeDoubleStar(self: ShapeDoubleStarHandle): ShapeDoubleStarHandle;
        create(): ShapeDoubleStarHandle;
        fromShape(shape: ShapeHandle): ShapeDoubleStarHandle;
        getInnerRadius(self: ShapeDoubleStarHandle): number;
        getPointCount(self: ShapeDoubleStarHandle): number;
        getPointRadius(self: ShapeDoubleStarHandle): number;
        setInnerRadius(self: ShapeDoubleStarHandle, innerRadius: number): void;
        setPointCount(self: ShapeDoubleStarHandle, pointCount: number): void;
        setPointRadius(self: ShapeDoubleStarHandle, pointRadius: number): void;
    }
    export const ShapeDoubleStarApi: ShapeDoubleStarApi;

    export interface ShapeEllipseApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeEllipseHandle): ShapeEllipseHandle;
        cloneAsShapeEllipse(self: ShapeEllipseHandle): ShapeEllipseHandle;
        create(): ShapeEllipseHandle;
        fromShape(shape: ShapeHandle): ShapeEllipseHandle;
    }
    export const ShapeEllipseApi: ShapeEllipseApi;

    export interface ShapeHeartApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeHeartHandle): ShapeHeartHandle;
        cloneAsShapeHeart(self: ShapeHeartHandle): ShapeHeartHandle;
        create(): ShapeHeartHandle;
        fromShape(shape: ShapeHandle): ShapeHeartHandle;
        getSpread(self: ShapeHeartHandle): number;
        setSpread(self: ShapeHeartHandle, spread: number): void;
    }
    export const ShapeHeartApi: ShapeHeartApi;

    export interface ShapePieApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapePieHandle): ShapePieHandle;
        cloneAsShapePie(self: ShapePieHandle): ShapePieHandle;
        closePie(self: ShapePieHandle): void;
        create(): ShapePieHandle;
        fromShape(shape: ShapeHandle): ShapePieHandle;
        getEndAngle(self: ShapePieHandle): number;
        getInnerRadius(self: ShapePieHandle): number;
        getIsClosed(self: ShapePieHandle): boolean;
        getStartAngle(self: ShapePieHandle): number;
        getSweep(self: ShapePieHandle): number;
        setEndAngle(self: ShapePieHandle, endAngle: number): void;
        setInnerRadius(self: ShapePieHandle, innerRadius: number): void;
        setStartAngle(self: ShapePieHandle, startAngle: number): void;
        setSweep(self: ShapePieHandle, sweep: number): void;
    }
    export const ShapePieApi: ShapePieApi;

    export interface ShapePolygonApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapePolygonHandle): ShapePolygonHandle;
        cloneAsShapePolygon(self: ShapePolygonHandle): ShapePolygonHandle;
        create(): ShapePolygonHandle;
        fromShape(shape: ShapeHandle): ShapePolygonHandle;
        getCurve(self: ShapePolygonHandle): number;
        getMinCurve(self: ShapePolygonHandle): number;
        getSideCount(self: ShapePolygonHandle): number;
        getSmoothPoints(self: ShapePolygonHandle): boolean;
        setCurve(self: ShapePolygonHandle, curve: number): void;
        setSideCount(self: ShapePolygonHandle, numSides: number): void;
        setSmoothPoints(self: ShapePolygonHandle, smoothPoints: boolean): void;
    }
    export const ShapePolygonApi: ShapePolygonApi;

    export interface ShapeQRCodeApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeQRCodeHandle): ShapeQRCodeHandle;
        cloneAsShapeQRCode(self: ShapeQRCodeHandle): ShapeQRCodeHandle;
        create(): ShapeQRCodeHandle;
        fromShape(shape: ShapeHandle): ShapeQRCodeHandle;
        getPayload(self: ShapeQRCodeHandle): QRPayloadHandle;
        setPayload(self: ShapeQRCodeHandle, payload: QRPayloadHandle): void;
    }
    export const ShapeQRCodeApi: ShapeQRCodeApi;

    export interface ShapeRectangleApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeRectangleHandle): ShapeRectangleHandle;
        cloneAsShapeRectangle(self: ShapeRectangleHandle): ShapeRectangleHandle;
        create(): ShapeRectangleHandle;
        fromShape(shape: ShapeHandle): ShapeRectangleHandle;
        getAbsoluteSizes(self: ShapeRectangleHandle): boolean;
        getCornerRadius(self: ShapeRectangleHandle, corner: ShapeCornerIndex): number;
        getCornerType(self: ShapeRectangleHandle, corner: ShapeCornerIndex): ShapeCornerType;
        getUseSingleRadius(self: ShapeRectangleHandle): boolean;
        isPlainRectangle(self: ShapeRectangleHandle): boolean;
        setAbsoluteSizes(self: ShapeRectangleHandle, absoluteSizes: boolean, width: number, height: number): void;
        setCornerRadius(self: ShapeRectangleHandle, corner: ShapeCornerIndex, cornerRadius: number, width: number, height: number): void;
        setCornerType(self: ShapeRectangleHandle, corner: ShapeCornerIndex, cornerType: ShapeCornerType): void;
        setUseSingleRadius(self: ShapeRectangleHandle, singleRadius: boolean): void;
    }
    export const ShapeRectangleApi: ShapeRectangleApi;

    export interface ShapeSegmentApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeSegmentHandle): ShapeSegmentHandle;
        cloneAsShapeSegment(self: ShapeSegmentHandle): ShapeSegmentHandle;
        create(): ShapeSegmentHandle;
        fromShape(shape: ShapeHandle): ShapeSegmentHandle;
        getAngle(self: ShapeSegmentHandle): number;
        getLowerLine(self: ShapeSegmentHandle): number;
        getUpperLine(self: ShapeSegmentHandle): number;
        setAngle(self: ShapeSegmentHandle, angle: number): void;
        setLowerLine(self: ShapeSegmentHandle, lowerLine: number): void;
        setUpperLine(self: ShapeSegmentHandle, upperLine: number): void;
    }
    export const ShapeSegmentApi: ShapeSegmentApi;

    export interface ShapeSpiralApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeSpiralHandle): ShapeSpiralHandle;
        cloneAsShapeSpiral(self: ShapeSpiralHandle): ShapeSpiralHandle;
        create(): ShapeSpiralHandle;
        fromShape(shape: ShapeHandle): ShapeSpiralHandle;
        getBias(self: ShapeSpiralHandle): number;
        getCapChoke(self: ShapeSpiralHandle): boolean;
        getChoke(self: ShapeSpiralHandle): number;
        getCusped(self: ShapeSpiralHandle): boolean;
        getDecay(self: ShapeSpiralHandle): number;
        getDecayPerSegment(self: ShapeSpiralHandle): boolean;
        getDivisions(self: ShapeSpiralHandle): number;
        getFlip(self: ShapeSpiralHandle): boolean;
        getInnerRadius(self: ShapeSpiralHandle): number;
        getPartTurn(self: ShapeSpiralHandle): number;
        getSegmentAngle(self: ShapeSpiralHandle): number;
        getStyle(self: ShapeSpiralHandle): ShapeSpiralStyle;
        getTurns(self: ShapeSpiralHandle): number;
        setBias(self: ShapeSpiralHandle, bias: number): void;
        setCapChoke(self: ShapeSpiralHandle, capChoke: boolean): void;
        setChoke(self: ShapeSpiralHandle, choke: number): void;
        setCusped(self: ShapeSpiralHandle, cusped: boolean): void;
        setDecay(self: ShapeSpiralHandle, decay: number): void;
        setDecayPerSegment(self: ShapeSpiralHandle, decayPerSegment: boolean): void;
        setDivisions(self: ShapeSpiralHandle, divisions: number): void;
        setFlip(self: ShapeSpiralHandle, flip: boolean): void;
        setInnerRadius(self: ShapeSpiralHandle, innerRadius: number): void;
        setPartTurn(self: ShapeSpiralHandle, partTurn: number): void;
        setSegmentAngle(self: ShapeSpiralHandle, segmentAngle: number): void;
        setStyle(self: ShapeSpiralHandle, style: ShapeSpiralStyle): void;
        setTurns(self: ShapeSpiralHandle, turns: number): void;
    }
    export const ShapeSpiralApi: ShapeSpiralApi;

    export interface ShapeSquareStarApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeSquareStarHandle): ShapeSquareStarHandle;
        cloneAsShapeSquareStar(self: ShapeSquareStarHandle): ShapeSquareStarHandle;
        create(): ShapeSquareStarHandle;
        fromShape(shape: ShapeHandle): ShapeSquareStarHandle;
        getCutout(self: ShapeSquareStarHandle): number;
        getSideCount(self: ShapeSquareStarHandle): number;
        setCutout(self: ShapeSquareStarHandle, cutout: number): void;
        setSideCount(self: ShapeSquareStarHandle, sideCount: number): void;
    }
    export const ShapeSquareStarApi: ShapeSquareStarApi;

    export interface ShapeStarApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeStarHandle): ShapeStarHandle;
        cloneAsShapeStar(self: ShapeStarHandle): ShapeStarHandle;
        create(): ShapeStarHandle;
        fromShape(shape: ShapeHandle): ShapeStarHandle;
        getCircleInnerRadius(self: ShapeStarHandle): number;
        getCircleOuterRadius(self: ShapeStarHandle): number;
        getCurvedEdges(self: ShapeStarHandle): boolean;
        getInnerRadius(self: ShapeStarHandle): number;
        getLeftCurve(self: ShapeStarHandle): number;
        getMaxCircleInnerRadius(self: ShapeStarHandle): number;
        getPointCount(self: ShapeStarHandle): number;
        getRightCurve(self: ShapeStarHandle): number;
        setCircleInnerRadius(self: ShapeStarHandle, innerRadius: number): void;
        setCircleOuterRadius(self: ShapeStarHandle, outerRadius: number): void;
        setCurvedEdges(self: ShapeStarHandle, curvedEdges: boolean): void;
        setInnerRadius(self: ShapeStarHandle, innerRadius: number): void;
        setLeftCurve(self: ShapeStarHandle, leftCurve: number): void;
        setPointCount(self: ShapeStarHandle, pointCount: number): void;
        setRightCurve(self: ShapeStarHandle, rightCurve: number): void;
    }
    export const ShapeStarApi: ShapeStarApi;

    export interface ShapeTearApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeTearHandle): ShapeTearHandle;
        cloneAsShapeTear(self: ShapeTearHandle): ShapeTearHandle;
        create(): ShapeTearHandle;
        fromShape(shape: ShapeHandle): ShapeTearHandle;
        getBallSize(self: ShapeTearHandle): number;
        getBend(self: ShapeTearHandle): number;
        getCurve(self: ShapeTearHandle): number;
        getFixedBallSize(self: ShapeTearHandle): boolean;
        getTailPosition(self: ShapeTearHandle): number;
        setBallSize(self: ShapeTearHandle, ballSize: number): void;
        setBend(self: ShapeTearHandle, bend: number): void;
        setCurve(self: ShapeTearHandle, curve: number): void;
        setFixedBallSize(self: ShapeTearHandle, fixedBallSize: boolean): void;
        setTailPosition(self: ShapeTearHandle, tailPosition: number): void;
    }
    export const ShapeTearApi: ShapeTearApi;

    export interface ShapeTrapezoidApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeTrapezoidHandle): ShapeTrapezoidHandle;
        cloneAsShapeTrapezoid(self: ShapeTrapezoidHandle): ShapeTrapezoidHandle;
        create(): ShapeTrapezoidHandle;
        fromShape(shape: ShapeHandle): ShapeTrapezoidHandle;
        getLeftPosition(self: ShapeTrapezoidHandle): number;
        getPositions(self: ShapeTrapezoidHandle): ShapeTrapezoidPositions;
        getRightPosition(self: ShapeTrapezoidHandle): number;
        setLeftPosition(self: ShapeTrapezoidHandle, leftPosition: number): void;
        setPositions(self: ShapeTrapezoidHandle, leftPosition: number, rightPosition: number): void;
        setRightPosition(self: ShapeTrapezoidHandle, rightPosition: number): void;
    }
    export const ShapeTrapezoidApi: ShapeTrapezoidApi;

    export interface ShapeTriangleApi extends Omit<ShapeApi, "clone" | "create"> {
        clone(self: ShapeTriangleHandle): ShapeTriangleHandle;
        cloneAsShapeTriangle(self: ShapeTriangleHandle): ShapeTriangleHandle;
        create(): ShapeTriangleHandle;
        fromShape(shape: ShapeHandle): ShapeTriangleHandle;
        getPosition(self: ShapeTriangleHandle): number;
        setPosition(self: ShapeTriangleHandle, position: number): void;
    }
    export const ShapeTriangleApi: ShapeTriangleApi;

    export interface SplineApi {
        clear(self: SplineHandle): void;
        clone(self: SplineHandle): SplineHandle;
        create(): SplineHandle;
        createFromPoints(points: Point[]): SplineHandle;
        createFromProfile(profile: SplineProfile): SplineHandle;
        findPoint(self: SplineHandle, point: Point): SplineFindPointResult;
        getPoint(self: SplineHandle, index: number): Point;
        getPointCount(self: SplineHandle): number;
        insertPoint(self: SplineHandle, point: Point): void;
        isLinear(self: SplineHandle): boolean;
        removePoint(self: SplineHandle, index: number): void;
        replaceOrInsertPoint(self: SplineHandle, point: Point): void;
        setIsLinear(self: SplineHandle, isLinear: boolean): void;
    }
    export const SplineApi: SplineApi;

    export interface TransformApi {
        add(left: Transform, right: Transform, result: Transform): void;
        applyToPoint(self: Transform, point: Point): Point;
        applyToVector(self: Transform, vector: Vector): Vector;
        assign(self: Transform, source: Transform): void;
        compose(self: Transform, data: TransformData): void;
        decompose(self: Transform): TransformData;
        invert(self: Transform): void;
        inverted(self: Transform): Transform;
        multiply(left: Transform, right: Transform, result: Transform): void;
        rotate(self: Transform, rads: number): void;
        scale(self: Transform, x: number, y: number): void;
        setIdentity(self: Transform): void;
        shear(self: Transform, x: number, y: number): void;
        subtract(left: Transform, right: Transform, result: Transform): void;
        translate(self: Transform, x: number, y: number): void;
    }
    export const TransformApi: TransformApi;

    export interface VectorApi {
        absEq(self: Vector): void;
        add(vector: Vector, other: Vector): Vector;
        assign(self: Vector, other: Vector): void;
        cross(vector: Vector, other: Vector): number;
        dot(vector: Vector, other: Vector): number;
        getAbs(vector: Vector): Vector;
        getAngle(vector: Vector): number;
        getAngleDeg(vector: Vector): number;
        getNeg(vector: Vector): Vector;
        getSpangle(vector: Vector): number;
        length(vector: Vector): number;
        lengthSquared(vector: Vector): number;
        makeZero(self: Vector): void;
        negEq(self: Vector): void;
        normalise(vector: Vector): Vector;
        reverse(vector: Vector): Vector;
        rotate(vector: Vector, rads: number): Vector;
        scale(vector: Vector, scale: number): Vector;
        subtract(vector: Vector, other: Vector): Vector;
        transform(vector: Vector, transform: Transform): Vector;
    }
    export const VectorApi: VectorApi;

}
