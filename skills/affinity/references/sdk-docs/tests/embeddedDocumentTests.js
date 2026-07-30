'use strict';
const {app} = require('/application');
const dommodule = require("affinity:dom");
const {EnumerationResult} = require("affinity:common");
const {Document, DocumentPromises} = require("/document");
const {DocumentCommand} = require("/commands");

const {TestUtils} = require('/tests/testUtils');

function printEmbeddedDocumentNodeInfo(embDocNode) {
    console.log("Selected Page Bounding Box Type:");
    console.log(embDocNode.pageBoundingBoxType);
    console.log("Is PDF Passthrough:");
    console.log(embDocNode.PDFPassthrough);
    console.log("can PDF passthrough be modified:");
    console.log(embDocNode.canSetPDFPassthrough);
    console.log("current raster dpi:");
    console.log(embDocNode.rasterDPI);
    console.log("original host's dpi:");
    console.log(embDocNode.originalHostDPI);
    console.log("can change to linked document:");
    console.log(embDocNode.canMakeLinked);
    console.log("can edit embedded image:");
    console.log(embDocNode.canEditEmbeddedImage);
    console.log("should allow select action:");
    console.log(embDocNode.shouldAllowSelectDocument);
    console.log("is artboard selected:");
    console.log(embDocNode.isArtboardSelected);
    console.log("is artboard a document:");
    console.log(embDocNode.isArtboardDoc);
    console.log("password protected:");
    console.log(embDocNode.needsPassword);
    
}

function enumStrPair(str1, str2) {
    console.log(str1, str2);
    return EnumerationResult.Stop;
}

function testEmbeddedDocumentWithArtboard() {
    let doc = TestUtils.getFile("/EmbDocWithArtboard.afdesign");
    console.log("filename: " + doc.path);
    if (doc) {
        console.log("testing embedded document with artboard");
        const edNode = doc.layers.first;
        console.log(edNode.toString());
        console.assert(edNode.isEmbeddedDocumentNode == true);
        console.assert(edNode.embeddedDocumentHasSpreads == false);
        console.assert(edNode.embeddedDocumentHasArtboards == true);
        console.assert(edNode.embeddedDocumentHasPageBoundingBoxes == true);
        console.assert(edNode.embeddedDocumentHasLayers == false);
        console.assert(edNode.isAffinityFile == true);
        if (edNode.embeddedDocumentHasArtboards) {
            let previd = edNode.selectedArtboardId;
            console.log(previd);
            let artboardlist = edNode.artboards;
            edNode.enumerateArtboards(enumStrPair);
            
            if (artboardlist.length > 2) {
                let newartboard = artboardlist.at(1).artboardID;
                console.log(newartboard);
                doc.selection = edNode;
                let changeartboard = DocumentCommand.createSetEmbeddedDocumentSelectedArtboardID(doc.selection, newartboard);
                let result = doc.executeCommand(changeartboard);
                console.log(result);
                console.assert(edNode.selectedArtboardId == newartboard);
                doc.undo();
                console.assert(edNode.selectedArtboardId == previd);
            }
        }
        doc.close();
        
        console.log("testEmbeddedDocumentWithArtboard OK.");
    }
    
}

function enumLayerVis(lname, vis) {
    console.log(lname, vis);
	return EnumerationResult.Continue;
}


function testEmbeddedDocumentWithLayer() {
    let doc = TestUtils.getFile("/EmbDocWithLayer.afdesign");
    if (doc) {
        const edNode = doc.layers.first;
        console.log(edNode.toString());
        console.assert(edNode.isEmbeddedDocumentNode == true);
        console.assert(edNode.embeddedDocumentHasSpreads == false);
        console.assert(edNode.embeddedDocumentHasArtboards == false);
        console.assert(edNode.embeddedDocumentHasPageBoundingBoxes == true);
        console.assert(edNode.embeddedDocumentHasLayers == true);
        console.assert(edNode.isAffinityFile == true);
        if (edNode.embeddedDocumentHasLayers) {
            const layervislist = edNode.layerVisibilities;
            edNode.enumerateLayerVisibilities(enumLayerVis);
            doc.selection = edNode;
            
            for (let i = 0; i < layervislist.length; i++) {
                let newvis = !layervislist.at(i).visible;
                // create set embedded doc layer visibility requires layer index.
                let changevis = DocumentCommand.createSetEmbeddedDocumentLayerVisibility(doc.selection, i, newvis);
                let result = doc.executeCommand(changevis);
            }
            
            const newlayervislist = edNode.layerVisibilities;
            
            for (let i = 0; i < layervislist.length; i++) {
                console.assert(layervislist.at(i).visible == (!newlayervislist.at(i).visible));
            }
            
            for (const layervis of layervislist) {
                doc.undo();
            }
            
            var newvislist = [];
            for (let i = 0; i < layervislist.length; i++) {
                let newvis = (Math.random() < 0.5);
                newvislist.push(newvis);
                console.log(newvis);
            }
            
            let changeAllVis = DocumentCommand.createSetEmbeddedDocumentAllLayersVisibility(doc.selection, newvislist);
            let resultAllVis = doc.executeCommand(changeAllVis);
            
            const newlayervislist2 = edNode.layerVisibilities;
            
            for (let i = 0; i < newvislist.length; i++) {
                console.log(newvislist[i]);
                console.log(newlayervislist2.at(i).visible);
                console.assert(newvislist[i] == newlayervislist2.at(i).visible);
            }
            
            doc.undo();
        }
        doc.close();
        
        console.log("testEmbeddedDocumentWithLayer OK.");
    }
    
}

function testEmbeddedDocumentWithSpread() {
    let doc = TestUtils.getFile("/EmbDocWithSpread.afdesign");
    if (doc) {
        console.log("testing embedded document with spread");
        const edNode = doc.layers.first;
        console.log(edNode.toString());
        console.assert(edNode.isEmbeddedDocumentNode == true);
        console.assert(edNode.embeddedDocumentHasSpreads == true);
        console.assert(edNode.embeddedDocumentHasArtboards == false);
        console.assert(edNode.embeddedDocumentHasPageBoundingBoxes == true);
        console.assert(edNode.embeddedDocumentHasLayers == false);
        console.assert(edNode.isAffinityFile == true);
        if (edNode.embeddedDocumentHasSpreads) {
            let prevspreadid = edNode.selectedSpreadId;
            console.log(prevspreadid);
            let spreadlist = edNode.getSpreads(false);
            edNode.enumerateSpreads(false, enumStrPair);
            
            if (spreadlist.length > 2) {
                let newspread = spreadlist.at(1).spreadID;
                console.log(newspread);
                doc.selection = edNode;
                let changespread = DocumentCommand.createSetEmbeddedDocumentSelectedSpreadID(doc.selection, newspread);
                let result = doc.executeCommand(changespread);
                console.log(result);
                console.assert(edNode.selectedSpreadId == newspread);
                doc.undo();
                console.assert(edNode.selectedSpreadId == prevspreadid);
            }
        }
        
        doc.close();
        
        console.log("testEmbeddedDocumentWithSpread OK.");
    }
}



function testEmbeddedDocumentWithPDF() {
    let doc = TestUtils.getFile("/EmbDocWithPDF.afdesign");
    if (doc) {
        console.log("testing embedded document with spread");
        const edNode = doc.layers.first;
        printEmbeddedDocumentNodeInfo(edNode);
        console.log(edNode.toString());
        console.assert(edNode.isEmbeddedDocumentNode == true);
        console.assert(edNode.embeddedDocumentHasSpreads == true);
        console.assert(edNode.embeddedDocumentHasArtboards == false);
        console.assert(edNode.embeddedDocumentHasPageBoundingBoxes == true);
        console.assert(edNode.embeddedDocumentHasLayers == true);
        console.assert(edNode.isAffinityFile == false);
        console.assert(edNode.PDFPassthrough == true);
        console.assert(edNode.canSetPDFPassthrough == true);
        
        doc.close();
        
        console.log("testEmbeddedDocumentWithPDF OK.");
    }
}

function testEmbeddedDocumentNodeIfaces() {
    let doc = TestUtils.getFile("/EmbDocWithArtboard.afdesign");
    if (doc) {
        console.log("testing embedded document interfaces");
        const edNode = doc.layers.first;
        console.log(edNode.toString());
        console.assert(edNode.transparencyInterface.toString() == '[object TransparencyInterface]');
        console.assert(edNode.imageResourceInterface.toString()== '[object ImageResourceInterface]');
        
        doc.close();
        
        console.log("testEmbeddedDocumentNodeIfaces OK.");
    }
}


function testEmbeddedDocumentNode() {
    testEmbeddedDocumentWithArtboard();
    testEmbeddedDocumentWithLayer();
    testEmbeddedDocumentWithSpread();
    testEmbeddedDocumentNodeIfaces();
    testEmbeddedDocumentWithPDF();
}

module.exports.testEmbeddedDocumentNode = testEmbeddedDocumentNode;
