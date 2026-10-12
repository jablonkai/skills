/// <reference types="@mapeditor/tiled-api" />
// Template: a custom Tiled map export format. Copy, rename the format, edit write().
// Try it without installing:  bash td-extension.sh try my-format.js map.tmx out.txt
// Install for the GUI + CLI:  bash td-extension.sh install my-format.js
//
// Tiled loads every .js / .mjs file in ~/Library/Preferences/Tiled/extensions at
// startup (the CLI too, but not a project's extensionsPath when run headless).

tiled.registerMapFormat("myformat", {        // short name: used by --export-map / --format
  name: "My format (*.myf)",                 // shown in File > Export As
  extension: "myf",                          // without the dot; one extension only

  write: function (map, fileName) {
    const lines = [];
    lines.push(`size ${map.width} ${map.height} ${map.tileWidth} ${map.tileHeight}`);

    // Walk layers recursively so tile layers inside groups are included.
    (function walk(layers, prefix) {
      for (const layer of layers) {
        if (layer.isGroupLayer) { walk(layer.layers, prefix + layer.name + "/"); continue; }
        if (layer.isTileLayer) {
          lines.push(`layer ${prefix}${layer.name}`);
          for (let y = 0; y < layer.height; y++) {
            const row = [];
            for (let x = 0; x < layer.width; x++) row.push(layer.cellAt(x, y).tileId); // -1 = empty
            lines.push(row.join(","));
          }
        } else if (layer.isObjectLayer) {
          // layer.objects is in draw order; sort when the output needs id order.
          const objects = layer.objects.slice().sort((a, b) => a.id - b.id);
          for (const o of objects) {
            const tx = Math.floor(o.x / map.tileWidth), ty = Math.floor(o.y / map.tileHeight);
            lines.push(`object ${o.className || "-"} ${o.name || "-"} ${tx} ${ty}`);
          }
        }
      }
    })(map.layers, "");

    const file = new TextFile(fileName, TextFile.WriteOnly);
    file.write(lines.join("\n") + "\n");
    file.commit();                            // without commit() nothing is written
    // Return a string to report an error; return nothing on success.
  },
});
