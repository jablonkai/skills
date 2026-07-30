'use strict';

const {EffectiveMarginBehaviour} = require("affinity:dom");
const {PhysicalRootInterface} = require("/physicalRootInterface.js");
const {PhysicalRootPropertiesInterface} = require("/physicalRootPropertiesInterface.js");
const {Document, NewDocumentOptions} = require("/document.js");

function runTests() {
	let options = NewDocumentOptions.createDefault();
	options.createArtboard = true;
	let doc = Document.createFromOptions(options);
	console.assert(doc);

	let artboardInterface = doc.layers.first.artboardInterface;
	console.log(artboardInterface);
	console.log('description:', artboardInterface.description);
	console.log('enabled:', artboardInterface.enabled);
	console.log('topOfPageMargin:', artboardInterface.topOfPageMargin);
	console.log('spreadBaseBox:', artboardInterface.spreadBaseBox);
	console.log('baseBox:', artboardInterface.baseBox);
	console.log('pageCount:', artboardInterface.physicalRootInterface.physicalRootProperties.pageCount);
	console.log('\n');

	let artboardProperties = artboardInterface.properties;
	console.log(artboardProperties);
	console.log('getMarginBox:', artboardProperties.getMarginBox(EffectiveMarginBehaviour.PageBoxIfDisabled));
	console.log('marginFill:', artboardProperties.marginFill);
	console.log('\n');

	let marginsInterface = artboardProperties.marginsInterface;
	console.log(marginsInterface);
	console.log('hasMargins:', marginsInterface.hasMargins);
	console.log('useMargins:', marginsInterface.useMargins);
	console.log('\n');

	let physicalRootPropertiesInterface = artboardProperties.physicalRootPropertiesInterface;
	console.log(physicalRootPropertiesInterface);
	console.log('pageCount:', physicalRootPropertiesInterface.pageCount);
	console.log('\n');

	let physicalRootInterface = artboardInterface.physicalRootInterface;
	console.log(physicalRootInterface);
	console.log('properties:', physicalRootInterface.physicalRootProperties);
	console.log('\n');

	let spread = doc.spreads.first;
	console.log(spread);
	console.log('physicalRootInterface.physicalRootProperties:', spread.physicalRootInterface.physicalRootProperties);
	console.log('PhysicalRootInterface.fromNode:', PhysicalRootInterface.fromNode(spread));
	console.log('PhysicalRootPropertiesInterface.fromNode:', PhysicalRootPropertiesInterface.fromNode(spread));
	console.log('\n');

	//doc.close();
}

module.exports.runTests = runTests;
