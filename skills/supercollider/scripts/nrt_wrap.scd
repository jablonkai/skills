// NRT render wrapper — filled in and run by `sc.py render`; not meant to be edited.
// @@NAME@@ placeholders are replaced with sclang string/number literals.
//
// The user file is evaluated with a fixed random seed. Its last expression must be a
// Score, a Pattern (rendered with asScore), or an Array of [time, [msg...]] events.
// Every SynthDef that an /s_new in the result names is looked up in SynthDescLib and
// prepended as /d_recv, so `SynthDef(...).add` in the file is all a render needs.
(
var userFile = @@USER_FILE@@, outFile = @@OUT_FILE@@;
var duration = @@DURATION@@, tail = @@TAIL@@, seed = @@SEED@@;
var sampleRate = @@SAMPLE_RATE@@, channels = @@CHANNELS@@, sampleFormat = @@SAMPLE_FORMAT@@;
var oscFile = @@OSC_FILE@@;
// `exit` does not stop the evaluation, so failures throw and the try at the end
// reports them and exits once
var fail = { |why| Error("SC_SKILL_FAIL " ++ why).throw };
var result, score, events, names = IdentitySet.new, defs = List.new, total, opts, shift;

try {
thisThread.randSeed = seed;
result = try {
	thisProcess.interpreter.executeFile(userFile)
} { |err|
	err.reportError;
	fail.("the file raised an error while evaluating (see ERROR above)");
};

case
{ result.isNil } {
	fail.("the file evaluated to nil — a syntax error above, or its last expression is not a Score, Pattern or event Array")
}
{ result.isKindOf(Score) } { score = result }
{ result.isKindOf(Pattern) } {
	if(duration.isNil) { fail.("a Pattern needs --duration (patterns can be infinite)") };
	score = result.asScore(duration);
}
{ result.isKindOf(SequenceableCollection) } { score = Score(result) }
{ fail.("the file's last expression is a " ++ result.class.name ++ ", expected a Score, Pattern or Array of [time, msg] events") };

events = score.score.reject { |ev| ev.size > 1 and: { ev[1] == [\c_set, 0, 0] or: { ev[1] == ['c_set', 0, 0] } } };
events.do { |ev|
	ev[1..].do { |msg|
		if(msg.isArray and: { [9, \s_new, '/s_new', "s_new", "/s_new"].includesEqual(msg[0]) }) {
			names.add(msg[1].asSymbol);
		};
	};
};
names.do { |name|
	var desc = SynthDescLib.global.at(name);
	if(desc.isNil or: { desc.def.isNil }) {
		fail.("SynthDef '" ++ name ++ "' is used but not defined — define it in the file with SynthDef(\\" ++ name ++ ", {...}).add");
	};
	defs.add(desc.def);
};

total = (duration ?? { events.collect(_.first).maxItem ? 0 }) + tail;
if(total <= 0) { fail.("nothing to render: the score is empty and no --duration was given") };

// Server-side noise UGens (WhiteNoise, LFNoise*, Rand, Dust…) draw from the world's
// random generators, which scsynth seeds from the clock. A one-shot synth at the very
// start reseeds generator 0 — the one every synth uses unless it calls RandID — so
// the same --seed gives the same audio.
// The reseed takes effect in the seed synth's first audio block, and a synth started at
// the same instant draws its random initial state when it is created, so everything
// else starts two control blocks (~2.7 ms at 48 kHz) later. The file length stays exact.
shift = 128 / sampleRate;
defs.add(SynthDef(\sc_skill_seed, { RandSeed.kr(Impulse.kr(0), seed); FreeSelf.kr(Impulse.kr(0)) }));
score = Score(defs.collect { |def| [0.0, ['/d_recv', def.asBytes]] }
	++ [[0.0, [\s_new, \sc_skill_seed, -1, 0, 0]]]
	++ events.collect { |ev| [ev[0] + shift] ++ ev[1..] }.sort { |a, b| a[0] <= b[0] });
("SC_SKILL_INFO synthdefs=" ++ names.asArray.sort.join(",") ++ " events=" ++ events.size ++ " seconds=" ++ total).postln;

opts = ServerOptions.new
	.numOutputBusChannels_(channels)
	.numInputBusChannels_(0)
	.memSize_(2 ** 18)     // 256 MB real-time memory: long delays and reverbs need it
	.maxNodes_(8192)
	.numWireBufs_(512)
	.sampleRate_(sampleRate);

score.recordNRT(
	oscFilePath: oscFile,
	outputFilePath: outFile,
	sampleRate: sampleRate,
	headerFormat: "WAV",
	sampleFormat: sampleFormat,
	options: opts,
	duration: total,
	action: { |code| ("SC_SKILL_DONE exit=" ++ code).postln; 0.exit }
);
} { |err|
	if(err.errorString.contains("SC_SKILL_FAIL")) {
		err.errorString.replace("ERROR: ", "").postln;
	} {
		err.reportError;
		"SC_SKILL_FAIL internal error in the render wrapper".postln;
	};
	1.exit;
};
)
