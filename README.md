[![bounty](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/yannyonn94/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/yannyonn94/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)

# Velmara — A Travel Poster for a Place That Does Not Exist

A [make.fun bounty](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
entry: a program that draws an original travel poster for an invented
place.

**Velmara** is a white cliff town above a luminous turquoise lagoon,
somewhere the maps forgot. At golden dusk the sun sinks behind violet
mountains, lantern boats drift home across the glowing water, and the
town's landmark — the Spiral Lighthouse, a white tower ringed with red
bands — sweeps its beam over the lagoon. Whitewashed houses with
terracotta roofs cascade down the headland, cypress trees stand between
them, and a pale path winds down to a stone quay lit by lanterns. The
promise of a stay in Velmara: slow evenings, warm light on the water,
and nowhere to be but the edge of the world.

The poster's only text is the place's name, **VELMARA**, set large in
cream across the dusk sky.

## How it works

`main.py` (Python 3.13, standard library only — no PIL, no network)
renders the poster procedurally and writes it to
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`):

- a hand-written PNG encoder (`zlib` + `struct`: IHDR/IDAT/IEND chunks)
- a small canvas library: gradients, polygons, discs, lines, alpha
  blending, all drawn pixel by pixel
- a bold 5×7 bitmap font defined in the code, used for the place name
- a fixed-seed deterministic generator, so every run produces
  byte-identical output

## Run it

```sh
python3 main.py
```

Output: a 1024×1024 PNG, well under the 1,048,576-byte cap.

## License

MIT — see [LICENSE](LICENSE).
