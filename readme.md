# Koopatlas ("Koopatlas-Updated" fork)

An editor for world maps for the custom Koopatlas Engine for New Super Mario Bros. Wii, created by Treeki.

The "Koopatlas-Updated" fork aims to keep Koopatlas compatible with the latest versions of its dependencies, and to fix bugs and make minor improvements. Pull requests that make large changes to how the editor works or add major features will be declined — please make your own fork for that.

## Original readme below

Where do I even begin with this...

This is the editor half of Koopatlas - a totally new 2D map engine we wrote
for Newer. Without going into too much detail, here's a quick roundup:

- Ridiculously buggy and unpolished editor
- 2D maps with an unlimited* amount of layers
- Tileset layers, supporting an unlimited* amount of tilesets
- Doodad layers, allowing you to place arbitrary textures on the map at any
  position and scale/rotate them
- Doodad animations
- Unlockable paths and level nodes
- More hardcoded things than you can shake a stick at (possibly rivalling
  Nintendo's 3D maps)
- Multiple maps with entrances/exits a la Reggie
- Maps are stored in a ".kpmap" format for easy editability - a JSON file in a
  specific format - and exported to an optimised ".kpbin" format for usage
  in-game

*\*Unlimited: Not really. This is the Wii, a game console which was
underpowered when it was released in 2006. There's not a lot of room in RAM
for lots of tilesets and doodads. A couple of the Newer maps use up almost all
the available space, so...*

If you want to make maps, feel free to try it. Then bash your head against a
wall when you accidentally close the editor and lose your unsaved work because
there's no warning against that. Or when it crashes on you, which might happen.