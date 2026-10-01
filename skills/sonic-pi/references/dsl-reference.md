# Sonic Pi DSL reference (5.0.0)

The names below were listed from a running 5.0.0 (`synth_names`, `fx_names`,
`scale_names`, `chord_names`). Sonic Pi code is Ruby: blocks, arrays, `.each`,
`.map`, string interpolation and `File` all work.

## Time

| Call | Meaning |
|------|---------|
| `use_bpm 80` | sets the beat length for this thread (`sleep 1` = one beat = 0.75 s) |
| `sleep 0.5` | wait half a beat; the **only** thing that advances time |
| `with_bpm 120 do ... end` | tempo for a block |
| `sample_duration :loop_amen` | length in beats at the current BPM |
| `current_bpm`, `current_sched_ahead_time` | read back (default sched-ahead 0.5 s) |

- **Bar maths:** with 4 beats per bar, `bars × 4 × 60 / bpm` seconds.
- Keep every loop's total sleep a whole number of bars.
- `play`/`sample` return immediately. Notes overlap unless you `sleep`.

## Loops and threads

```ruby
live_loop :drums do          # named, re-definable while running; must sleep or sync
  sample :bd_haus
  sleep 1
end

live_loop :bass do
  sync :drums                # wait for the drums loop's next iteration (its cue)
  play :e2, release: 0.5
end

in_thread do ... end          # one-off parallel block
4.times do |i| ... end        # plain Ruby iteration
stop                          # inside a loop: ends that loop
```

- `cue :name` / `sync :name` pass events between threads. Every `live_loop`
  cues its own name each iteration.
- `tick` / `look` give a per-loop counter: `ring(...).tick` steps through a ring.
- `density 2 do ... end` squeezes the block into half the time.

## Notes, chords, scales

```ruby
play 60                       # MIDI number, or :c4, :eb3, :fs5
play :e3, attack: 0.01, sustain: 0.5, release: 0.3, amp: 0.8, pan: -0.3, cutoff: 90
play chord(:d4, :minor7)      # list of notes, played together
play_pattern_timed scale(:c4, :major), [0.25, 0.25, 0.5]
play_chord [60, 64, 67]
note(:c4) # => 60
chord_degree(:ii, :c4, :major, 4)  # 4-note chord on the 2nd degree
```

- **Envelope:** `attack`, `decay`, `sustain`, `release` (in beats). The note
  length is their sum.
- **Common options:** `amp` (0–1+), `pan` (−1…1), `cutoff` (MIDI note 0–130,
  for a low-pass), `res`.

- **Scales (frequently used):** `major minor major_pentatonic minor_pentatonic
  dorian mixolydian lydian phrygian aeolian blues_major blues_minor harmonic_minor
  melodic_minor chromatic whole_tone hungarian_minor egyptian hirajoshi`.
  `scale(:c3, :minor_pentatonic, num_octaves: 2)`.
- **Chords:** `major minor major7 minor7 dom7 dim7 halfdim sus2 sus4 add9 m9 maj9
  9 11 13 augmented` (and the short forms `M m M7 m7 7`).

## Synths (`use_synth :name` or `synth :name, note: 60`)

```
bass_foundation bass_highend beep blade bnoise chipbass chiplead chipnoise cnoise
dark_ambience dpulse dsaw dtri dull_bell fm gabberkick gnoise growl hollow hoover
kalimba mod_beep mod_dsaw mod_fm mod_pulse mod_saw mod_sine mod_tri noise
organ_tonewheel piano pluck pnoise pretty_bell prophet pulse rhodey rodeo saw
sc808_bassdrum sc808_clap sc808_claves sc808_closed_hihat sc808_congahi
sc808_congalo sc808_congamid sc808_cowbell sc808_cymbal sc808_maracas
sc808_open_hihat sc808_rimshot sc808_snare sc808_tomhi sc808_tomlo sc808_tommid
sine sound_in sound_in_stereo square subpulse supersaw tb303 tech_saws tri
winwood_lead zawa
```

- **Keys and pads:** `rhodey piano organ_tonewheel hollow dark_ambience
  pretty_bell kalimba`.
- **Bass:** `bass_foundation tb303 subpulse fm chipbass`.
- **Leads:** `blade prophet supersaw tech_saws zawa winwood_lead`.
- `pluck` and `kalimba` are quiet: raise `amp:` (2–3) or choose another synth.

## Samples (`sample :name, rate:, amp:, start:, finish:, beat_stretch:`)

The 206 built-in samples, by group (from `etc/samples`):

- **Kicks:** `bd_808 bd_ada bd_boom bd_chip bd_fat bd_gas bd_haus bd_jazz bd_klub
  bd_mehackit bd_pure bd_sone bd_tek bd_zome bd_zum drum_bass_hard
  drum_bass_soft drum_heavy_kick elec_hollow_kick elec_soft_kick`
- **Snares and claps:** `sn_dolf sn_dub sn_generic sn_zome drum_snare_hard
  drum_snare_soft elec_snare elec_hi_snare elec_lo_snare elec_mid_snare
  elec_filt_snare perc_snap perc_snap2`
- **Hats and cymbals:** `drum_cymbal_closed drum_cymbal_open drum_cymbal_pedal
  drum_cymbal_soft drum_cymbal_hard drum_splash_soft drum_splash_hard hat_bdu
  hat_cab hat_cats hat_gem hat_gnu hat_gump hat_hier hat_len hat_mess hat_metal
  hat_noiz hat_psych hat_raw hat_sci hat_snap hat_star hat_tap hat_yosh hat_zan
  hat_zap hat_zild ride_tri ride_via elec_cymbal`
- **Toms and percussion:** `drum_tom_hi_soft drum_tom_mid_soft drum_tom_lo_soft`
  (and `_hard`), `drum_cowbell drum_roll perc_bell perc_bell2 perc_impact1
  perc_till elec_tick elec_wood elec_triangle tabla_*` (25 tabla hits).
- **Loops** (use `beat_stretch:` to fit bars): `loop_amen loop_amen_full
  loop_breakbeat loop_compus loop_garzul loop_industrial loop_mika loop_safari
  loop_tabla loop_perc1 loop_perc2 loop_electric loop_3d_printer loop_weirdo
  loop_drone_g_97 loop_mehackit1 loop_mehackit2 arovane_beat_a…e tbd_fxbed_loop`
- **Bass:** `bass_dnb_f bass_drop_c bass_hard_c bass_hit_c bass_thick_c
  bass_trance_c bass_voxy_c bass_voxy_hit_c bass_woodsy_c glitch_bass_g`
- **Ambient and texture:** `ambi_choir ambi_dark_woosh ambi_drone ambi_glass_hum
  ambi_glass_rub ambi_haunted_hum ambi_lunar_land ambi_piano ambi_sauna
  ambi_soft_buzz ambi_swoosh tbd_pad_1…4 tbd_highkey_c4 tbd_voctone`
- **Lo-fi:** `vinyl_hiss vinyl_backspin vinyl_rewind vinyl_scratch`
- **Guitar:** `guit_e_fifths guit_e_slide guit_em9 guit_harmonics`
- **Misc and electronic:** `elec_*` blips, `glitch_perc1…5 glitch_robot1/2
  mehackit_phone1…4 mehackit_robot1…7 misc_burp misc_cineboom misc_crow
  perc_door perc_swash perc_swoosh`

A file path also works: `sample "/path/to/file.wav"`.

## FX (`with_fx :name, opt: v do ... end`)

```
autotuner band_eq bitcrusher bpf compressor distortion echo eq flanger gverb hpf
ixi_techno krush level lpf mono nbpf nhpf nlpf normaliser nrbpf nrhpf nrlpf octaver
pan panslicer ping_pong pitch_shift rbpf record reverb rhpf ring_mod rlpf slicer
sound_out sound_out_stereo tanh tremolo vowel whammy wobble
```

- **Every FX takes:** `mix:` (0–1, wet/dry) and `amp:`.
- **Common options:**
  - `reverb room: damp:`
  - `echo phase: decay:`
  - `lpf`/`hpf cutoff:`
  - `bitcrusher bits: sample_rate:`
  - `distortion distort:`
  - `slicer phase:`
  - `compressor threshold:`
- Wrap FX **inside** a `live_loop` (see gotchas).

## Randomness and data structures

- **Random:**
  - `rrand(0.5, 1)`: float
  - `rrand_i(1, 6)`: integer
  - `choose([...])`
  - `one_in(3)`
  - `dice(6)`
  - `shuffle(...)`
- **Seeding:** randomness is seeded per thread, so runs repeat. `use_random_seed N`
  picks a different (still reproducible) sequence.
- **Rings** wrap around: `ring(1, 0, 0, 1)`, `(ring :e3, :g3).tick`,
  `spread(3, 8)` (Euclidean rhythm: `play 60 if spread(3, 8).tick`),
  `knit(:e3, 3, :g3, 1)`, `range(60, 72, 2)`, `line(0, 1, steps: 8)`.

## Mixer and output

- `set_volume! 0.8` sets the master volume (default 1). It affects recordings.
- Takes are clean at an `amp:` of about 1. Many stacked layers above that clip, so
  check `true_peak_dbtp` with `wav_check.py`.
