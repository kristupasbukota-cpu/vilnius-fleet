# Maps in this project

Decided 4 October 2026: **every map this project draws sits on a real street map.**
A route or a set of links on a blank background is hard to read; with streets,
water, forest and district names under it, a reader can tell where they are.

## The default

- **Basemap:** OpenStreetMap, as a vector map built into the page. Streets in four
  classes, water, rivers, forest and parks, railways, district names, and the names
  of main streets. It follows the page's light or dark theme.
- **Overlays follow the streets.** Routes are drawn along the timetable's shape, cut at
  each stop, never as straight lines between stops.
- **Zoomable.** Drag to move, pinch or double-click to zoom, Ctrl or ⌘ with the scroll
  wheel to zoom, + / − / fit buttons. Labels thin out as you zoom out so they never
  overlap; stop names appear when zoomed in.
- **Credit:** "© OpenStreetMap contributors" on the map. The data is under the ODbL.
- **One coordinate frame:** metres around 25.215 E, 54.685 N, so overlays from any page
  line up with any basemap.

## Why vector and not map tiles

The pages are published as private Claude artifacts, which may not load images from
other sites. Tiles from a tile server would show as an empty grey box. A vector
basemap travels inside the page, stays sharp at every zoom, and switches with the
theme. For the area of one or two lines it adds about 190 KB.

The fleet replay that `code/build_map.py` generates is a different case: it is opened
as an ordinary web page and keeps its Leaflet tile map.

## How

1. Pick the box the map needs, in degrees: west, south, east, north.
2. Write the Overpass request and fetch it:

   ```
   python3 code/basemap.py query 25.135 54.62 25.295 54.75 > q.txt
   curl -A 'vilnius-fleet-research/1.0' --data-urlencode data@q.txt \
        https://overpass-api.de/api/interpreter -o osm.json
   ```

   From the cloud sandbox, overpass-api.de refuses the connection; fetch it from the
   Mac or the box instead.
3. Build the basemap: `python3 code/basemap.py build osm.json 25.135 54.62 25.295 54.75 basemap.json`.
   `--no-minor` leaves out residential streets, saving about 40% of the size. The
   city map keeps them, because a reader zoomed in on one link needs the side streets.
4. Inline `basemap.json` and `code/vmap.js` in the page, define the theme tokens
   (list at the top of `vmap.js`), and draw the page's own data into `map.overlay`.

Basemaps built so far, reuse them when they cover the area:

- `analysis/basemap-2026-10-04-north-west.json`: Pilaitė to Perkūnkiemis and Žvėrynas,
  for the [lines 118 and 32](lines-118-32-2026-10-04.md) page. About 190 KB.
- `analysis/basemap-2026-10-04-city.json`: the whole network, 25.04 to 25.50 E,
  54.575 to 54.83 N, residential streets included so a zoomed-in link still has its
  side streets. About 800 KB.
