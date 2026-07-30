const { Dialog, HorizontalAlignment } = require('/dialog');
const { SVG11 } = require('/colours');

function main() {
    const dlg = Dialog.create("Flexible Layout Demo")
    const col = dlg.addColumn();
    const topGrp = col.addGroup();
    const topStack = topGrp.addColumnStack();
    const visGrp = topStack.addColumn().addGroup("Visibilities");
    visGrp.addStaticText(null, "This group uses a ColumnStack to form 2 columns of controls.").setIsFullWidth();
    const visStack = visGrp.addColumnStack();
    const visLeftGroup = visStack.addColumn().addGroup();
    const visRightGroup = visStack.addColumn().addGroup();
    const visTicks = [
        visLeftGroup.addCheckBox("Show Group 1" ).setValue(true).setIsFullWidth(),
        visLeftGroup.addCheckBox("Show Group 2" ).setValue(true).setIsFullWidth(),
        visLeftGroup.addCheckBox("Show Group 3" ).setValue(true).setIsFullWidth(),
        visLeftGroup.addCheckBox("Show Group 4" ).setValue(true).setIsFullWidth(),
        visRightGroup.addCheckBox("Show Group 5" ).setValue(true).setIsFullWidth(),
        visRightGroup.addCheckBox("Show Group 6" ).setValue(true).setIsFullWidth(),
        visRightGroup.addCheckBox("Show Group 7" ).setValue(true).setIsFullWidth(),
        visRightGroup.addCheckBox("Show Group 8" ).setValue(true).setIsFullWidth(),
    ];

    const topRightCol = topStack.addColumn();    
    const grp1 = topRightCol.addGroup("Group 1")
    grp1.addStaticText(null, "You can hide individual groups or both, preserving space for the column.").setIsFullWidth();
    const grp2 = topRightCol.addGroup("Group 2");
    const stack = grp2.addColumnStack();
    stack.addColumn().addGroup().addButton("Alert").setAlignment(HorizontalAlignment.Left).setOnValueChangedHandler(() => alert("The left button was pressed."));
    stack.addColumn().addGroup().addButton("Alert").setAlignment(HorizontalAlignment.Centre).setOnValueChangedHandler(() => alert("The middle button was pressed."));
    stack.addColumn().addGroup().addButton("Alert").setAlignment(HorizontalAlignment.Right).setOnValueChangedHandler(() => alert("The right button was pressed."));

    visTicks[0].onValueChangedHandler = ()=> {grp1.isVisible = visTicks[0].value};
    visTicks[1].onValueChangedHandler = ()=> {grp2.isVisible = visTicks[1].value};

    function ColourGroup(stack, name) {
        this.column = stack.addColumn();
        this.group = this.column.addGroup(name);
        this.setPicker = this.group.addButtonSet("Colour Type", ["RGB", "CMYK"]);
        this.rgb = [
            this.group.addColourPicker("Red", SVG11.red),
            this.group.addColourPicker("Green", SVG11.green),
            this.group.addColourPicker("Blue", SVG11.blue)
        ];
        this.cmyk = [
            this.group.addColourPicker("Cyan", SVG11.cyan).setIsVisible(false),
            this.group.addColourPicker("Magenta", SVG11.magenta).setIsVisible(false),
            this.group.addColourPicker("Yellow", SVG11.yellow).setIsVisible(false)
        ];
        this.setPicker.onValueChangedHandler = ()=>{
            const rgbIds = this.rgb.map(ctrl => ctrl.itemID);
            const cmykIds = this.cmyk.map(ctrl => ctrl.itemID);
            if (this.setPicker.selectedIndex == 0) {
                dlg.setItemsVisibility(rgbIds, cmykIds);
            }
            else {
                dlg.setItemsVisibility(cmykIds, rgbIds);
            }
        }
    };

    const midGrp = col.addGroup();
    midGrp.addStaticText("For these groups, the groups are hidden but the columns remain visible, preserving the horizontal space.").setIsFullWidth();
    const midStack = midGrp.addColumnStack();    
    const grp3 = new ColourGroup(midStack, "Group 3");
    const grp4 = new ColourGroup(midStack, "Group 4");
    const grp5 = new ColourGroup(midStack, "Group 5");
    visTicks[2].onValueChangedHandler = () => grp3.group.isVisible = visTicks[2].value;
    visTicks[3].onValueChangedHandler = () => grp4.group.isVisible = visTicks[3].value;
    visTicks[4].onValueChangedHandler = () => grp5.group.isVisible = visTicks[4].value;

    const btmGrp = col.addGroup();
    btmGrp.addStaticText("For these groups, the columns are hidden, so the horizontal space collapses.").setIsFullWidth();
    const btmStack = btmGrp.addColumnStack();    
    const grp6 = new ColourGroup(btmStack, "Group 6");
    const grp7 = new ColourGroup(btmStack, "Group 7");
    const grp8 = new ColourGroup(btmStack, "Group 8");
    visTicks[5].onValueChangedHandler = () => grp6.column.isVisible = visTicks[5].value;
    visTicks[6].onValueChangedHandler = () => grp7.column.isVisible = visTicks[6].value;
    visTicks[7].onValueChangedHandler = () => grp8.column.isVisible = visTicks[7].value;


    dlg.initialWidth = 600;
    dlg.runModal();
}

module.exports.main = main;
