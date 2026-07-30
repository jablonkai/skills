'use strict';

const { ColourSpaceType } = require('affinity:colours');
const { DocumentCommandApi } = require('affinity:commands');
const { EnumerationResult, ErrorCode, UnitType } = require('affinity:common');
const {
    ContentType,
    DocumentApi,
    DocumentExportRecordApi,
    DocumentExportRecordsApi,
    DocumentHistoryApi,
    DocumentHistoryItemApi,
    DocumentLoadMode,
    DocumentPresetApi,
    DocumentSnapshotApi,
    FileExportAreaApi,
    FileExportOptionsApi,
    ImagePlacement,
    LoadDocumentOptionsApi,
    NewDocumentOptionsApi,
    PackageResourcesPolicy,
    SpatialAnchor
} = require('affinity:dom');
const { RasterFormat } = require('affinity:raster');
const { Collection } = require('./collection.js');
const { Colour, ColourProfile } = require('./colours.js');
const { DrawingScale } = require('./drawingscale.js');
const { FillDescriptor, SolidFill } = require('./fills.js');
const { HandleObject } = require('./handleobject.js');
const { LineStyle, LineStyleMask } = require('./linestyle.js');
const { PixelBuffer } = require('./rasterobject.js');
const { RasterSelection } = require('./rasterselection.js');
const { ShapeCornerType, ShapeRectangle } = require('./shapes.js');
const { UnitValueConverter } = require('./units.js');

// cyclics:
const CommandsModule = require('./commands.js');
const NodesModule = require('./nodes.js');
const SelectionsModule = require('./selections.js');

class DocumentSnapshot extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DocumentSnapshot';
    }

    get description() {
        return DocumentSnapshotApi.getDescription(this.handle);
    }

    get format() {
        return DocumentSnapshotApi.getFormat(this.handle);
    }

    createDocument() {
        return new Document(DocumentApi.createFromSnapshot(this.handle));
    }

    createDocumentAsync(callback) {
        if (typeof callback === 'function') {
            function wrappedCallback(errorCode, documentHandle) {
                let document = documentHandle ? new Document(documentHandle) : null;
                return callback(errorCode, document);
            }
            return DocumentApi.createFromSnapshotAsync(this.handle, false, wrappedCallback);
        }
        return DocumentApi.createFromSnapshotAsync(this.handle, false, callback);
    }
}


class DocumentPreset extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DocumentPreset';
    }

    static enumerateAll(callback) {
        if (typeof callback === 'function') {
            function wrapped(presetHandle) {
                return callback(new DocumentPreset(presetHandle));
            }
            return DocumentPresetApi.enumerateAll(wrapped);
        }
        return DocumentPresetApi.enumerateAll(callback);
    }

    static get all() {
        let res = [];
        DocumentPreset.enumerateAll(preset => {
            res.push(preset);
            return EnumerationResult.Continue;
        });
        return res;
    }

    get name() {
        return DocumentPresetApi.getName(this.handle);
    }

    get units() {
        return DocumentPresetApi.getUnits(this.handle);
    }

    get imagePlacement() {
        return DocumentPresetApi.getImagePlacement(this.handle);
    }

    get isTransparentBackground() {
        return DocumentPresetApi.getIsTransparentBackground(this.handle);
    }

    get createArtboard() {
        return DocumentPresetApi.getCreateArtboard(this.handle);
    }

    get isFavourite() {
        return DocumentPresetApi.getIsFavourite(this.handle);
    }

    get facing() {
        return DocumentPresetApi.getFacing(this.handle);
    }

    get verticalStack() {
        return DocumentPresetApi.getVerticalStack(this.handle);
    }

    get doublePageStart() {
        return DocumentPresetApi.getDoublePageStart(this.handle);
    }

    get rasterFormat() {
        return DocumentPresetApi.getRasterFormat(this.handle);
    }

    get width() {
        return DocumentPresetApi.getWidth(this.handle);
    }

    get height() {
        return DocumentPresetApi.getHeight(this.handle);
    }

    get dpi() {
        return DocumentPresetApi.getDpi(this.handle);
    }

    get viewDpi() {
        return DocumentPresetApi.getViewDpi(this.handle);
    }

    get margins() {
        return DocumentPresetApi.getMargins(this.handle);
    }

    get marginsEnabled() {
        return DocumentPresetApi.getMarginsEnabled(this.handle);
    }

    get bleed() {
        return DocumentPresetApi.getBleed(this.handle);
    }

    get useDrawingScale() {
        return DocumentPresetApi.getUseDrawingScale(this.handle);
    }

    get drawingScale() {
        return new DrawingScale(DocumentPresetApi.getDrawingScale(this.handle));
    }

    get colourProfileName() {
        return DocumentPresetApi.getColourProfileName(this.handle);
    }

    get isMultiPage() {
        return DocumentPresetApi.getIsMultiPage(this.handle);
    }
}

class Layers extends Collection {    
    constructor(documentNodeHandle, reverse, all) {
        const genFunc = function*() {
            for (const spread of NodesModule.getNodeChildren(documentNodeHandle, NodesModule.NodeChildType.Main, reverse)) {
                const f = all ? NodesModule.getNodeChildrenRecursive : NodesModule.getNodeChildren;
                for (const node of f(spread.handle, NodesModule.NodeChildType.Main, reverse)) {
                    yield node;
                }
            }
        };
        super(genFunc);

        this.reverse = function() {
            return new Layers(documentNodeHandle, !reverse, all);
        }

        Object.defineProperty(this, "all", {
            get: function() {
                return new Layers(documentNodeHandle, reverse, true);
            }
        });
    }
}


class Document extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'Document';
    }

    get promises() {
        return new DocumentPromises(this);
    }

    isSameObject(otherDocument) {
        return DocumentApi.isSameObject(this.handle, otherDocument.handle);
    }

    get isOpen() {
        return DocumentApi.isOpen(this.handle);
    }

    get path() {
        return DocumentApi.getPath(this.handle);
    }

    #rootNode;
    get rootNode() {
        if (!this.#rootNode)
            this.#rootNode = new NodesModule.DocumentNode(DocumentApi.getRootNode(this.handle));
        return this.#rootNode;
    }

    get selection() {
        return new SelectionsModule.Selection(DocumentApi.getCurrentSelection(this.handle));
    }

    set selection(items) {
        if (items) {
            if (items.isSelection) {
                const cmd = DocumentCommandApi.createSetSelectionCommand(items.handle);
                DocumentApi.executeCommand(this.handle, cmd);
            }
            else {
                this.selection = SelectionsModule.Selection.create(this, items);
            }
        }
        else {
            const cmd = DocumentCommandApi.createSetSelectionCommand(SelectionsModule.Selection.createEmpty(this).handle);
            DocumentApi.executeCommand(this.handle, cmd);
        }
    }

    get dpi() {
        return DocumentApi.getDpi(this.handle);
    }

    get viewdpi() {
        return DocumentApi.getViewDpi(this.handle);
    }

    executeCommand(documentCommand, preview) {
        return DocumentApi.executeCommand(this.handle, documentCommand.handle, preview);
    }

    #history
    get history() {
        if (!this.#history)
            this.#history = DocumentHistory.create(this);
        return this.#history;
    }

    static get current() {
        let res = DocumentApi.getCurrent();
        if (res && DocumentApi.isOpen(res))
            res = new Document(res);
        else
            res = null;
        return res;
    }

    static enumerateAll(callback) {
        if (typeof callback === 'function') {
            function wrapped(documentHandle) {
                return callback(new Document(documentHandle));
            }
            return DocumentApi.enumerateOpen(wrapped);
        }
        return DocumentApi.enumerateOpen(callback);
    }

    static get all() {
        const res = [];
        function callback(document) {
            res.push(document);
            return EnumerationResult.Continue;
        }
        Document.enumerateAll(callback);
        return res;
    }

    static load(path) {
        return new Document(DocumentApi.load(path).document);
    }

    get isEmbedded() {
        return DocumentApi.isEmbedded(this.handle);
    }

    get isReadOnly() {
        return DocumentApi.isReadOnly(this.handle);
    }

    get mustSaveAs() {
        return DocumentApi.mustSaveAs(this.handle);
    }

    get needsSaving() {
        return DocumentApi.needsSaving(this.handle);
    }

    get isDirty() {
        return DocumentApi.isDirty(this.handle);
    }

    get title() {
        return DocumentApi.getTitle(this.handle);
    }

    save() {
        return DocumentApi.save(this.handle);
    }

    saveAs(path) {
        return DocumentApi.saveAs(this.handle, path);
    }

    saveAsPackage(path, policy) {
        return DocumentApi.saveAsPackage(this.handle, path, policy);
    }

    get colourProfile() {
        return new ColourProfile(DocumentApi.getColourProfile(this.handle));
    }

    get currentSpread() {
        return new NodesModule.SpreadNode(DocumentApi.getCurrentSpread(this.handle));
    }

    close() {
        return DocumentApi.close(this.handle);
    }

    static createFromPreset(preset, landscape) {
        if (landscape == null)
            landscape = preset.width > preset.height;
        return new Document(DocumentApi.createFromPreset(preset.handle, landscape));
    }

    static createFromOptions(options) {
        return new Document(DocumentApi.createFromOptions(options.handle));
    }

    static create(options) {
        return new Document(DocumentApi.createFromOptions(options.handle));
    }

    export(path, exportOptions, exportArea, size) {
        return new DocumentExportRecords(DocumentApi.export(this.handle, path, exportOptions.handle, exportArea?.handle, size));
    }

    get format() {
        return DocumentApi.getFormat(this.handle);
    }

    set format(format) {
        const cmd = CommandsModule.DocumentCommand.createConvertDocumentFormat(format);
        return this.executeCommand(cmd);
    }
    
    get maskFormat() {
        return DocumentApi.getMaskFormat(this.handle);
    }

    get units() {
        return DocumentApi.getUnits(this.handle);
    }

    set units(value) {
        if (!this.units.equals(value)) {
            const cmd = CommandsModule.DocumentCommand.createSetDocumentUnits(value);
            return this.executeCommand(cmd);
        }
    }

    get unitValueConverter() {
        return new UnitValueConverter(DocumentApi.getUnitValueConverter(this.handle));
    }

    enumerateSnapshots(callback) {
        if (typeof callback === 'function') {
            function wrapped(handle) {
                return callback(new DocumentSnapshot(handle));
            }
            return DocumentApi.enumerateSnapshots(this.handle, wrapped);
        }
        return DocumentApi.enumerateSnapshots(this.handle, callback);
    }

    get snapshotCount() {
        return DocumentApi.getSnapshotCount(this.handle);
    }

    get snapshots() {
        const res = [];
        function callback(snapshot) {
            res.push(snapshot);
            return EnumerationResult.Continue;
        }
        this.enumerateSnapshots(callback);
        return res;
    }
    
    get currentSnapshotIndex() {
        return DocumentApi.getCurrentSnapshotIndex(this.handle);
    }
    
    get currentSnapshotHistoryIndex() {
        return DocumentApi.getCurrentSnapshotHistoryIndex(this.handle);
    }
    
    get currentSnapshot() {
        const snapshotHandle = DocumentApi.getCurrentSnapshot(this.handle);
        return snapshotHandle ? new DocumentSnapshot(snapshotHandle) : null;
    }

    get rasterSelection() {
        return new RasterSelection(DocumentApi.getRasterSelection(this.handle));
    }

    enumerateFontNames(callback) {
        return DocumentApi.enumerateFontNames(this.handle, callback);
    }
    
    getFontNames() {
        let names = [];
        this.enumerateFontNames((name, isInstalled) => { 
            names.push(name); 
            return EnumerationResult.Continue;
        });
        return names;
    }

    get sessionUuid() {
        return DocumentApi.getSessionUuid(this.handle);
    }

    get persistentUuid() {
        return DocumentApi.getPersistentUuid(this.handle);
    }
    
    // async
    static getCurrentAsync(callback) {
        if (typeof callback === 'function') {
            function wrapped(errorCode, documentHandle) {
                const document = documentHandle ? new Document(documentHandle) : null;
                callback(errorCode, document);
            }
            return DocumentApi.getCurrentAsync(wrapped);
        }
        return DocumentApi.getCurrentAsync(callback);
    }
    
    static loadAsync(path, callback) {
        if (typeof callback === 'function') {
            function wrapped(errorCode, desc, documentHandle) {
                const document = documentHandle ? new Document(documentHandle) : null;
                callback(errorCode, desc, document);
            }
            return DocumentApi.loadAsync(path, null, wrapped);
        }
        return DocumentApi.loadAsync(path, null, callback);
    }

    static createFromPresetAsync(preset, landscape, callback) {
        if (landscape == null) {
            landscape = preset.width > preset.height;
        }
        if (typeof callback === 'function') {
            function wrapped(errorCode, documentHandle) {
                const document = documentHandle ? new Document(documentHandle) : null;
                callback(errorCode, document);
            }
            return DocumentApi.createFromPresetAsync(preset.handle, landscape, wrapped);
        }
        return DocumentApi.createFromPresetAsync(preset.handle, landscape, callback);
    }

    static createAsync(options, callback) {
        if (typeof callback === 'function') {
            function wrapped(errorCode, documentHandle) {
                const document = documentHandle ? new Document(documentHandle) : null;
                callback(errorCode, document);
            }
            return DocumentApi.createFromOptionsAsync(options.handle, wrapped);
        }
        return DocumentApi.createFromOptionsAsync(options.handle, callback);
    }

    executeCommandAsync(command, callback, preview) {
        return DocumentApi.executeCommandAsync(this.handle, command.handle, callback, preview);
    }

    saveAsync(callback) {
        return DocumentApi.saveAsync(this.handle, callback);
    }

    saveAsAsync(path, callback) {
        return DocumentApi.saveAsAsync(this.handle, path, callback);
    }

    saveAsPackageAsync(path, policy, callback) {
        return DocumentApi.saveAsPackageAsync(this.handle, path, policy, callback);
    }

    closeAsync(callback) {
        return DocumentApi.closeAsync(this.handle, callback);
    }

    exportAsync(path, exportOptions, exportArea, size, callback) {
        if (typeof callback === 'function') {
            function wrapped(errorCode, documentExportRecordsHandle) {
                const documentExportRecords = documentExportRecordsHandle ? new DocumentExportRecords(documentExportRecordsHandle) : null;
                callback(errorCode, documentExportRecords);
            }
            return DocumentApi.exportAsync(this.handle, path, exportOptions.handle, exportArea?.handle, size, wrapped);
        }
        return DocumentApi.exportAsync(this.handle, path, exportOptions.handle, exportArea?.handle, size, callback);
    }

    // helpers
    get sizePixels() {
        const bbox = this.rootNode.baseBoxInterface.baseBox;
        return {
            width: bbox.width,
            height: bbox.height,
        };
    }

    get widthPixels() {
        const bbox = this.rootNode.baseBoxInterface.baseBox;
        return bbox.width;
    }

    get heightPixels() {
        const bbox = this.rootNode.baseBoxInterface.baseBox;
        return bbox.height;
    }

    get layers() {
        return new Layers(this.rootNode.handle, false, false);
    }

    get spreads() {
        return new NodesModule.NodeChildrenOnly(this.rootNode.handle, NodesModule.NodeChildType.Main, false);
    }
    
    get artboards() {
        return this.spreads.first.artboards;
    }

    get hasArtboards() {
        return this.spreads.first.artboardCount > 0;
    }

    get canUndo() {
        return this.history.canUndo;
    }

    get canRedo() {
        return this.history.canRedo;
    }

    get undoDescription() {
        return this.history.undoDescription;
    }

    get redoDescription() {
        return this.history.redoDescription;
    }

    // synchronous command helpers
    #ensureSelection(selection) {
        if (selection == null || selection.isSelection)
            return selection;
        else
            return SelectionsModule.Selection.create(this, selection);
    }

    #makeFillDescriptor(fillDescriptor) {
        if (fillDescriptor == null) {
            return FillDescriptor.createNone();
        }
        if (fillDescriptor instanceof FillDescriptor) {
            return fillDescriptor;
        }
        if (fillDescriptor instanceof SolidFill) {
            return FillDescriptor.createSolid(fillDescriptor);
        }
        if (fillDescriptor instanceof Colour) {
            return FillDescriptor.createSolid(fillDescriptor);
        }
        return fillDescriptor;
    }
    undo() {
        this.history.undo();
    }

    redo() {
        this.history.redo();
    }

    selectAll(selectOnCurrentLayerOnly, preview) {
        const cmd = CommandsModule.DocumentCommand.createSelectAll(selectOnCurrentLayerOnly);
        return this.executeCommand(cmd, preview);
    }

    deleteSelection(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createDeleteSelection(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setEditable(editable, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetEditable(this.#ensureSelection(selection), editable);
        return this.executeCommand(cmd, preview);
    }

    lockSelection(selection, preview) {
        return this.setEditable(false, selection, preview);
    }
    
    unlockSelection(selection, preview) {
        return this.setEditable(true, selection, preview);
    }

    setArtboardEnabled(enabled, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetArtboardEnabled(this.#ensureSelection(selection), enabled);
        return this.executeCommand(cmd, preview);
    }

    setVisible(visible, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetVisibility(this.#ensureSelection(selection), visible);
        return this.executeCommand(cmd, preview);
    }

    showSelection(selection, preview) {
        return this.setVisible(true, selection, preview);
    }

    hideSelection(selection, preview) {
        return this.setVisible(false, selection, preview);
    }

    showAll(preview) {
        const cmd = CommandsModule.DocumentCommand.createShowAll();
        return this.executeCommand(cmd, preview);
    }
    
    addNode(nodeDefinition, targetNode = null, childList = NodesModule.NodeChildType.Main, preview) {
        const builder = CommandsModule.AddChildNodesCommandBuilder.create();
        if (targetNode != null) {
            builder.setInsertionTarget(targetNode);
        }
        builder.addNode(nodeDefinition);
        return this.executeCommand(builder.createCommand(true, childList), preview);
    }

    setBlendMode(blendMode, setPassthrough, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBlendMode(this.#ensureSelection(selection), blendMode, setPassthrough);
        return this.executeCommand(cmd, preview);
    }

    setOpacity(opacity, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOpacity(this.#ensureSelection(selection), opacity);
        return this.executeCommand(cmd, preview);
    }

    setBrushFillOpacity(opacity, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBrushFillOpacity(this.#ensureSelection(selection), opacity, options);
        return this.executeCommand(cmd, preview);
    }

    setLineFillOpacity(opacity, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetLineFillOpacity(this.#ensureSelection(selection), opacity, options);
        return this.executeCommand(cmd, preview);
    }

    setBrushFillDescriptor(fillDescriptorOrColour, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBrushFill(this.#ensureSelection(selection), this.#makeFillDescriptor(fillDescriptorOrColour), options);
        return this.executeCommand(cmd, preview);
    }

    setPenFillDescriptor(fillDescriptorOrColour, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPenFill(this.#ensureSelection(selection), this.#makeFillDescriptor(fillDescriptorOrColour), options);
        return this.executeCommand(cmd, preview);
    }

    setTransparencyFillDescriptor(fillDescriptor, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetTransparencyFill(this.#ensureSelection(selection), this.#makeFillDescriptor(fillDescriptor), options);
        return this.executeCommand(cmd, preview);
    }

    setLineStyleDescriptor(lineStyleDescriptor, selection, options = null, preview = false) {
        const cmd = CommandsModule.DocumentCommand.createSetLineStyleDescriptor(this.#ensureSelection(selection), lineStyleDescriptor, options);
        return this.executeCommand(cmd, preview);
    }

    setLineStyle(lineStyle, selection, options = null, preview = false) {
        const cmd = CommandsModule.DocumentCommand.createSetLineStyle(this.#ensureSelection(selection), lineStyle, options);
        return this.executeCommand(cmd, preview);
    }

    setLineCap(cap, selection, preview) {
        const lineStyle = LineStyle.createDefault();
        lineStyle.cap = cap;
        return this.setLineStyle(lineStyle, this.#ensureSelection(selection), {lineStyleMask: LineStyleMask.Cap}, preview);
    }

    setLineJoin(join, selection, preview) {
        const lineStyle = LineStyle.createDefault();
        lineStyle.join = join;
        return this.setLineStyle(lineStyle, this.#ensureSelection(selection), {lineStyleMask: LineStyleMask.Join}, preview);
    }

    setLineType(type, selection, preview) {
        const lineStyle = LineStyle.createDefault();
        lineStyle.type = type;
        return this.setLineStyle(lineStyle, this.#ensureSelection(selection), {lineStyleMask: LineStyleMask.Type}, preview);
    }

    setLineWeight(weight, selection, preview) {
        const lineStyle = LineStyle.createDefault();
        lineStyle.weight = weight;
        return this.setLineStyle(lineStyle, this.#ensureSelection(selection), {lineStyleMask: LineStyleMask.Weight}, preview);
    }

    setLineWeightPts(weightInPts, selection, preview) {
        const lineStyle = LineStyle.createDefault();
        const pointsToPixels = this.dpi / 72;
        lineStyle.weight = weightInPts * pointsToPixels;
        return this.setLineStyle(lineStyle, this.#ensureSelection(selection), {lineStyleMask: LineStyleMask.Weight}, preview);
    }

    setDashPattern(dashPattern, selection, preview) {
        const lineStyle = LineStyle.createDefault();
        lineStyle.dashPattern = dashPattern;
        return this.setLineStyle(lineStyle, this.#ensureSelection(selection), {lineStyleMask: LineStyleMask.DashPattern}, preview);
    }

    setDashPhase(dashPhase, selection, preview) {
        const lineStyle = LineStyle.createDefault();
        lineStyle.dashPhase = dashPhase;
        return this.setLineStyle(lineStyle, this.#ensureSelection(selection), {lineStyleMask: LineStyleMask.DashPhase}, preview);
    }

    setBalancedDashes(balanced, selection, preview) {
        const lineStyle = LineStyle.createDefault();
        lineStyle.hasBalancedDashes = balanced;
        return this.setLineStyle(lineStyle, this.#ensureSelection(selection), {lineStyleMask: LineStyleMask.BalancedDashes}, preview);
    }

    setStrokeAlignment(strokeAlignment, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetStrokeAlignment(this.#ensureSelection(selection), strokeAlignment);
        return this.executeCommand(cmd, preview);
    }

    importMacro(path) {
        const cmd = CommandsModule.DocumentCommand.createImportMacro(path);
        return this.executeCommand(cmd);
    }

    exportMacro(path) {
        const cmd = CommandsModule.DocumentCommand.createExportMacro(path);
        return this.executeCommand(cmd);
    }
    
    generateImage(prompt) {
        const cmd = CommandsModule.DocumentCommand.createGenerateImage(prompt);
        return this.executeCommand(cmd);
    }
    
    detectDepth() {
        const cmd = CommandsModule.DocumentCommand.createDetectDepth();
        return this.executeCommand(cmd);
    }
    
    colourise() {
        const cmd = CommandsModule.DocumentCommand.createColourise();
        return this.executeCommand(cmd);
    }
    
    generateImage(prompt) {
        const cmd = CommandsModule.DocumentCommand.createGenerateImage(prompt);
        return this.executeCommand(cmd);
    }
    
    generativeEditImage(prompt) {
        const cmd = CommandsModule.DocumentCommand.createGenerativeEditImage(prompt);
        return this.executeCommand(cmd);
    }

    clearMacro() {
        const cmd = CommandsModule.DocumentCommand.createClearMacro();
        return this.executeCommand(cmd);
    }

    startRecordingMacro() {
        const cmd = CommandsModule.DocumentCommand.createStartRecordingMacro();
        return this.executeCommand(cmd);
    }

    stopRecordingMacro() {
        const cmd = CommandsModule.DocumentCommand.createStopRecordingMacro();
        return this.executeCommand(cmd);
    }
    
    removeBackground() {
        const cmd = CommandsModule.DocumentCommand.createRemoveBackground();
        return this.executeCommand(cmd);
    }
    
    selectSubject() {
        const cmd = CommandsModule.DocumentCommand.createSelectSubject();
        return this.executeCommand(cmd);
    }

    addGuide(horizontal, pixels96, preview) {
        const cmd = CommandsModule.DocumentCommand.createAddGuide(horizontal, pixels96);
        return this.executeCommand(cmd, preview);
    }

    moveGuide(horizontal, index, newPixels96, preview) {
        const cmd = CommandsModule.DocumentCommand.createMoveGuide(horizontal, index, newPixels96);
        return this.executeCommand(cmd, preview);
    }

    removeGuide(horizontal, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveGuide(horizontal, index);
        return this.executeCommand(cmd, preview);
    }

    setGuidesColour(colour, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGuidesColour(colour);
        return this.executeCommand(cmd, preview);
    }

    setLayerDescription(description, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetDescription(this.#ensureSelection(selection), description);
        return this.executeCommand(cmd, preview);
    }

    setTagColour(colour, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetTagColour(this.#ensureSelection(selection), colour);
        return this.executeCommand(cmd, preview);
    }

    setCurveNodeStyle(style, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetCurveNodeStyle(this.#ensureSelection(selection), style);
        return this.executeCommand(cmd, preview);
    }

    deleteCurveNodes(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createDeleteCurveNodes(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setShape(shape, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetShape(this.#ensureSelection(selection), shape, options);
        return this.executeCommand(cmd, preview);
    }

    setShapeFloatParam(key, value, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetShapeFloatParam(this.#ensureSelection(selection), key, value, options);
        return this.executeCommand(cmd, preview);
    }

    setShapeIntParam(key, value, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetShapeIntParam(this.#ensureSelection(selection), key, value);
        return this.executeCommand(cmd, preview);
    }

    setShapeBoolParam(key, value, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetShapeBoolParam(this.#ensureSelection(selection), key, value);
        return this.executeCommand(cmd, preview);
    }

    setShapeEnumParam(key, value, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetShapeEnumParam(this.#ensureSelection(selection), key, value);
        return this.executeCommand(cmd, preview);
    }

    setBrushFillIsAnchoredToSpread(anchoredToSpread, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBrushFillIsAnchoredToSpread(this.#ensureSelection(selection), anchoredToSpread, options);
        return this.executeCommand(cmd, preview);
    }

    setPenFillIsAnchoredToSpread(anchoredToSpread, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPenFillIsAnchoredToSpread(this.#ensureSelection(selection), anchoredToSpread, options);
        return this.executeCommand(cmd, preview);
    }

    setTransparencyFillIsAnchoredToSpread(anchoredToSpread, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetTransparencyFillIsAnchoredToSpread(this.#ensureSelection(selection), anchoredToSpread, options);
        return this.executeCommand(cmd, preview);
    }
    
    rasteriseObjects(selection, rasteriseContentsOnly, clipToSpread, preview) {
        const cmd = CommandsModule.DocumentCommand.createRasteriseObjects(this.#ensureSelection(selection), rasteriseContentsOnly, clipToSpread);
        return this.executeCommand(cmd, preview);
    }
    
    convertToCurves(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createConvertToCurves(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setBrushHatchFillAttributes(attr, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBrushHatchFillAttributes(this.#ensureSelection(selection), attr, options);
        return this.executeCommand(cmd, preview);
    }

    setPenHatchFillAttributes(attr, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPenHatchFillAttributes(this.#ensureSelection(selection), attr, options);
        return this.executeCommand(cmd, preview);
    }

    setTransparencyHatchFillAttributes(attr, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetTransparencyHatchFillAttributes(this.#ensureSelection(selection), attr, options);
        return this.executeCommand(cmd, preview);
    }

    clearPreviews() {
        const cmd = CommandsModule.DocumentCommand.createClearPreviews();
        return this.executeCommand(cmd);
    }

    applyTransform(transform, selection, options, preview) {
        const cmd = CommandsModule.DocumentCommand.createTransform(this.#ensureSelection(selection), transform, options);
        return this.executeCommand(cmd, preview);
    }

    applyGroupTransform(xDataOrNull, yDataOrNull, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createGroupTransform(this.#ensureSelection(selection), xDataOrNull, yDataOrNull);
        return this.executeCommand(cmd, preview);
    }

    setText(text, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetText(this.#ensureSelection(selection), text);
        return this.executeCommand(cmd, preview);
    }
    
    formatText(delta, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createFormatText(this.#ensureSelection(selection), delta);
        return this.executeCommand(cmd, preview);
    }

    insertGlyph(glyph, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createInsertGlyph(this.#ensureSelection(selection), glyph);
        return this.executeCommand(cmd, preview);
    }

    insertGlyphAt(glyph, textNode, position, preview) {
        const selection = SelectionsModule.Selection.create(this, textNode);
        const textSelection = SelectionsModule.TextSelection.create([{begin:position, end:position}]);
        selection.addSubSelection(textNode, textSelection);
        const cmd = CommandsModule.DocumentCommand.createInsertGlyph(selection, glyph);
        return this.executeCommand(cmd, preview);
    }
    
    imageTrace(edgeThreshold, curveFittingTolerance, selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createImageTrace(this.#ensureSelection(selection), edgeThreshold, curveFittingTolerance);
        return this.executeCommand(cmd, preview);
    }
    
    rasterSelectAll(preview){
        const cmd = CommandsModule.DocumentCommand.createRasterSelectAll();
        return this.executeCommand(cmd, preview);
    }
    
    rasterDeselect(preview){
        const cmd = CommandsModule.DocumentCommand.createRasterDeselect();
        return this.executeCommand(cmd, preview);
    }
    
    rasterInvertSelection(preview){
        const cmd = CommandsModule.DocumentCommand.createRasterInvertSelection();
        return this.executeCommand(cmd, preview);
    }
    
    rasterReselect(preview){
        const cmd = CommandsModule.DocumentCommand.createRasterReselect();
        return this.executeCommand(cmd, preview);
    }

    setRasterSelectionFromPolygon(polygon, operation, isAntialias, featherRadius, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetRasterSelectionFromPolygon(polygon, operation, isAntialias, featherRadius);
        return this.executeCommand(cmd, preview);
    }

    setRasterSelectionFromObject(node, useIntensity, operation, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetRasterSelectionFromObject(node, useIntensity, operation);
        return this.executeCommand(cmd, preview);
    }

    /**
    * @deprecated Use setRasterSelectionFromPolygon instead.
    */
    rasterSelectPolygon(polygon, operation, isAntialias, featherRadius, preview) {
        console.warn("Using deprecated Document.rasterSelectPolygon() function. Use setRasterSelectionFromPolygon() instead.");
        return this.setRasterSelectionFromPolygon(polygon, operation, isAntialias, featherRadius, preview);
    }

    growShrinkRasterSelection(radius, circular, preview) {
        const cmd = CommandsModule.DocumentCommand.createGrowShrinkRasterSelection(radius, circular);
        return this.executeCommand(cmd, preview);
    }
    
    featherRasterSelection(radius, preview) {
        const cmd = CommandsModule.DocumentCommand.createFeatherRasterSelection(radius);
        return this.executeCommand(cmd, preview);
    }
    
    smoothRasterSelection(radius, preview) {
        const cmd = CommandsModule.DocumentCommand.createSmoothRasterSelection(radius);
        return this.executeCommand(cmd, preview);
    }
    
    outlineRasterSelection(radius, alignment, circular, preview) {
        const cmd = CommandsModule.DocumentCommand.createOutlineRasterSelection(radius, alignment, circular);
        return this.executeCommand(cmd, preview);
    }
    
    flatten(preview) {
        const cmd = CommandsModule.DocumentCommand.createFlatten();
        return this.executeCommand(cmd, preview);
    }

    mergeVisible(preview) {
        const cmd = CommandsModule.DocumentCommand.createMergeVisible();
        return this.executeCommand(cmd, preview);
    }

    // LayerEffectCommands
    setAllLayerEffectsScaleWithObject(selection, scaleWithObject, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetAllLayerEffectsScaleWithObject(this.#ensureSelection(selection), scaleWithObject);
        return this.executeCommand(cmd, preview);
    }

    removeAllLayerEffects(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveAllLayerEffects(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    // BevelEmbossLayerEffectCommands
    setBevelEmbossLayerEffectBlendMode(selection, blendMode, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateBevelEmbossLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateBevelEmbossLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectEnabled(selection, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectEnabled(this.#ensureSelection(selection), enabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectOpacity(selection, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectOpacity(this.#ensureSelection(selection), opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectRadius(selection, radius, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectRadius(this.#ensureSelection(selection), radius, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeBevelEmbossLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveBevelEmbossLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectScaleWithObject(this.#ensureSelection(selection), scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffect(selection, layerEffect, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffect(this.#ensureSelection(selection), layerEffect);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectColour(selection, colourType, colour, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectColour(this.#ensureSelection(selection), colourType, colour, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectDirection(selection, azimuth, elevation, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectDirection(this.#ensureSelection(selection), azimuth, elevation, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectInverted(selection, inverted, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectInverted(this.#ensureSelection(selection), inverted, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectLinkDepth(selection, linkDepth, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectLinkDepth(this.#ensureSelection(selection), linkDepth, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectParam(selection, param, value, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectParam(this.#ensureSelection(selection), param, value, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectShadowBlendMode(selection, blendMode, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectShadowBlendMode(this.#ensureSelection(selection), blendMode, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setBevelEmbossLayerEffectType(selection, bevelType, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetBevelEmbossLayerEffectType(this.#ensureSelection(selection), bevelType, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // OutlineLayerEffectCommands
    setOutlineLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateOutlineLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateOutlineLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectEnabled(selection, index, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectEnabled(this.#ensureSelection(selection), index, enabled);
        return this.executeCommand(cmd, preview);
    }

    moveOutlineLayerEffect(selection, fromIndex, toIndex, preview) {
        const cmd = CommandsModule.DocumentCommand.createMoveOutlineLayerEffect(this.#ensureSelection(selection), fromIndex, toIndex);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectOpacity(selection, index, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectOpacity(this.#ensureSelection(selection), index, opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectRadius(selection, index, radius, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectRadius(this.#ensureSelection(selection), index, radius, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeOutlineLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveOutlineLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectScaleWithObject(this.#ensureSelection(selection), index, scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffect(selection, layerEffect, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffect(this.#ensureSelection(selection), layerEffect, index);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectAlignment(selection, alignment, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectAlignment(this.#ensureSelection(selection), alignment, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectColour(selection, colour, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectColour(this.#ensureSelection(selection), colour, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectFill(selection, gradientFill, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectFill(this.#ensureSelection(selection), gradientFill, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectFillTransform(selection, fillDescriptor, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectFillTransform(this.#ensureSelection(selection), fillDescriptor, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOutlineLayerEffectFillType(selection, fillType, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOutlineLayerEffectFillType(this.#ensureSelection(selection), fillType, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // PhongBevelLayerEffectCommands
    duplicatePhongBevelLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicatePhongBevelLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectEnabled(selection, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectEnabled(this.#ensureSelection(selection), enabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectOpacity(selection, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectOpacity(this.#ensureSelection(selection), opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectRadius(selection, radius, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectRadius(this.#ensureSelection(selection), radius, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removePhongBevelLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemovePhongBevelLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectScaleWithObject(this.#ensureSelection(selection), scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffect(selection, layerEffect, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffect(this.#ensureSelection(selection), layerEffect);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectAmbient(selection, ambient, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectAmbient(this.#ensureSelection(selection), ambient, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectAmbientColour(selection, colour, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectAmbientColour(this.#ensureSelection(selection), colour, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectDepth(selection, depth, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectDepth(this.#ensureSelection(selection), depth, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectDiffuse(selection, diffuse, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectDiffuse(this.#ensureSelection(selection), diffuse, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectLinkDepth(selection, linkDepth, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectLinkDepth(this.#ensureSelection(selection), linkDepth, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectShininess(selection, shininess, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectShininess(this.#ensureSelection(selection), shininess, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectSoften(selection, soften, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectSoften(this.#ensureSelection(selection), soften, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectSpecular(selection, specular, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectSpecular(this.#ensureSelection(selection), specular, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectSpecularColour(selection, colour, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectSpecularColour(this.#ensureSelection(selection), colour, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setPhongBevelLayerEffectLights(selection, lights, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetPhongBevelLayerEffectLights(this.#ensureSelection(selection), lights, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // InnerShadowLayerEffectCommands
    setInnerShadowLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateInnerShadowLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateInnerShadowLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setInnerShadowLayerEffectEnabled(selection, index, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffectEnabled(this.#ensureSelection(selection), index, enabled);
        return this.executeCommand(cmd, preview);
    }

    moveInnerShadowLayerEffect(selection, fromIndex, toIndex, preview) {
        const cmd = CommandsModule.DocumentCommand.createMoveInnerShadowLayerEffect(this.#ensureSelection(selection), fromIndex, toIndex);
        return this.executeCommand(cmd, preview);
    }

    setInnerShadowLayerEffectOpacity(selection, index, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffectOpacity(this.#ensureSelection(selection), index, opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setInnerShadowLayerEffectRadius(selection, index, radius, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffectRadius(this.#ensureSelection(selection), index, radius, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeInnerShadowLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveInnerShadowLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setInnerShadowLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffectScaleWithObject(this.#ensureSelection(selection), index, scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setInnerShadowLayerEffect(selection, layerEffect, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffect(this.#ensureSelection(selection), layerEffect, index);
        return this.executeCommand(cmd, preview);
    }

    setInnerShadowLayerEffectColour(selection, colour, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffectColour(this.#ensureSelection(selection), colour, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setInnerShadowLayerEffectIntensity(selection, index, intensity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffectIntensity(this.#ensureSelection(selection), index, intensity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setInnerShadowLayerEffectOffsetAngle(selection, offset, angle, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerShadowLayerEffectOffsetAngle(this.#ensureSelection(selection), offset, angle, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // InnerGlowLayerEffectCommands
    setInnerGlowLayerEffectBlendMode(selection, blendMode, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerGlowLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateInnerGlowLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateInnerGlowLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setInnerGlowLayerEffectEnabled(selection, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerGlowLayerEffectEnabled(this.#ensureSelection(selection), enabled);
        return this.executeCommand(cmd, preview);
    }

    setInnerGlowLayerEffectOpacity(selection, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerGlowLayerEffectOpacity(this.#ensureSelection(selection), opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setInnerGlowLayerEffectRadius(selection, radius, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerGlowLayerEffectRadius(this.#ensureSelection(selection), radius, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeInnerGlowLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveInnerGlowLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setInnerGlowLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerGlowLayerEffectScaleWithObject(this.#ensureSelection(selection), scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setInnerGlowLayerEffect(selection, layerEffect, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerGlowLayerEffect(this.#ensureSelection(selection), layerEffect);
        return this.executeCommand(cmd, preview);
    }

    setInnerGlowLayerEffectColour(selection, colour, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerGlowLayerEffectColour(this.#ensureSelection(selection), colour, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setInnerGlowLayerEffectIntensity(selection, intensity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetInnerGlowLayerEffectIntensity(this.#ensureSelection(selection), intensity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // ColourOverlayLayerEffectCommands
    setColourOverlayLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetColourOverlayLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateColourOverlayLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateColourOverlayLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setColourOverlayLayerEffectEnabled(selection, index, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetColourOverlayLayerEffectEnabled(this.#ensureSelection(selection), index, enabled);
        return this.executeCommand(cmd, preview);
    }

    moveColourOverlayLayerEffect(selection, fromIndex, toIndex, preview) {
        const cmd = CommandsModule.DocumentCommand.createMoveColourOverlayLayerEffect(this.#ensureSelection(selection), fromIndex, toIndex);
        return this.executeCommand(cmd, preview);
    }

    setColourOverlayLayerEffectOpacity(selection, index, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetColourOverlayLayerEffectOpacity(this.#ensureSelection(selection), index, opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeColourOverlayLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveColourOverlayLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setColourOverlayLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetColourOverlayLayerEffectScaleWithObject(this.#ensureSelection(selection), index, scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setColourOverlayLayerEffect(selection, layerEffect, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetColourOverlayLayerEffect(this.#ensureSelection(selection), layerEffect, index);
        return this.executeCommand(cmd, preview);
    }

    setColourOverlayLayerEffectColour(selection, colour, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetColourOverlayLayerEffectColour(this.#ensureSelection(selection), colour, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // GradientOverlayLayerEffectCommands
    setGradientOverlayLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGradientOverlayLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateGradientOverlayLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateGradientOverlayLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setGradientOverlayLayerEffectEnabled(selection, index, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGradientOverlayLayerEffectEnabled(this.#ensureSelection(selection), index, enabled);
        return this.executeCommand(cmd, preview);
    }

    moveGradientOverlayLayerEffect(selection, fromIndex, toIndex, preview) {
        const cmd = CommandsModule.DocumentCommand.createMoveGradientOverlayLayerEffect(this.#ensureSelection(selection), fromIndex, toIndex);
        return this.executeCommand(cmd, preview);
    }

    setGradientOverlayLayerEffectOpacity(selection, index, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGradientOverlayLayerEffectOpacity(this.#ensureSelection(selection), index, opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeGradientOverlayLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveGradientOverlayLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setGradientOverlayLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGradientOverlayLayerEffectScaleWithObject(this.#ensureSelection(selection), index, scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setGradientOverlayLayerEffect(selection, layerEffect, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGradientOverlayLayerEffect(this.#ensureSelection(selection), layerEffect, index);
        return this.executeCommand(cmd, preview);
    }

    setGradientOverlayLayerEffectFill(selection, gradientFill, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGradientOverlayLayerEffectFill(this.#ensureSelection(selection), gradientFill, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setGradientOverlayLayerEffectFillTransform(selection, transform, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGradientOverlayLayerEffectFillTransform(this.#ensureSelection(selection), transform, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // OuterGlowLayerEffectCommands
    setOuterGlowLayerEffectBlendMode(selection, blendMode, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterGlowLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateOuterGlowLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateOuterGlowLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setOuterGlowLayerEffectEnabled(selection, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterGlowLayerEffectEnabled(this.#ensureSelection(selection), enabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterGlowLayerEffectOpacity(selection, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterGlowLayerEffectOpacity(this.#ensureSelection(selection), opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterGlowLayerEffectRadius(selection, radius, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterGlowLayerEffectRadius(this.#ensureSelection(selection), radius, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeOuterGlowLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveOuterGlowLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setOuterGlowLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterGlowLayerEffectScaleWithObject(this.#ensureSelection(selection), scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterGlowLayerEffect(selection, layerEffect, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterGlowLayerEffect(this.#ensureSelection(selection), layerEffect);
        return this.executeCommand(cmd, preview);
    }

    setOuterGlowLayerEffectColour(selection, colour, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterGlowLayerEffectColour(this.#ensureSelection(selection), colour, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterGlowLayerEffectIntensity(selection, intensity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterGlowLayerEffectIntensity(this.#ensureSelection(selection), intensity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // OuterShadowLayerEffectCommands
    setOuterShadowLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateOuterShadowLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateOuterShadowLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffectEnabled(selection, index, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectEnabled(this.#ensureSelection(selection), index, enabled);
        return this.executeCommand(cmd, preview);
    }

    moveOuterShadowLayerEffect(selection, fromIndex, toIndex, preview) {
        const cmd = CommandsModule.DocumentCommand.createMoveOuterShadowLayerEffect(this.#ensureSelection(selection), fromIndex, toIndex);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffectOpacity(selection, index, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectOpacity(this.#ensureSelection(selection), index, opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffectRadius(selection, index, radius, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectRadius(this.#ensureSelection(selection), index, radius, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeOuterShadowLayerEffect(selection, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveOuterShadowLayerEffect(this.#ensureSelection(selection), index);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectScaleWithObject(this.#ensureSelection(selection), index, scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffect(selection, layerEffect, index, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffect(this.#ensureSelection(selection), layerEffect, index);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffectColour(selection, colour, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectColour(this.#ensureSelection(selection), colour, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffectIntensity(selection, index, intensity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectIntensity(this.#ensureSelection(selection), index, intensity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffectKnocksOut(selection, knocksOut, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectKnocksOut(this.#ensureSelection(selection), knocksOut, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setOuterShadowLayerEffectOffsetAngle(selection, offset, angle, index, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetOuterShadowLayerEffectOffsetAngle(this.#ensureSelection(selection), offset, angle, index, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    // GaussianBlurLayerEffectCommands
    setGaussianBlurLayerEffectBlendMode(selection, blendMode, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGaussianBlurLayerEffectBlendMode(this.#ensureSelection(selection), blendMode, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    duplicateGaussianBlurLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createDuplicateGaussianBlurLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setGaussianBlurLayerEffectEnabled(selection, enabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGaussianBlurLayerEffectEnabled(this.#ensureSelection(selection), enabled);
        return this.executeCommand(cmd, preview);
    }

    setGaussianBlurLayerEffectOpacity(selection, opacity, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGaussianBlurLayerEffectOpacity(this.#ensureSelection(selection), opacity, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setGaussianBlurLayerEffectRadius(selection, radius, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGaussianBlurLayerEffectRadius(this.#ensureSelection(selection), radius, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    removeGaussianBlurLayerEffect(selection, preview) {
        const cmd = CommandsModule.DocumentCommand.createRemoveGaussianBlurLayerEffect(this.#ensureSelection(selection));
        return this.executeCommand(cmd, preview);
    }

    setGaussianBlurLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGaussianBlurLayerEffectScaleWithObject(this.#ensureSelection(selection), scaleWithObject, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setGaussianBlurLayerEffect(selection, layerEffect, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGaussianBlurLayerEffect(this.#ensureSelection(selection), layerEffect);
        return this.executeCommand(cmd, preview);
    }

    setGaussianBlurLayerEffectPreserveAlpha(selection, preserveAlpha, enableIfDisabled, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetGaussianBlurLayerEffectPreserveAlpha(this.#ensureSelection(selection), preserveAlpha, enableIfDisabled);
        return this.executeCommand(cmd, preview);
    }

    setDocumentProperties(documentProperties) {
        const cmd = CommandsModule.DocumentCommand.createSetDocumentProperties(documentProperties);
        return this.executeCommand(cmd);
    }

    setSpreadSizeWithAnchor(spreadNode, width, height, anchor) {
        const cmd = CommandsModule.DocumentCommand.createSetSpreadSizeWithAnchor(spreadNode, width, height, anchor);
        return this.executeCommand(cmd);
    }

    setArtboardSizeWithAnchor(artboardInterface, width, height, anchor) {
        const cmd = CommandsModule.DocumentCommand.createSetArtboardSizeWithAnchor(artboardInterface, width, height, anchor);
        return this.executeCommand(cmd);
    }

    setSpreadDocumentProperties(spreadNode, spreadDocumentProperties) {
        const cmd = CommandsModule.DocumentCommand.createSetSpreadDocumentProperties(spreadNode, spreadDocumentProperties);
        return this.executeCommand(cmd);
    }

    setArtboardDocumentProperties(artboardInterface, artboardDocumentProperties) {
        const cmd = CommandsModule.DocumentCommand.createSetArtboardDocumentProperties(artboardInterface, artboardDocumentProperties);
        return this.executeCommand(cmd);
    }

    addArtboard(artboardDefinition, copyProperties, copyGuides, preview) {
        const cmd = CommandsModule.DocumentCommand.createAddArtboard(artboardDefinition, copyProperties, copyGuides);
        return this.executeCommand(cmd, preview);
    }

    addRectangularArtboard(rectangle, copyProperties, copyGuides, preview) {
        const def = NodesModule.ShapeNodeDefinition.createDefault();
        def.setShape(ShapeRectangle.create());
        def.setBoundingRectangle(rectangle);
        return this.addArtboard(def, copyProperties, copyGuides, preview);
    }

    // TODO: asynchronous command helpers
    setLayerDescriptionAsync(description, selection, callback, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetDescription(this.#ensureSelection(selection), description);
        return this.executeCommandAsync(cmd, callback, preview);
    }

    setTagColourAsync(colour, selection, callback, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetTagColour(this.#ensureSelection(selection), colour);
        return this.executeCommandAsync(cmd, callback, preview);
    }

    setShapeAsync(shape, selection, callback, preview) {
        const cmd = CommandsModule.DocumentCommand.createSetShape(this.#ensureSelection(selection), shape);
        return this.executeCommandAsync(cmd, callback, preview);
    }

    clearPreviewsAsync(callback) {
        const cmd = CommandsModule.DocumentCommand.createClearPreviews();
        return this.executeCommandAsync(cmd, callback);
    }

    get pageCount() {
        return this.rootNode.pageCount;
    }

    get spreadCount() {
        return this.rootNode.spreadCount;
    }
}


class NewDocumentOptions extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'NewDocumentOptions';
    }

    static createDefault() {
        return new NewDocumentOptions(NewDocumentOptionsApi.createDefault());
    }
    
    static createFromPreset(documentPreset) {
        return new NewDocumentOptions(NewDocumentOptionsApi.createFromPreset(documentPreset.handle));
    }
    
    static getMaxDpi(unit, dimension) {
        return NewDocumentOptionsApi.getMaxDpi(unit, dimension);
    }
    
    static getMaxSize(unit, dpi) {
        return NewDocumentOptionsApi.getMaxSize(unit, dpi);
    }
    
    set units(unit) {
        NewDocumentOptionsApi.setUnits(this.handle, unit);
    }
    
    set imagePlacement(placement) {
        NewDocumentOptionsApi.setImagePlacement(this.handle, placement);
    }
    
    set isTransparentBackground(isTransparent) {
        NewDocumentOptionsApi.setIsTransparentBackground(this.handle, isTransparent);
    }
    
    set createArtboard(createArtboard) {
        NewDocumentOptionsApi.setCreateArtboard(this.handle, createArtboard);
    }
    
    set isFacing(facing) {
        NewDocumentOptionsApi.setIsFacing(this.handle, facing);
    }
    
    set isLandscape(isLandscape) {
        NewDocumentOptionsApi.setIsLandscape(this.handle, isLandscape);
    }
    
    set isVerticalStack(verticalStack) {
        NewDocumentOptionsApi.setIsVerticalStack(this.handle, verticalStack);
    }
    
    set isDoublePageStart(doublePageStart) {
        NewDocumentOptionsApi.setIsDoublePageStart(this.handle, doublePageStart);
    }
    
    set rasterFormat(format) {
        NewDocumentOptionsApi.setRasterFormat(this.handle, format);
    }
    
    set colourProfile(profile) {
        NewDocumentOptionsApi.setColourProfile(this.handle, profile);
    }
    
    set width(w) {
        NewDocumentOptionsApi.setWidth(this.handle, w);
    }
    
    set height(h) {
        NewDocumentOptionsApi.setHeight(this.handle, h);
    }
    
    set dpi(dpi) {
        NewDocumentOptionsApi.setDpi(this.handle, dpi);
    }
    
    set viewDpi(dpi) {
        NewDocumentOptionsApi.setViewDpi(this.handle, dpi);
    }
    
    set margins(margins) {
        NewDocumentOptionsApi.setMargins(this.handle, margins);
    }
    
    set marginsEnabled(enabled) {
        NewDocumentOptionsApi.setMarginsEnabled(this.handle, enabled);
    }
    
    set bleed(bleed) {
        NewDocumentOptionsApi.setBleed(this.handle, bleed);
    }
    
    set pageCount(pCount) {
        NewDocumentOptionsApi.setPageCount(this.handle, pCount);
    }
    
    set createMaster(create) {
        NewDocumentOptionsApi.setCreateMaster(this.handle, create);
    }
    
    set useDrawingScale(use) {
        NewDocumentOptionsApi.setUseDrawingScale(this.handle, use);
    }
    
    set drawingScale(drawingScale) {
        NewDocumentOptionsApi.setDrawingScale(this.handle, drawingScale.handle);
    }
    
    set isMultiPage(isMultiPage) {
        NewDocumentOptionsApi.setIsMultiPage(this.handle, isMultiPage);
    }
}

class DocumentHistoryItem extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'DocumentHistoryItem';
    }

    get hasAlternateFutures() {
        return DocumentHistoryItemApi.hasAlternateFutures(this.handle);
    }

    get command() {
        return new DocumentCommand(DocumentHistoryItemApi.getCommand(this.handle));
    }

    get thumbnail() {
        return new PixelBuffer(DocumentHistoryItemApi.getThumbnail(this.handle));
    }

    get description() {
        return DocumentHistoryItemApi.getDescription(this.handle);
    }

    dispose() {
        DocumentHistoryItemApi.dispose();
    }
}


// note this takes a document handle
class DocumentHistory extends HandleObject {
    #documentHandle;

    constructor(documentHandle) {
        super(DocumentApi.getHistory(documentHandle));
        this.#documentHandle = documentHandle;
    }

    static create(document) {
        const history = new DocumentHistory(document.handle);
        return history;
    }

    get documentHandle() {
        return this.#documentHandle;
    }

    get document() {
        return new Document(this.#documentHandle);
    }

    get [Symbol.toStringTag]() {
        return 'DocumentHistory';
    }

    get position() {
        return DocumentHistoryApi.getUndoPosition(this.handle);
    }

    set position(index) {
        const commandHandle = DocumentCommandApi.createSetHistoryIndexCommand(index - 1);
        DocumentApi.executeCommand(this.#documentHandle, commandHandle);
    }

    get size() {
        return DocumentHistoryApi.getSize(this.handle);
    }

    get canUndo() {
        return DocumentHistoryApi.canUndo(this.handle);
    }

    get canRedo() {
        return DocumentHistoryApi.canRedo(this.handle);
    }

    get undoDescription() {
        return DocumentHistoryApi.getUndoDescription(this.handle);
    }

    get redoDescription() {
        return DocumentHistoryApi.getRedoDescription(this.handle);
    }

    getItem(index) {
        let itemHandle = DocumentHistoryApi.getItem(this.handle, index);
        if (itemHandle) {
            return new DocumentHistoryItem(itemHandle);
        }
        else {
            return null;
        }
    }

    enumerateItems(callback) {
        if (typeof callback === 'function') {
            function wrapped(documentHistoryItemHandle) {
                return callback(new DocumentHistoryItem(documentHistoryItemHandle));
            }
            return DocumentHistoryApi.enumerateItems(this.handle, wrapped);
        }
        return DocumentHistoryApi.enumerateItems(this.handle, callback);
    }

    get items() {
        let items = [];
        this.enumerateItems((item) => {
            items.push(item);
            return false;
        });
        return items;
    }

    undo(preview) {
        const commandHandle = DocumentCommandApi.createUndoCommand();
        DocumentApi.executeCommand(this.documentHandle, commandHandle, preview);
    }

    redo(preview) {
        const commandHandle = DocumentCommandApi.createRedoCommand();
        DocumentApi.executeCommand(this.documentHandle, commandHandle, preview);
    }

    undoAsync(callback, preview) {
        const commandHandle = DocumentCommandApi.createUndoCommand();
        DocumentApi.executeCommandAsync(this.documentHandle, commandHandle, callback, preview);
    }

    redoAsync(callback, preview) {
        const commandHandle = DocumentCommandApi.createRedoCommand();
        DocumentApi.executeCommandAsync(this.documentHandle, commandHandle, callback, preview);
    }
}

class DocumentExportRecord extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'DocumentExportRecord';
    }

    get path() {
        return DocumentExportRecordApi.getPath(this.handle);
    }

    get hasWarnings() {
        return DocumentExportRecordApi.hasWarnings(this.handle);
    }

    get warningMessage() {
        return DocumentExportRecordApi.getWarningMessage(this.handle);
    }

    get errorMessage() {
        return DocumentExportRecordApi.getErrorMessage(this.handle);
    }

    get result() {
        return DocumentExportRecordApi.getResult(this.handle);
    }

    get isSuccess() {
        const result_value = this.result.value;
        return result_value == ErrorCode.OK || result_value == ErrorCode.WARNINGS_ONLY;
    }
}

class DocumentExportRecords extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'DocumentExportRecords';
    }

    get count() {
        return DocumentExportRecordsApi.getCount(this.handle);
    }

    enumerate(callback) {
        if (typeof callback === 'function') {
            function wrapped(documentExportRecordHandle) {
                return callback(new DocumentExportRecord(documentExportRecordHandle));
            }
            return DocumentExportRecordsApi.enumerate(this.handle, wrapped);
        }
        return DocumentExportRecordsApi.enumerate(this.handle, callback);
    }

    get all() {
        let records = [];
        this.enumerate(record => {
            records.push(record);
            return false;
        });
        return records;
    }
}

class FileExportOptions extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FileExportOptions';
    }

    static enumeratePresetNames(callback) {
        return FileExportOptionsApi.enumeratePresetNames(callback);
    }

    static createWithPresetName(presetName) {
        return new FileExportOptions(FileExportOptionsApi.createWithPresetName(presetName));
    }

    static createForCanvaExport(dpi) {
        return new FileExportOptions(FileExportOptionsApi.createForCanvaExport(dpi));
    }

    static get allPresetNames() {
        let presetNames = [];
        FileExportOptions.enumeratePresetNames(presetName => {
            presetNames.push(presetName);
            return EnumerationResult.Continue;
        });
        return presetNames;
    }
}

class FileExportArea extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FileExportArea';
    }

    clone() {
        return new FileExportArea(FileExportAreaApi.clone(this.handle));
    }

    static createForWholeDocument() {
        return new FileExportArea(FileExportAreaApi.createForWholeDocument());
    }

    static createForCurrentSpread() {
        return new FileExportArea(FileExportAreaApi.createForCurrentSpread());
    }

    static createForCurrentPage() {
        return new FileExportArea(FileExportAreaApi.createForCurrentPage());
    }

    static createForArtboard(artboardInterface) {
        return new FileExportArea(FileExportAreaApi.createForArtboard(artboardInterface.handle));
    }

    static createForSpreads(strPages) {
        return new FileExportArea(FileExportAreaApi.createForSpreads(strPages));
    }

    static createForPages(strPages) {
        return new FileExportArea(FileExportAreaApi.createForPages(strPages));
    }

    static createForSelection(selection) {
        return new FileExportArea(FileExportAreaApi.createForSelection(selection?.handle));
    }

    static createForSelectionArea(selection) {
        return new FileExportArea(FileExportAreaApi.createForSelectionArea(selection?.handle));
    }
}

class LoadDocumentOptions extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LoadDocumentOptions';
    }

    set dpi(dpi) {
        LoadDocumentOptionsApi.setDpi(this.handle, dpi);
    }

    set hostDpi(dpi) {
        LoadDocumentOptionsApi.setHostDpi(this.handle, dpi);
    }

    set password(password) {
        LoadDocumentOptionsApi.setPassword(this.handle, password);
    }

    set colourSpace(colourSpace) {
        LoadDocumentOptionsApi.setColourSpace(this.handle, colourSpace);
    }

    set format(colourFormat) {
        LoadDocumentOptionsApi.setFormat(this.handle, colourFormat);
    }

    set loadMode(loadmode) {
        LoadDocumentOptionsApi.setLoadMode(this.handle, loadmode);
    }

    static createDefault() {
        return new LoadDocumentOptions(LoadDocumentOptionsApi.createDefault());
    }
}

class DocumentPromises {
    #document;

    constructor(document) {
        if (document == null || document == undefined) {
            throw new Error("Invalid Document");
        }
        this.#document = document;
    }

    get [Symbol.toStringTag]() {
        return 'DocumentPromises';
    }

    get document() {
        return this.#document;
    }

    static load(path) {
        return new Promise((resolve, reject) => {
            Document.loadAsync(path, (err, desc, document) => {
                if (err)
                    reject({ "error" : err, "desc" : desc });
                else {
                    resolve(document ? new DocumentPromises(document) : null);
                }
            });
        });
    }

    static getCurrent() {
        return new Promise((resolve, reject) => {
            Document.getCurrentAsync((err, document) => {
                if (err)
                    reject(err);
                else
                    resolve(document ? new DocumentPromises(document) : null);
            });
        });
    }

    static createFromPreset(preset, landscape) {
        return new Promise((resolve, reject) => {
            Document.createFromPresetAsync(preset, landscape, (err, document) => {
                if (err)
                    reject(err);
                else
                    resolve(document ? new DocumentPromises(document) : null);
            });
        });
    }

    static create(options) {
        return new Promise((resolve, reject) => {
            Document.createAsync(options, (err, document) => {
                if (err)
                    reject(err);
                else
                    resolve(document ? new DocumentPromises(document) : null);
            });
        });
    }

    export(path, exportOptions, exportArea, size) {
        return new Promise((resolve, reject) => {
            this.document.exportAsync(path, exportOptions, exportArea, size, (err, documentExportRecords) => {
                if (err)
                    reject(err);
                else
                    resolve(documentExportRecords);
            });
        });
    }

    executeCommand(command, preview) {
        return new Promise((resolve, reject) => {
            this.document.executeCommandAsync(command, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            }, preview);
        });
    }

    save() {
        return new Promise((resolve, reject) => {
            this.document.saveAsync((err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }

    saveAs(path) {
        return new Promise((resolve, reject) => {
            this.document.saveAsAsync(path, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }

    saveAsPackage(path, policy) {
        return new Promise((resolve, reject) => {
            this.document.saveAsPackageAsync(path, policy, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }

    close() {
        return new Promise((resolve, reject) => {
            this.document.closeAsync((err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
}


module.exports.ColourSpaceType = ColourSpaceType;
module.exports.Document = Document;
module.exports.DocumentExportRecord = DocumentExportRecord;
module.exports.DocumentExportRecords = DocumentExportRecords;
module.exports.DocumentHistory = DocumentHistory;
module.exports.DocumentLoadMode = DocumentLoadMode;
module.exports.DocumentPreset = DocumentPreset;
module.exports.DocumentPromises = DocumentPromises;
module.exports.DocumentSnapshot = DocumentSnapshot;
module.exports.ErrorCode = ErrorCode;
module.exports.FileExportArea = FileExportArea;
module.exports.FileExportOptions = FileExportOptions;
module.exports.ImagePlacement = ImagePlacement;
module.exports.LoadDocumentOptions = LoadDocumentOptions;
module.exports.NewDocumentOptions = NewDocumentOptions;
module.exports.PackageResourcesPolicy = PackageResourcesPolicy;
module.exports.RasterFormat = RasterFormat;
module.exports.SpatialAnchor = SpatialAnchor;
module.exports.UnitType = UnitType;
