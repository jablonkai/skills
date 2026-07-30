'use strict';

const { EnumerationResult } = require('affinity:common');
const {
    CurveEdgeSubSelectionApi,
    CurveEdgeSubSelectionItem,
    CurveNodeSubSelectionApi,
    CurveNodeSubSelectionItem,
    FillMeshSubSelectionApi,
    FillSubSelectionApi,
    LineFillMeshSubSelectionApi,
    LineFillSubSelectionApi,
    MeshSubSelectionItem,
    SelectableApi,
    SelectionApi,
    SelectionItemApi,
    SubSelectionApi,
    SubSelectionType,
    TableEdgeSelector,
    TableSubSelectionApi,
    TextSelectionApi,
    TransparencyMeshSubSelectionApi,
    TransparencySubSelectionApi
} = require('affinity:dom');
const { TableAxis } = require('affinity:story');
const { Collection, SpanCollection } = require("./collection.js");
const { HandleObject } = require("./handleobject.js");

// cyclics:
const NodesModule = require("./nodes.js");
function createTypedSubSelection(subSelectionHandle) {
    if (subSelectionHandle == null)
        return null;

	switch (SubSelectionApi.getSubSelectionType(subSelectionHandle).value) {
        case SubSelectionType.CurveEdge.value:
            return new CurveEdgeSubSelection(CurveEdgeSubSelectionApi.fromSubSelection(subSelectionHandle));
		case SubSelectionType.CurveNode.value:
		    return new CurveNodeSubSelection(CurveNodeSubSelectionApi.fromSubSelection(subSelectionHandle));
		case SubSelectionType.Fill.value:
			return new FillSubSelection(FillSubSelectionApi.fromSubSelection(subSelectionHandle));
        case SubSelectionType.FillMesh.value:
            return new FillMeshSubSelection(FillMeshSubSelectionApi.fromSubSelection(subSelectionHandle));
		case SubSelectionType.LineFill.value:
			return new LineFillSubSelection(LineFillSubSelectionApi.fromSubSelection(subSelectionHandle));
        case SubSelectionType.LineFillMesh.value:
            return new LineFillMeshSubSelection(LineFillMeshSubSelectionApi.fromSubSelection(subSelectionHandle));
        case SubSelectionType.Table.value:
            return new TableSubSelection(TableSubSelectionApi.fromSubSelection(subSelectionHandle));
		case SubSelectionType.Text.value:
			return new TextSelection(TextSelectionApi.fromSubSelection(subSelectionHandle));
		case SubSelectionType.Transparency.value:
			return new TransparencySubSelection(TransparencySubSelectionApi.fromSubSelection(subSelectionHandle));
        case SubSelectionType.TransparencyMesh.value:
            return new TransparencyMeshSubSelection(TransparencyMeshSubSelectionApi.fromSubSelection(subSelectionHandle));
		default:
			return new SubSelection(subSelectionHandle);
	}
}

class SelectionItem extends HandleObject {
	
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'SelectionItem';
	}
	
	get isSelectionItem() {
		return true;
	}

	get node() {
		const nodeHandle = SelectionItemApi.getNode(this.handle);
		if (!nodeHandle)
			return null;
		return NodesModule.createTypedNode(nodeHandle);
	}

	getSubSelection(index) {
		return createTypedSubSelection(SelectionItemApi.getSubSelection(this.handle, index));
	}

	getSubSelectionOfType(subSelectionType) {
		const handle = SelectionItemApi.getSubSelectionOfType(this.handle, subSelectionType);
		return handle ? createTypedSubSelection(handle) : handle;
	}

	get subSelectionCount() {
		return SelectionItemApi.getSubSelectionCount(this.handle);
	}

	enumerateSubSelections(callback) {
		if (typeof callback === 'function') {
			function wrapped(subSelectionHandle) {
				return callback(createTypedSubSelection(subSelectionHandle));
			}
			return SelectionItemApi.enumerateSubSelections(this.handle, wrapped);
		}
		return SelectionItemApi.enumerateSubSelections(this.handle, callback);
	}

	get subSelections() {
		const res = [];
        this.enumerateSubSelections(subSelection => {
            res.push(subSelection);
            return EnumerationResult.Continue;
        });
        return res;
	}
}

class Selection extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Selection';
    }

    get length() {
        return SelectionApi.getCount(this.handle);
    }

    at(index) {
        return new SelectionItem(SelectionApi.getItem(this.handle, index));
    }

    get items() {
        return new SpanCollection(this);
    }

	get nodes() {
		return this.items.map(item => item.node).filter(node => node);
	}

	get firstNode() {
		return this.nodes.first;
	}
    
    add(nodeOrItem) {
        if (nodeOrItem.isNode) {
            this.addNode(nodeOrItem);
        } else if (nodeOrItem.isSelectionItem) {
            this.addItem(nodeOrItem);
        } else if (nodeOrItem.isSelectable) {
            this.addSelectable(nodeOrItem);
        } else {
            throw new TypeError("expected Node, SelectionItem, or Selectable");
        }
    }

	addNode(node) {
		return SelectionApi.addNode(this.handle, node.handle);
	}
    
    addItem(item) {
        return SelectionApi.addItem(this.handle, item.handle);
    }
	
	addSelectable(selectable) {
		return SelectionApi.addSelectable(this.handle, selectable.handle);
	}
	
	addSubSelectionForNode(node, subSelection) {
		return SelectionApi.addSubSelectionForNode(this.handle, node.handle, subSelection.handle);
	}
	
	get isSelection() {
		return true;
	}

	getFirstSubSelectionOfType(subSelectionType) {
		const handle = SelectionApi.getFirstSubSelectionOfType(this.handle, subSelectionType);
		return handle ? createTypedSubSelection(handle) : null;
	}

	removeNested() {
		return SelectionApi.removeNested(this.handle);
	}

	containsItem(item) {
		return SelectionApi.containsItem(this.handle, item.handle);
	}
	
	static create(document, items, removeNested) {
		let sel = Selection.createEmpty(document);
		if (items != null) {
			if (items.isNode || items.isSelectionItem || items.isSelectable) {
				sel.add(items);
			}
			else if (items[Symbol.iterator]) {
				for (const item of items) {
					sel.add(item);
				}
			}
			if (removeNested)
				sel.removeNested();
		}
		return sel;
	}

	static createEmpty(document) {
		return new Selection(SelectionApi.createEmpty(document.handle));
	}

	clear() {
		SelectionApi.clear(this.handle);
	}
}

class SubSelection extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SubSelection';
    }

    get isSubSelection() {
        return true;
    }

	get subSelectionType() {
		return SubSelectionApi.getSubSelectionType(this.handle);
	}
}

class CurveNodeSubSelection extends SubSelection {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'CurveNodeSubSelection';
	}

	static create(items) {
		if (items != null) {
			if (items instanceof Collection)
				items = items.toArray();
			else if (!(items instanceof Array))
				items = [items];
		}
		return new CurveNodeSubSelection(CurveNodeSubSelectionApi.create(items));
	}
	
	get isEmpty() {
		return CurveNodeSubSelectionApi.isEmpty(this.handle);
	}

	get itemCount() {
		return CurveNodeSubSelectionApi.getItemCount(this.handle);
	}

	getItem(index) {
		return CurveNodeSubSelectionApi.getItem(this.handle, index);
	}

	enumerateItems(callback) {
		return CurveNodeSubSelectionApi.enumerateItems(this.handle, callback);
	}

	get items() {
		let res = [];
        function callback(range) {
            res.push(range);
            return EnumerationResult.Continue;
        }
        this.enumerateItems(callback);
        return res;
	}

	enumerateItemsWithCurveID(curveID, callback) {
		return CurveNodeSubSelectionApi.enumerateItemsWithCurveID(this.handle, curveID, callback);
	}

	getItemsWithCurveID(curveID) {
		let res = [];
        function callback(range) {
            res.push(range);
            return EnumerationResult.Continue;
        }
        this.enumerateItemsWithCurveID(curveID, callback);
        return res;
	}

	cloneAndAddItems(items) {
		if (items != null) {
			if (items instanceof Collection)
				items = items.toArray();
			else if (!(items instanceof Array))
				items = [items];
		}
		return new CurveNodeSubSelection(CurveNodeSubSelectionApi.cloneAndAddItems(this.handle, items));
	}
	
	cloneAndRemoveItems(items) {
		if (items != null) {
			if (items instanceof Collection)
				items = items.toArray();
			else if (!(items instanceof Array))
				items = [items];
		}
		return new CurveNodeSubSelection(CurveNodeSubSelectionApi.cloneAndRemoveItems(this.handle, items));
	}

	cloneAndRemoveCurves(curveIDs) {
		if (curveIDs != null) {
			if (curveIDs instanceof Collection)
                curveIDs = curveIDs.toArray();
			else if (!(curveIDs instanceof Array))
                curveIDs = [curveIDs];
		}
		return new CurveNodeSubSelection(CurveNodeSubSelectionApi.cloneAndRemoveCurves(this.handle, curveIDs));
	}

	clone() {
		return new CurveNodeSubSelection(CurveNodeSubSelectionApi.clone(this.handle));
	}
}

class CurveEdgeSubSelection extends SubSelection {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CurveEdgeSubSelection';
    }

    static create(items) {
        if (items != null) {
            if (items instanceof Collection)
                items = items.toArray();
            else if (!(items instanceof Array))
                items = [items];
        }
        return new CurveEdgeSubSelection(CurveEdgeSubSelectionApi.create(items));
    }
    
    get isEmpty() {
        return CurveEdgeSubSelectionApi.isEmpty(this.handle);
    }

    get itemCount() {
        return CurveEdgeSubSelectionApi.getItemCount(this.handle);
    }

    getItem(index) {
        return CurveEdgeSubSelectionApi.getItem(this.handle, index);
    }

    enumerateItems(callback) {
        return CurveEdgeSubSelectionApi.enumerateItems(this.handle, callback);
    }

    get items() {
        let res = [];
        function callback(range) {
            res.push(range);
            return EnumerationResult.Continue;
        }
        this.enumerateItems(callback);
        return res;
    }

    enumerateItemsWithCurveID(curveID, callback) {
        return CurveEdgeSubSelectionApi.enumerateItemsWithCurveID(this.handle, curveID, callback);
    }

    getItemsWithCurveID(curveID) {
        let res = [];
        function callback(range) {
            res.push(range);
            return EnumerationResult.Continue;
        }
        this.enumerateItemsWithCurveID(curveID, callback);
        return res;
    }

    cloneAndAddItems(items) {
        if (items != null) {
            if (items instanceof Collection)
                items = items.toArray();
            else if (!(items instanceof Array))
                items = [items];
        }
        return new CurveEdgeSubSelection(CurveEdgeSubSelectionApi.cloneAndAddItems(this.handle, items));
    }
    
    cloneAndRemoveItems(items) {
        if (items != null) {
            if (items instanceof Collection)
                items = items.toArray();
            else if (!(items instanceof Array))
                items = [items];
        }
        return new CurveEdgeSubSelection(CurveEdgeSubSelectionApi.cloneAndRemoveItems(this.handle, items));
    }

    cloneAndRemoveCurves(curveIDs) {
        if (curveIDs != null) {
            if (curveIDs instanceof Collection)
                curveIDs = curveIDs.toArray();
            else if (!(curveIDs instanceof Array))
                curveIDs = [curveIDs];
        }
        return new CurveEdgeSubSelection(CurveEdgeSubSelectionApi.cloneAndRemoveCurves(this.handle, curveIDs));
    }

    clone() {
        return new CurveEdgeSubSelection(CurveEdgeSubSelectionApi.clone(this.handle));
    }
}

class FillMeshSubSelection extends SubSelection {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FillMeshSubSelection';
    }

    get isFillMeshSubSelection() {
        return true;
    }

    get isEmpty() {
        return FillMeshSubSelectionApi.isEmpty(this.handle);
    }

    get itemCount() {
        return FillMeshSubSelectionApi.getItemCount(this.handle);
    }

    enumerateItems(callback) {
        return FillMeshSubSelectionApi.enumerateItems(this.handle, callback);
    }

    get items() {
        let res = [];
        function callback(item) {
            res.push(item);
            return EnumerationResult.Continue;
        }
        this.enumerateItems(callback);
        return res;
    }

    static fromSubSelection(subSelection) {
        return new FillMeshSubSelection(FillMeshSubSelectionApi.fromSubSelection(subSelection.handle));
	}
}

class FillSubSelection extends SubSelection {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'FillSubSelection';
	}

	get index() {
		return FillSubSelectionApi.getIndex(this.handle);
	}

	static fromSubSelection(subSelection) {
		return new FillSubSelection(FillSubSelectionApi.fromSubSelection(subSelection.handle));
	}

	clone() {
		return new FillSubSelection(FillSubSelectionApi.clone(this.handle));
	}

	cloneAsFillSubSelection() {
		return new FillSubSelection(FillSubSelectionApi.cloneAsFillSubSelection(this.handle));
	}
}

class LineFillMeshSubSelection extends SubSelection {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LineFillMeshSubSelection';
    }

    get isLineFillMeshSubSelection() {
        return true;
    }

    get isEmpty() {
        return LineFillMeshSubSelectionApi.isEmpty(this.handle);
    }

    get itemCount() {
        return LineFillMeshSubSelectionApi.getItemCount(this.handle);
    }

    enumerateItems(callback) {
        return LineFillMeshSubSelectionApi.enumerateItems(this.handle, callback);
    }

    get items() {
        let res = [];
        function callback(item) {
            res.push(item);
            return EnumerationResult.Continue;
        }
        this.enumerateItems(callback);
        return res;
    }

    static fromSubSelection(subSelection) {
        return new LineFillMeshSubSelection(LineFillMeshSubSelectionApi.fromSubSelection(subSelection.handle));
    }
}

class LineFillSubSelection extends SubSelection {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'LineFillSubSelection';
	}

	get index() {
		return LineFillSubSelectionApi.getIndex(this.handle);
	}

	static fromSubSelection(subSelection) {
		return new LineFillSubSelection(LineFillSubSelectionApi.fromSubSelection(subSelection.handle));
	}

	clone() {
		return new LineFillSubSelection(LineFillSubSelectionApi.clone(this.handle));
	}

	cloneAsLineFillSubSelection() {
		return new LineFillSubSelection(LineFillSubSelectionApi.cloneAsLineFillSubSelection(this.handle));
	}
}

class TableSubSelection extends SubSelection {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TableSubSelection';
    }

    get isEmpty() {
        return TableSubSelectionApi.isEmpty(this.handle);
    }

    get isRectangle() {
        return TableSubSelectionApi.isRectangle(this.handle);
    }

    get anchor() {
        return TableSubSelectionApi.getAnchor(this.handle);
    }

    get caret() {
        return TableSubSelectionApi.getCaret(this.handle);
    }

    get boundingBox() {
        return TableSubSelectionApi.getBoundingBox(this.handle);
    }

    enumerateCells(callback) {
        return TableSubSelectionApi.enumerateCells(this.handle, callback);
    }

    enumerateEdges(tableAxis, tableEdgeSelector, callback) {
        return TableSubSelectionApi.enumerateEdges(this.handle, tableAxis, tableEdgeSelector, callback);
    }

    get cells() {
        let res = [];
        function callback(cell) {
            res.push(cell);
            return EnumerationResult.Continue;
        }
        this.enumerateCells(callback);
        return res;
    }

    getEdges(tableAxis, tableEdgeSelector) {
        let res = [];
        function callback(edges) {
            res.push(edges);
            return EnumerationResult.Continue;
        }
        this.enumerateEdges(tableAxis, tableEdgeSelector, callback);
        return res;
    }

    static fromSubSelection(subSelection) {
        return new TableSubSelection(TableSubSelectionApi.fromSubSelection(subSelection.handle));
    }
};

class TextSelection extends SubSelection {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'TextSelection';
	}

	static create(rangesOrNull) {
		if (rangesOrNull != null) {
			if (rangesOrNull instanceof Collection)
				rangesOrNull = rangesOrNull.toArray();
			else if (!(rangesOrNull instanceof Array))
				rangesOrNull = [rangesOrNull];
		}
		return new TextSelection(TextSelectionApi.create(rangesOrNull));
	}
	
	get isEmpty() {
		return TextSelectionApi.isEmpty(this.handle);
	}

	get hasMarkedText() {
		return TextSelectionApi.hasMarkedText(this.handle);
	}

	get caret() {
		return TextSelectionApi.getCaret(this.handle);
	}

	get anchor() {
		return TextSelectionApi.getAnchor(this.handle);
	}

	get markedTextBegin() {
		return TextSelectionApi.getMarkedTextBegin(this.handle);
	}

	get markedTextEnd() {
		return TextSelectionApi.getMarkedTextEnd(this.handle);
	}

	get rangeCount() {
		return TextSelectionApi.getRangeCount(this.handle);
	}

	getRange(index) {
		return TextSelectionApi.getRange(this.handle, index);
	}

	enumerateRanges(callback) {
		return TextSelectionApi.enumerateRanges(this.handle, callback);
	}

	get ranges() {
		let res = [];
        function callback(range) {
            res.push(range);
            return EnumerationResult.Continue;
        }
        this.enumerateRanges(callback);
        return res;
	}
};

class TransparencyMeshSubSelection extends SubSelection {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TransparencyMeshSubSelection';
    }

    get isTransparencyMeshSubSelection() {
        return true;
    }

    get isEmpty() {
        return TransparencyMeshSubSelectionApi.isEmpty(this.handle);
    }

    get itemCount() {
        return TransparencyMeshSubSelectionApi.getItemCount(this.handle);
    }

    enumerateItems(callback) {
        return TransparencyMeshSubSelectionApi.enumerateItems(this.handle, callback);
    }

    get items() {
        let res = [];
        function callback(item) {
            res.push(item);
            return EnumerationResult.Continue;
        }
        this.enumerateItems(callback);
        return res;
    }

    static fromSubSelection(subSelection) {
        return new TransparencyMeshSubSelection(TransparencyMeshSubSelectionApi.fromSubSelection(subSelection.handle));
    }
}

class TransparencySubSelection extends SubSelection {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'TransparencySubSelection';
	}

	get index() {
		return TransparencySubSelectionApi.getIndex(this.handle);
	}

	static fromSubSelection(subSelection) {
		return new TransparencySubSelection(TransparencySubSelectionApi.fromSubSelection(subSelection.handle));
	}

	clone() {
		return new TransparencySubSelection(TransparencySubSelectionApi.clone(this.handle));
	}

	cloneAsTransparencySubSelection() {
		return new TransparencySubSelection(TransparencySubSelectionApi.cloneAsTransparencySubSelection(this.handle));
	}
}

module.exports.createTypedSubSelection = createTypedSubSelection;
module.exports.CurveNodeSubSelection = CurveNodeSubSelection;
module.exports.CurveNodeSubSelectionItem = CurveNodeSubSelectionItem;
module.exports.CurveEdgeSubSelection = CurveEdgeSubSelection;
module.exports.CurveEdgeSubSelectionItem = CurveEdgeSubSelectionItem;
module.exports.FillMeshSubSelection = FillMeshSubSelection;
module.exports.FillSubSelection = FillSubSelection;
module.exports.LineFillMeshSubSelection = LineFillMeshSubSelection;
module.exports.LineFillSubSelection = LineFillSubSelection;
module.exports.MeshSubSelectionItem = MeshSubSelectionItem;
module.exports.Selection = Selection;
module.exports.SelectionItem = SelectionItem;
module.exports.SubSelection = SubSelection;
module.exports.SubSelectionType = SubSelectionType;
module.exports.TableAxis = TableAxis;
module.exports.TableEdgeSelector = TableEdgeSelector;
module.exports.TableSubSelection = TableSubSelection;
module.exports.TextSelection = TextSelection;
module.exports.TransparencyMeshSubSelection = TransparencyMeshSubSelection;
module.exports.TransparencySubSelection = TransparencySubSelection;
