# Recipes

Every recipe was run and recorded on Sonic Pi 5.0.0. `S=scripts` as in SKILL.md.

## Lo-fi hip-hop beat, exact length

80 BPM, 4/4. Every loop sums to whole bars. The lo-fi character comes from:

- a low-pass on the drums
- bit-crushed, swung hats
- Rhodes 7th chords through reverb
- vinyl hiss

```ruby
use_bpm 80

live_loop :drums do
  with_fx :lpf, cutoff: 95 do
    sample :bd_fat, amp: 1.6
    sleep 1
    sample :sn_dolf, amp: 0.9
    sleep 0.75
    sample :bd_fat, amp: 1.1
    sleep 0.25
    sample :bd_fat, amp: 1.3
    sleep 1
    sample :sn_dolf, amp: 0.9
    sleep 1
  end
end

live_loop :hats do
  with_fx :bitcrusher, bits: 10, sample_rate: 16000, mix: 0.4 do
    8.times do |i|
      sample :drum_cymbal_closed, amp: (i.even? ? 0.5 : 0.3), rate: 1.1
      sleep(i.even? ? 0.55 : 0.45)   # swing: long-short pairs, still 4 beats per bar
    end
  end
end

live_loop :keys do
  with_fx :reverb, room: 0.7, mix: 0.4 do
    with_fx :lpf, cutoff: 85 do
      use_synth :rhodey
      [chord(:d4, :minor7), chord(:g3, :dom7), chord(:c4, :major7), chord(:a3, :minor7)].each do |c|
        play c, sustain: 3, release: 1, amp: 0.7
        sleep 4
      end
    end
  end
end

live_loop :vinyl do
  sample :vinyl_hiss, amp: 0.3
  sleep sample_duration(:vinyl_hiss)
end
```

```bash
python3 $S/sp.py record -o lofi.wav --bars 32 --bpm 80 -f lofi.rb     # 96 s
python3 $S/wav_check.py lofi.wav --expect-seconds 96
```

Result: about −27 LUFS, true peak about −10 dBTP. Raise `set_volume!` or the `amp:`
values for a louder master.

## Changing a running loop (live coding)

`v1.rb`:

```ruby
live_loop :drums do
  sample :bd_haus
  sleep 0.5
end
```

`v2.rb`: same loop name, new body.

```ruby
live_loop :drums do
  sample :bd_haus
  sample :hat_bdu, amp: 1.5
  sleep 0.25
  sample :hat_bdu, amp: 1.5
  sleep 0.25
end
```

```bash
python3 $S/sp.py record-start
python3 $S/sp.py run -f v1.rb --wait 0.5
sleep 8
python3 $S/sp.py run -f v2.rb --wait 0.5     # no `stop` in between
sleep 8
python3 $S/sp.py record-stop live.wav && python3 $S/sp.py stop
python3 $S/wav_check.py live.wav --start 0 --end 7 --highpass 6000    # before
python3 $S/wav_check.py live.wav --start 9 --end 16 --highpass 6000   # after: louder
```

The change lands on the loop's next iteration, keeping time; there is no gap. The
measured high band went from −44.6 to −28.8 LUFS.

- **Several loops:** re-send only the file that holds all of them.
- **Fade a layer out:** redefine its loop with a lower `amp:`.
- **Remove a layer:** redefine its loop with `stop` as its body.

## Data sonification

Map each value to a note of a scale, one note per data point. Pentatonic scales keep
any sequence consonant. Print the mapping, so the result can be checked.

```ruby
use_bpm 120
rows = File.readlines("/abs/path/temps.csv").drop(1).map { |l| l.strip.split(",") }
values = rows.map { |r| r[1].to_f }
lo, hi = values.min, values.max
notes = scale(:c3, :major_pentatonic, num_octaves: 3)
use_synth :pluck
values.each_with_index do |v, i|
  idx = ((v - lo) / (hi - lo) * (notes.length - 1)).round
  puts "#{rows[i][0]} #{v} -> #{note_info(notes[idx]).midi_string}"
  play notes[idx], release: 0.35, amp: 2.5
  sleep 1
end
```

12 rows at 120 BPM, one beat each, is 6 s:

```bash
python3 $S/sp.py record -o temps.wav --seconds 6 -f sonify.rb
python3 $S/wav_check.py temps.wav        # onsets == 12 (notes are separated by silence)
python3 $S/sp.py logs --last-run -n 20   # the value -> note mapping
```

- **Paths:** use absolute paths in `File.readlines`. The spider's working
  directory is not yours.
- **Variations:**
  - map a second column to `amp:` or `pan:`
  - map a category to the synth
  - map magnitude to duration, keeping the total sleep known so the take length
    is exact
- To keep notes countable, use `release:` shorter than the step. For legato, drop
  the onset check.

## Chord progression with bass and arpeggio

```ruby
use_bpm 90
prog = (ring chord(:a3, :minor7), chord(:f3, :major7), chord(:c4, :major7), chord(:g3, :dom7))

live_loop :pad do
  use_synth :hollow
  play prog.tick, attack: 0.5, sustain: 3, release: 0.5, amp: 0.6
  sleep 4
end

live_loop :bass, sync: :pad do
  use_synth :bass_foundation
  c = prog.tick
  play c[0] - 12, release: 1.5
  sleep 2
  play c[0] - 12, release: 1.5
  sleep 2
end

live_loop :arp, sync: :pad do
  use_synth :pluck
  c = prog.tick
  8.times { play c.choose + 12, release: 0.2, amp: 2; sleep 0.5 }
end
```

`sync: :pad` starts the loop in phase with `:pad`. Each loop has its own `tick`,
and each is 4 beats long, so all of them stay on the same chord.

## Fixed-length takes of code that runs forever

`live_loop` never ends by itself. `sp.py record --seconds/--bars` stops all jobs
after the take. For a finite piece (no live_loops), measure its length as total
beats × 60 / BPM, and pass `--tail` for the last note's release or reverb.
